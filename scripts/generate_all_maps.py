# scripts/generate_all_maps.py

import json
import os
import copy # Import module copy
import sys
import random

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
from scripts.gameSolver import solve_map_and_get_solution
import re
import xml.etree.ElementTree as ET

def create_buggy_start_blocks(raw_actions: list, bug_type: str) -> list:
    """
    Tạo ra một phiên bản lỗi của chuỗi hành động dựa trên loại lỗi được chỉ định.
    """
    buggy_actions = list(raw_actions)
    if not buggy_actions:
        return []

    print(f"    LOG: Creating bug of type '{bug_type}' from {len(raw_actions)} optimal actions.")

    if bug_type == 'misplaced_block' and len(buggy_actions) >= 2:
        # Lỗi 1: Sai vị trí khối lệnh (Hoán đổi 2 khối lệnh ngẫu nhiên)
        idx1, idx2 = random.sample(range(len(buggy_actions)), 2)
        buggy_actions[idx1], buggy_actions[idx2] = buggy_actions[idx2], buggy_actions[idx1]
        print(f"      -> Swapped actions at index {idx1} and {idx2}.")

    elif bug_type == 'missing_block':
        # Lỗi 2 & 3: Thiếu khối lệnh / Tham số sai (Xóa một khối lệnh ngẫu nhiên)
        # Việc xóa một 'moveForward' tương đương với lỗi 'tham số sai' (di chuyển không đủ)
        # Việc xóa 'jump' hoặc 'collect' là lỗi 'thiếu khối lệnh'
        if len(buggy_actions) > 1:
            # Ưu tiên xóa các hành động quan trọng
            important_actions = ['collect', 'jump', 'toggleSwitch', 'turnLeft', 'turnRight']
            for act in important_actions:
                if act in buggy_actions:
                    buggy_actions.remove(act)
                    print(f"      -> Removed important action '{act}'.")
                    return buggy_actions
            # Nếu không có, xóa một hành động ngẫu nhiên
            remove_idx = random.randint(0, len(buggy_actions) - 1)
            removed_action = buggy_actions.pop(remove_idx)
            print(f"      -> Removed random action '{removed_action}' at index {remove_idx}.")

    elif bug_type == 'incorrect_parameter':
        # Lỗi 2 (biến thể): Sai hướng rẽ
        turn_indices = [i for i, action in enumerate(buggy_actions) if action.startswith('turn')]
        if turn_indices:
            idx_to_change = random.choice(turn_indices)
            original_action = buggy_actions[idx_to_change]
            buggy_actions[idx_to_change] = 'turnRight' if original_action == 'turnLeft' else 'turnLeft'
            print(f"      -> Flipped turn direction at index {idx_to_change}.")
        else:
            # Nếu không có turn, quay về lỗi thiếu khối 'moveForward' để mô phỏng sai tham số
            if 'moveForward' in buggy_actions:
                buggy_actions.remove('moveForward')
                print("      -> No turn found, removed 'moveForward' to simulate incorrect parameter.")

    elif bug_type == 'optimization':
        # Lỗi 4: Tối ưu hóa (Thêm một khối lệnh thừa)
        if len(buggy_actions) > 0:
            insert_idx = random.randint(0, len(buggy_actions))
            # Thêm một cặp lệnh thừa tự hủy (vd: turnLeft rồi turnRight)
            buggy_actions.insert(insert_idx, 'turnRight')
            buggy_actions.insert(insert_idx, 'turnLeft')
            print(f"      -> Inserted redundant turn actions at index {insert_idx}.")

    return buggy_actions

def actions_to_xml(actions: list) -> str:
    """Chuyển đổi danh sách hành động thành chuỗi XML lồng nhau cho Blockly."""
    if not actions:
        return ""
    
    action = actions[0]
    # Đệ quy tạo chuỗi cho các khối còn lại
    next_block_xml = actions_to_xml(actions[1:])
    next_tag = f"<next>{next_block_xml}</next>" if next_block_xml else ""

    if action == 'turnLeft' or action == 'turnRight':
        direction = 'turnLeft' if action == 'turnLeft' else 'turnRight'
        return f'<block type="maze_turn"><field name="DIR">{direction}</field>{next_tag}</block>'
    
    # Các action khác như moveForward, jump, collect, toggleSwitch
    action_name = action.replace("maze_", "")
    return f'<block type="maze_{action_name}">{next_tag}</block>'

def _create_xml_from_structured_solution(program_dict: dict) -> str:
    """
    [REWRITTEN] Chuyển đổi dictionary lời giải thành chuỗi XML Blockly một cách an toàn.
    Sử dụng ElementTree để xây dựng cây XML thay vì xử lý chuỗi.
    """
    def build_blocks_recursively(block_list: list) -> list[ET.Element]:
        """Hàm đệ quy để xây dựng một danh sách các đối tượng ET.Element từ dict."""
        elements = []
        for block_data in block_list:
            block_type = block_data.get("type")
            
            if block_type == "maze_repeat":
                block_element = ET.Element('block', {'type': 'maze_repeat'})
                value_el = ET.SubElement(block_element, 'value', {'name': 'TIMES'})
                shadow_el = ET.SubElement(value_el, 'shadow', {'type': 'math_number'})
                field_el = ET.SubElement(shadow_el, 'field', {'name': 'NUM'})
                field_el.text = str(block_data.get("times", 1))
                
                statement_el = ET.SubElement(block_element, 'statement', {'name': 'DO'})
                inner_blocks = build_blocks_recursively(block_data.get("body", []))
                if inner_blocks:
                    # Nối các khối bên trong statement lại với nhau
                    for i in range(len(inner_blocks) - 1):
                        next_tag = ET.Element('next')
                        next_tag.append(inner_blocks[i+1])
                        inner_blocks[i].append(next_tag)
                    statement_el.append(inner_blocks[0])
            else:
                # Các khối đơn giản khác
                action = block_type.replace("maze_", "") if block_type.startswith("maze_") else block_type
                block_element = ET.Element('block', {'type': f'maze_{action}'})
                if action == "turn":
                    direction = block_data.get("direction", "turnLeft")
                    field_el = ET.SubElement(block_element, 'field', {'name': 'DIR'})
                    field_el.text = direction
            
            elements.append(block_element)
        return elements

    # Xử lý chương trình chính
    main_blocks = build_blocks_recursively(program_dict.get("main", []))
    
    # Nối các khối ở cấp cao nhất của chương trình chính
    if not main_blocks:
        return ""
    for i in range(len(main_blocks) - 1):
        next_tag = ET.Element('next')
        next_tag.append(main_blocks[i+1])
        main_blocks[i].append(next_tag)
        
    return ET.tostring(main_blocks[0], encoding='unicode')

def _introduce_parameter_bug(xml_string: str) -> str:
    """[MỚI] Cố tình tạo lỗi tham số trong một chuỗi XML của Blockly."""
    try:
        # Bọc chuỗi XML trong một thẻ gốc để phân tích cú pháp
        # Vì _create_xml_from_structured_solution chỉ trả về khối đầu tiên đã được nối
        root = ET.fromstring(xml_string)
        
        # Ưu tiên 1: Tìm và thay đổi khối 'maze_repeat'
        repeat_fields = root.findall(".//block[@type='maze_repeat']/value/shadow/field[@name='NUM']")
        if repeat_fields:
            target_field = random.choice(repeat_fields)
            original_num = int(target_field.text)
            # Tạo lỗi một cách thông minh
            bugged_num = original_num + 1 if original_num > 2 else original_num - 1
            if bugged_num <= 0: bugged_num = 1
            target_field.text = str(bugged_num)
            print(f"    -> Tạo lỗi tham số: Thay đổi số lần lặp từ {original_num} thành {bugged_num}.")
            return ET.tostring(root, encoding='unicode')

        # Ưu tiên 2: Tìm và thay đổi khối 'maze_turn'
        turn_fields = root.findall(".//block[@type='maze_turn']/field[@name='DIR']")
        if turn_fields:
            target_field = random.choice(turn_fields)
            original_dir = target_field.text
            bugged_dir = "turnRight" if original_dir == "turnLeft" else "turnLeft"
            target_field.text = bugged_dir
            print(f"    -> Tạo lỗi tham số: Thay đổi hướng rẽ từ {original_dir} thành {bugged_dir}.")
            return ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        print(f"   - ⚠️ Lỗi khi phân tích XML để tạo lỗi: {e}. Trả về chuỗi gốc.")
        return xml_string

    return xml_string # Trả về chuỗi gốc nếu không tìm thấy mục tiêu để tạo lỗi

def main():
    """
    Hàm chính để chạy toàn bộ quy trình sinh map.
    Nó đọc file curriculum, sau đó gọi MapGeneratorService để tạo các file map tương ứng.
    """
    print("=============================================")
    print("=== BẮT ĐẦU QUY TRÌNH SINH MAP TỰ ĐỘNG ===")
    print("=============================================")

    # Xác định các đường dẫn file dựa trên thư mục gốc của dự án
    curriculum_dir = os.path.join(PROJECT_ROOT, 'data', 'curriculum')
    toolbox_filepath = os.path.join(PROJECT_ROOT, 'data', 'toolbox_presets.json')
    base_maps_output_dir = os.path.join(PROJECT_ROOT, 'data', 'base_maps') # Thư mục mới để test map
    final_output_dir = os.path.join(PROJECT_ROOT, 'data', 'final_game_levels')

    # --- Bước 1: [CẢI TIẾN] Lấy danh sách các file curriculum topic ---
    try:
        # Lọc ra tất cả các file có đuôi .json trong thư mục curriculum
        topic_files = sorted([f for f in os.listdir(curriculum_dir) if f.endswith('.json')])
        if not topic_files:
            print(f"❌ Lỗi: Không tìm thấy file curriculum nào trong '{curriculum_dir}'. Dừng chương trình.")
            return
        print(f"✅ Tìm thấy {len(topic_files)} file curriculum trong thư mục: {curriculum_dir}")
    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy thư mục curriculum tại '{curriculum_dir}'. Dừng chương trình.")
        return

    # --- [MỚI] Đọc file cấu hình toolbox ---
    try:
        with open(toolbox_filepath, 'r', encoding='utf-8') as f:
            toolbox_presets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"   ⚠️ Cảnh báo: Không tìm thấy hoặc file toolbox_presets.json không hợp lệ. Sẽ sử dụng toolbox rỗng.")
        toolbox_presets = {}

    # --- [SỬA LỖI] Đảm bảo thư mục đầu ra tồn tại trước khi ghi file ---
    if not os.path.exists(final_output_dir):
        os.makedirs(final_output_dir)
        print(f"✅ Đã tạo thư mục đầu ra: {final_output_dir}")
    if not os.path.exists(base_maps_output_dir):
        os.makedirs(base_maps_output_dir)
        print(f"✅ Đã tạo thư mục đầu ra cho map test: {base_maps_output_dir}")

    # --- Bước 2: Khởi tạo service sinh map ---
    map_generator = MapGeneratorService()
    
    total_maps_generated = 0
    total_maps_failed = 0

    # --- Bước 3: Lặp qua từng topic và từng yêu cầu map ---
    for topic_filename in topic_files:
        topic_filepath = os.path.join(curriculum_dir, topic_filename)
        try:
            with open(topic_filepath, 'r', encoding='utf-8') as f:
                topic = json.load(f)
            topic_code = topic.get('topic_code', 'UNKNOWN_TOPIC')
            print(f"\n>> Đang xử lý Topic: {topic.get('topic_name', 'N/A')} ({topic_code}) từ file '{topic_filename}'")
        except json.JSONDecodeError:
            print(f"   ❌ Lỗi: File '{topic_filename}' không phải là file JSON hợp lệ. Bỏ qua topic này.")
            total_maps_failed += len(topic.get('suggested_maps', [])) # Giả định lỗi cho tất cả map trong file
            continue
        except Exception as e:
            print(f"   ❌ Lỗi không xác định khi đọc file '{topic_filename}': {e}. Bỏ qua topic này.")
            continue
        
        # SỬA LỖI: Sử dụng enumerate để lấy chỉ số của mỗi yêu cầu
        for request_index, map_request in enumerate(topic.get('suggested_maps', [])):
            # Lấy thông tin từ cấu trúc mới
            generation_config = map_request.get('generation_config', {})
            map_type = generation_config.get('map_type')
            logic_type = generation_config.get('logic_type')
            num_variants = generation_config.get('num_variants', 1)

            if not map_type or not logic_type:
                print(f"   ⚠️ Cảnh báo: Bỏ qua yêu cầu #{request_index + 1} trong topic {topic_code} vì thiếu 'map_type' hoặc 'logic_type'.")
                continue
            
            print(f"  -> Chuẩn bị sinh {num_variants} biến thể cho Yêu cầu '{map_request.get('id', 'N/A')}'")

            # Lặp để tạo ra số lượng biến thể mong muốn
            for variant_index in range(num_variants):
                try:
                    # --- Bước 4: Sinh map và tạo gameConfig ---
                    params_for_generation = generation_config.get('params', {})
                    
                    generated_map = map_generator.generate_map(
                        map_type=map_type,
                        logic_type=logic_type,
                        params=params_for_generation
                    )
                    
                    if not generated_map: continue

                    game_config = generated_map.to_game_engine_dict()

                    # --- [MỚI] Lưu file gameConfig vào base_maps để test ---
                    test_map_filename = f"{map_request.get('id', 'unknown')}-var{variant_index + 1}.json"
                    test_map_filepath = os.path.join(base_maps_output_dir, test_map_filename)
                    try:
                        with open(test_map_filepath, 'w', encoding='utf-8') as f:
                            json.dump(game_config, f, indent=2, ensure_ascii=False)
                        print(f"✅ Đã tạo thành công file map test: {test_map_filename}")
                    except Exception as e:
                        print(f"   - ⚠️ Lỗi khi lưu file map test: {e}")

                    # --- Bước 5: Lấy cấu hình Blockly ---
                    blockly_config_req = map_request.get('blockly_config', {})
                    toolbox_preset_name = blockly_config_req.get('toolbox_preset')
                    
                    # Lấy toolbox từ preset và tạo một bản sao để không làm thay đổi bản gốc
                    # (SỬA LỖI) Sử dụng deepcopy để tạo một bản sao hoàn toàn độc lập
                    base_toolbox = copy.deepcopy(toolbox_presets.get(toolbox_preset_name, {"kind": "categoryToolbox", "contents": []}))

                    # (CẢI TIẾN) Tự động thêm khối "Events" (when Run) vào đầu mỗi toolbox
                    events_category = {
                      "kind": "category",
                      "name": "Events",
                      "categorystyle": "procedure_category",
                      "contents": [ { "kind": "block", "type": "maze_start" } ]
                    }
                    
                    # Đảm bảo 'contents' là một danh sách và chèn khối Events vào đầu
                    if 'contents' not in base_toolbox: base_toolbox['contents'] = []
                    base_toolbox['contents'].insert(0, events_category)
                    toolbox_data = base_toolbox

                    # --- Bước 6: Gọi gameSolver để tìm lời giải ---
                    # Tạo một đối tượng level tạm thời để solver đọc
                    temp_level_for_solver = {
                        "gameConfig": game_config['gameConfig'],
                        "blocklyConfig": {"toolbox": toolbox_data},
                        "solution": map_request.get('solution_config', {})
                    }
                    solution_result = solve_map_and_get_solution(temp_level_for_solver)

                    # --- Logic mới để sinh startBlocks động cho các thử thách FixBug ---
                    final_inner_blocks = ''
                    bug_type = generation_config.get("params", {}).get("bug_type")

                    if bug_type and solution_result:
                        # Nếu là thử thách FixBug, tạo start_blocks bị lỗi
                        raw_actions = solution_result.get("raw_actions", [])
                        buggy_actions = create_buggy_start_blocks(raw_actions, bug_type)
                        final_inner_blocks = actions_to_xml(buggy_actions)
                    elif 'start_blocks' in blockly_config_req and blockly_config_req['start_blocks']:
                        # Giữ lại logic cũ cho các trường hợp start_blocks được định nghĩa sẵn
                        raw_start_blocks = blockly_config_req['start_blocks']
                        final_inner_blocks = raw_start_blocks.replace('<xml>', '').replace('</xml>', '')
                    
                    if final_inner_blocks:
                        final_start_blocks = f"<xml><block type=\"maze_start\"><statement name=\"DO\">{final_inner_blocks}</statement></block></xml>"
                    else:
                        # Mặc định cho các bài không phải FixBug: tạo một khối maze_start rỗng
                        final_start_blocks = "<xml><block type=\"maze_start\"><statement name=\"DO\"></block></statement></block></xml>"

                    # --- Bước 7: Tổng hợp file JSON cuối cùng ---
                    final_json = {
                        "id": f"{map_request.get('id', 'unknown')}-var{variant_index + 1}",
                        "gameType": "maze",
                        "level": map_request.get('level', 1),
                        "titleKey": map_request.get('titleKey'),
                        "descriptionKey": map_request.get('descriptionKey'),
                        "translations": map_request.get('translations'),
                        "supportedEditors": ["blockly", "monaco"],
                        "blocklyConfig": {
                            "toolbox": toolbox_data,
                            "maxBlocks": (solution_result['block_count'] + 5) if solution_result else 99,
                            "startBlocks": final_start_blocks
                        },
                        "gameConfig": game_config['gameConfig'],
                        "solution": {
                            "type": map_request.get('solution_config', {}).get('type', 'reach_target'),
                            "itemGoals": map_request.get('solution_config', {}).get('item_goals', {}),
                            "optimalBlocks": solution_result['block_count'] if solution_result else 0,
                            "rawActions": solution_result['raw_actions'] if solution_result else [],
                            "structuredSolution": solution_result['structuredSolution'] if solution_result else []
                        },
                        "sounds": { "win": "/assets/maze/win.mp3", "fail": "/assets/maze/fail_pegman.mp3" }
                    }

                    # --- Bước 8: Lưu file JSON cuối cùng ---
                    filename = f"{final_json['id']}.json"
                    output_filepath = os.path.join(final_output_dir, filename)
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        json.dump(final_json, f, indent=2, ensure_ascii=False)
                    print(f"✅ Đã tạo thành công file game hoàn chỉnh: {filename}")
                    total_maps_generated += 1
                    
                except Exception as e:
                    print(f"   ❌ Lỗi khi sinh biến thể {variant_index + 1} cho yêu cầu #{request_index + 1}: {e}")
                    total_maps_failed += 1
                    # Nếu một biến thể bị lỗi, bỏ qua các biến thể còn lại của map request này
                    break 

    # --- Bước 6: In báo cáo tổng kết ---
    print("\n=============================================")
    print("=== KẾT THÚC QUY TRÌNH SINH MAP ===")
    print(f"📊 Báo cáo: Đã tạo thành công {total_maps_generated} file game, thất bại {total_maps_failed} file.")
    print(f"📂 Các file game đã được lưu tại: {final_output_dir}")
    print(f"📂 Các file map test đã được lưu tại: {base_maps_output_dir}")
    print("=============================================")

if __name__ == "__main__":
    # Điểm khởi chạy của script
    main()