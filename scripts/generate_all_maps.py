# scripts/generate_all_maps.py

import json
import os
import sys

# --- Thiết lập đường dẫn để import từ thư mục src ---
# Lấy đường dẫn đến thư mục gốc của dự án (đi lên 2 cấp từ file hiện tại)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Thêm thư mục src vào sys.path để Python có thể tìm thấy các module
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)
# ----------------------------------------------------

# Bây giờ chúng ta có thể import từ src một cách an toàn
from map_generator.service import MapGeneratorService

def main():
    """
    Hàm chính để chạy toàn bộ quy trình sinh map.
    Nó đọc file curriculum, sau đó gọi MapGeneratorService để tạo các file map tương ứng.
    """
    print("=============================================")
    print("=== BẮT ĐẦU QUY TRÌNH SINH MAP TỰ ĐỘNG ===")
    print("=============================================")

    # Xác định các đường dẫn file dựa trên thư mục gốc của dự án
    input_filepath = os.path.join(PROJECT_ROOT, 'data', 'curriculum_input.json')
    original_output_dir = os.path.join(PROJECT_ROOT, 'data', 'generated_maps')
    game_engine_output_dir = os.path.join(PROJECT_ROOT, 'data', 'base_maps')

    # --- Bước 1: Đọc và kiểm tra file curriculum input ---
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
        print(f"✅ Đã đọc thành công file curriculum từ: {input_filepath}")
    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file curriculum tại '{input_filepath}'. Dừng chương trình.")
        return
    except json.JSONDecodeError:
        print(f"❌ Lỗi: File curriculum '{input_filepath}' không phải là file JSON hợp lệ. Dừng chương trình.")
        return

    # --- Bước 2: Khởi tạo service sinh map ---
    map_generator = MapGeneratorService()
    
    total_maps_generated = 0
    total_maps_failed = 0

    # --- Bước 3: Lặp qua từng topic và từng yêu cầu map ---
    for topic in curriculum_data:
        topic_code = topic.get('topic_code', 'UNKNOWN_TOPIC')
        print(f"\n>> Đang xử lý Topic: {topic.get('topic_name', 'N/A')} ({topic_code})")
        
        # SỬA LỖI: Sử dụng enumerate để lấy chỉ số của mỗi yêu cầu
        for request_index, map_request in enumerate(topic.get('suggested_maps', [])):
            map_type = map_request.get('map_type')
            logic_type = map_request.get('logic_type')
            num_variants = map_request.get('num_variants', 1)

            if not map_type or not logic_type:
                print(f"   ⚠️ Cảnh báo: Bỏ qua yêu cầu #{request_index + 1} trong topic {topic_code} vì thiếu 'map_type' hoặc 'logic_type'.")
                continue
            
            print(f"  -> Chuẩn bị sinh {num_variants} biến thể cho Yêu cầu #{request_index + 1} (Loại: '{map_type}')")

            # Lặp để tạo ra số lượng biến thể mong muốn
            for variant_index in range(num_variants):
                try:
                    # Lấy đối tượng params từ request, nếu không có thì dùng dict rỗng
                    params_for_generation = map_request.get('params', {})
                    
                    # --- Bước 4: Gọi service để sinh một map duy nhất ---
                    generated_map = map_generator.generate_map(
                        map_type=map_type,
                        logic_type=logic_type,
                        params=params_for_generation
                    )
                    
                    if generated_map:
                        # --- Bước 5: Tạo tên file duy nhất và lưu map ---
                        # SỬA LỖI: Thêm chỉ số của request và variant vào tên file
                        filename = f"{topic_code}_{map_type}_req{request_index + 1}_var{variant_index + 1}.json"
                        
                        # 1. Lưu file "bản thiết kế" vào /generated_maps
                        original_filepath = os.path.join(original_output_dir, filename)
                        generated_map.save_to_json(original_filepath)

                        # 2. Lưu file "map game" vào /base_maps
                        game_engine_filepath = os.path.join(game_engine_output_dir, filename)
                        generated_map.save_to_game_engine_json(game_engine_filepath)

                        total_maps_generated += 1
                    
                except Exception as e:
                    print(f"   ❌ Lỗi khi sinh biến thể {variant_index + 1} cho yêu cầu #{request_index + 1}: {e}")
                    total_maps_failed += 1
                    # Nếu một biến thể bị lỗi, bỏ qua các biến thể còn lại của map request này
                    break 

    # --- Bước 6: In báo cáo tổng kết ---
    print("\n=============================================")
    print("=== KẾT THÚC QUY TRÌNH SINH MAP ===")
    print(f"📊 Báo cáo: Đã tạo thành công {total_maps_generated} map, thất bại {total_maps_failed} map.")
    print(f"📂 Các map (bản thiết kế) đã được lưu tại: {original_output_dir}")
    print(f"📂 Các map (định dạng game) đã được lưu tại: {game_engine_output_dir}")
    print("=============================================")

if __name__ == "__main__":
    # Điểm khởi chạy của script
    main()