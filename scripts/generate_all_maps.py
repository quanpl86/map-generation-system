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
from bug_generator.service import create_bug # [THAY ĐỔI] Import hàm điều phối mới
import re
import xml.etree.ElementTree as ET

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
            
            if block_type == "CALL":
                # [SỬA] Xử lý khối gọi hàm
                block_element = ET.Element('block', {'type': 'procedures_callnoreturn'})
                ET.SubElement(block_element, 'mutation', {'name': block_data.get("name")})
            elif block_type == "maze_repeat":
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
                        ET.SubElement(inner_blocks[i], 'next').append(inner_blocks[i+1])
                    statement_el.append(inner_blocks[0])
            else:
                # [SỬA] Xử lý các khối đơn giản khác
                action = block_type.replace("maze_", "") if block_type.startswith("maze_") else block_type
                # Blockly không có khối maze_collect, chỉ có maze_collect
                if action == "collect":
                    block_element = ET.Element('block', {'type': 'maze_collect'})
                elif action == "toggleSwitch":
                    block_element = ET.Element('block', {'type': 'maze_toggle_switch'})
                else:
                    block_element = ET.Element('block', {'type': f'maze_{action}'})

                if action == "turn":
                    direction = block_data.get("direction", "turnLeft")
                    field_el = ET.SubElement(block_element, 'field', {'name': 'DIR'})
                    field_el.text = direction
            
            elements.append(block_element)
        return elements
    
    # --- [SỬA LỖI] Logic mới để xử lý cả hàm và chương trình chính ---
    # Sẽ trả về một dictionary chứa các khối định nghĩa và khối main riêng biệt.
    final_xml_components = {"procedures": [], "main": None}
    
    # 1. Xử lý các khối định nghĩa hàm (procedures)
    for proc_name, proc_body in program_dict.get("procedures", {}).items():
        # [SỬA] Thêm deletable="false" và bỏ x, y
        proc_def_block = ET.Element('block', {'type': 'procedures_defnoreturn', 'deletable': 'false'})
        
        field_el = ET.SubElement(proc_def_block, 'field', {'name': 'NAME'})
        field_el.text = proc_name
        
        statement_el = ET.SubElement(proc_def_block, 'statement', {'name': 'STACK'})
        inner_blocks = build_blocks_recursively(proc_body)
        if inner_blocks:
            for i in range(len(inner_blocks) - 1):
                ET.SubElement(inner_blocks[i], 'next').append(inner_blocks[i+1])
            statement_el.append(inner_blocks[0])
        
        final_xml_components["procedures"].append(ET.tostring(proc_def_block, encoding='unicode'))

    # 2. Xử lý chương trình chính (main)
    main_blocks = build_blocks_recursively(program_dict.get("main", []))
    if main_blocks:
        for i in range(len(main_blocks) - 1):
            ET.SubElement(main_blocks[i], 'next').append(main_blocks[i+1])
        final_xml_components["main"] = ET.tostring(main_blocks[0], encoding='unicode')

    # Nối tất cả các thành phần lại thành một chuỗi XML duy nhất
    # Các khối định nghĩa hàm sẽ ở cấp cao nhất, cùng cấp với maze_start
    proc_defs_xml = "".join(final_xml_components["procedures"])
    main_code_xml = final_xml_components["main"] or ""

    # Bọc code chính trong khối maze_start
    main_start_block = f'<block type="maze_start" deletable="false" movable="false"><statement name="DO">{main_code_xml}</statement></block>'
    
    return proc_defs_xml + main_start_block

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
                    solution_result = solve_map_and_get_solution(temp_level_for_solver) # type: ignore

                    # --- Logic mới để sinh startBlocks động cho các thử thách FixBug ---
                    final_inner_blocks = ''
                    bug_type = generation_config.get("params", {}).get("bug_type")
                    start_blocks_type = generation_config.get("params", {}).get("start_blocks_type", "empty")

                    # [CẢI TIẾN LỚN] Logic sinh startBlocks
                    program_dict = solution_result.get("program_solution_dict", {}) if solution_result else {}
                    if start_blocks_type == "buggy_solution" and solution_result:
                        bug_type = generation_config.get("params", {}).get("bug_type")
                        bug_config = generation_config.get("params", {}).get("bug_config", {})

                        # [REFACTORED] Phân loại bug type để quyết định nên tạo lỗi trên XML hay raw_actions
                        xml_based_bugs = {
                            'incorrect_loop_count', 'incorrect_parameter', 
                            'incorrect_logic_in_function', 'missing_block', 
                            'incorrect_function_call_order'
                        }
                        raw_action_based_bugs = {'sequence_error', 'optimization'}

                        if bug_type in xml_based_bugs:
                            # 1. Tạo XML từ lời giải có cấu trúc
                            correct_xml = _create_xml_from_structured_solution(program_dict)
                            # 2. Tạo lỗi trên XML đó
                            final_inner_blocks = create_bug(bug_type, correct_xml, bug_config)
                        elif bug_type in raw_action_based_bugs:
                            # 1. Lấy chuỗi hành động thô
                            raw_actions = solution_result.get("raw_actions", [])
                            # 2. Tạo lỗi trên chuỗi hành động đó
                            buggy_actions = create_bug(bug_type, raw_actions, bug_config)
                            # 3. Chuyển chuỗi lỗi thành XML
                            final_inner_blocks = f'<block type="maze_start" deletable="false" movable="false"><statement name="DO">{actions_to_xml(buggy_actions)}</statement></block>'
                        else:
                            print(f"   - ⚠️ Cảnh báo: bug_type '{bug_type}' không được hỗ trợ hoặc chưa được phân loại.")
                            final_inner_blocks = ''

                    elif start_blocks_type == "raw_solution" and solution_result:
                        # Cung cấp lời giải tuần tự (chưa tối ưu)
                        raw_actions = solution_result.get("raw_actions", [])
                        # [SỬA LỖI] Bọc các khối tuần tự trong một khối maze_start
                        inner_xml = actions_to_xml(raw_actions)
                        final_inner_blocks = f'<block type="maze_start" deletable="false" movable="false"><statement name="DO">{inner_xml}</statement></block>'
                    
                    elif start_blocks_type == "optimized_solution" and solution_result:
                        # Cung cấp lời giải đã tối ưu
                        final_inner_blocks = _create_xml_from_structured_solution(program_dict)
                    elif 'start_blocks' in blockly_config_req and blockly_config_req['start_blocks']:
                        raw_start_blocks = blockly_config_req['start_blocks']
                        # [CẢI TIẾN] Sử dụng XML parser để trích xuất nội dung một cách an toàn
                        try:
                            root = ET.fromstring(raw_start_blocks)
                            final_inner_blocks = "".join(ET.tostring(child, encoding='unicode') for child in root)
                        except ET.ParseError:
                            print(f"   - ⚠️ Cảnh báo: Lỗi cú pháp XML trong 'start_blocks' được định nghĩa sẵn. Sử dụng chuỗi thô.")
                            final_inner_blocks = raw_start_blocks.replace('<xml>', '').replace('</xml>', '')
                    
                    if final_inner_blocks:
                        final_start_blocks = f"<xml>{final_inner_blocks}</xml>"
                    else:
                        # Mặc định: tạo một khối maze_start rỗng
                        final_start_blocks = "<xml><block type=\"maze_start\" deletable=\"false\" movable=\"false\"><statement name=\"DO\"></statement></block></xml>"

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