# src/bug_generator/service.py
import random
from typing import List, Callable, Dict, Any, Optional
import xml.etree.ElementTree as ET

# --- SECTION 1: Bug Generators for Raw Action Lists ---

def _introduce_sequence_error(actions: List[str], config: Dict) -> List[str]:
    """
    Tạo lỗi thứ tự bằng cách tráo đổi hai hành động.
    """
    if len(actions) < 2:
        return actions
    
    idx1, idx2 = random.sample(range(len(actions)), 2)
    actions[idx1], actions[idx2] = actions[idx2], actions[idx1]
    print(f"      -> Bug 'sequence_error': Hoán đổi hành động ở vị trí {idx1} và {idx2}.")
    return actions # type: ignore

def _introduce_missing_block_bug(data: Any, config: Dict) -> Any:
    """
    [REFACTORED] Tạo lỗi thiếu sót. Hỗ trợ cả list hành động và XML.
    """
    if isinstance(data, str):  # Xử lý đầu vào là XML
        try:
            root = ET.fromstring(f"<root>{data}</root>")
            # Ưu tiên xóa một khối trong hàm
            possible_parents = root.findall(".//statement/..") # Tìm tất cả các khối có statement
            target_parent = random.choice(possible_parents) if possible_parents else root
            target_statement = target_parent.find("./statement")
            
            if target_statement is not None and len(list(target_statement)) > 1:
                blocks_in_statement = list(target_statement)
                # Ưu tiên xóa các khối lệnh đơn giản, tránh xóa khối gọi hàm hoặc vòng lặp
                simple_blocks_indices = [
                    i for i, b in enumerate(blocks_in_statement) 
                    if b.get('type') not in ['procedures_callnoreturn', 'maze_repeat', 'variables_set']
                ]
                
                remove_idx = random.choice(simple_blocks_indices) if simple_blocks_indices else random.randint(0, len(blocks_in_statement) - 1)
                removed_block = blocks_in_statement.pop(remove_idx)
                
                # Xóa hết và nối lại
                for child in list(target_statement): target_statement.remove(child)
                if blocks_in_statement:
                    for i in range(len(blocks_in_statement) - 1):
                        ET.SubElement(blocks_in_statement[i], 'next').append(blocks_in_statement[i+1])
                    target_statement.append(blocks_in_statement[0])
                print(f"      -> Bug 'missing_block' (XML): Đã xóa khối '{removed_block.get('type')}'")
                return "".join(ET.tostring(child, encoding='unicode') for child in root)
        except Exception as e:
            print(f"   - ⚠️ Lỗi khi tạo lỗi missing_block (XML): {e}. Trả về chuỗi gốc.")
            return data  # Trả về chuỗi gốc nếu có lỗi
        return data # Trả về nếu không có gì để xóa
    
    elif isinstance(data, list): # Xử lý đầu vào là list hành động
        if len(data) <= 1: return data

        important_actions = ['collect', 'jump', 'toggleSwitch']
        for act in important_actions:
            if act in data:
                data.remove(act)
                print(f"      -> Bug 'missing_block' (raw): Đã xóa hành động quan trọng '{act}'")
                return data
                
        # Nếu không có hành động quan trọng, xóa một hành động ngẫu nhiên
        remove_idx = random.randint(0, len(data) - 1)
        removed_action = data.pop(remove_idx)
        print(f"      -> Bug 'missing_block' (raw): Đã xóa hành động ngẫu nhiên '{removed_action}'")
        return data
        
    return data # Trả về dữ liệu gốc nếu không phải str hoặc list

def _introduce_optimization_bug(actions: List[str], config: Dict) -> List[str]:
    """
    Tạo lỗi tối ưu hóa bằng cách thêm các khối lệnh thừa (tự triệt tiêu).
    Ví dụ: thêm một cặp turnLeft và turnRight.
    """
    if not actions:
        return actions
    insert_idx = random.randint(0, len(actions))
    actions.insert(insert_idx, 'turnRight')
    actions.insert(insert_idx, 'turnLeft')
    print(f"      -> Bug 'optimization': Chèn cặp lệnh rẽ thừa ở vị trí {insert_idx}.")
    return actions

# --- SECTION 2: Bug Generators for XML Strings ---

def _introduce_incorrect_loop_count_bug(xml_string: str, config: Dict) -> str:
    """
    Tạo lỗi sai số lần lặp trong khối 'maze_repeat'.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")

        # Ưu tiên 1: Tìm và thay đổi khối 'maze_repeat'
        repeat_fields = root.findall(".//block[@type='maze_repeat']//field[@name='NUM']")
        if repeat_fields:
            target_field = random.choice(repeat_fields)
            original_num = int(target_field.text or 1)
            bugged_num = original_num + 1 if original_num > 2 else original_num - 1
            if bugged_num <= 0: bugged_num = 1
            target_field.text = str(bugged_num)
            print(f"      -> Bug 'incorrect_loop_count': Thay đổi số lần lặp từ {original_num} thành {bugged_num}.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except ET.ParseError as e:
        print(f"   - ⚠️ Lỗi khi phân tích XML để tạo lỗi tham số: {e}. Trả về chuỗi gốc.")
        return xml_string

    print(f"   - ⚠️ Không tìm thấy khối 'maze_repeat' để tạo lỗi. Trả về chuỗi gốc.")
    return xml_string

def _introduce_incorrect_parameter_bug(xml_string: str, config: Dict) -> str:
    """
    Tạo lỗi sai tham số cho các khối lệnh đơn giản như 'maze_turn'.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        # Tìm khối 'maze_turn'
        turn_fields = root.findall(".//block[@type='maze_turn']/field[@name='DIR']")
        if turn_fields:
            target_field = random.choice(turn_fields)
            original_dir = target_field.text
            bugged_dir = "turnRight" if original_dir == "turnLeft" else "turnLeft"
            target_field.text = bugged_dir
            print(f"      -> Bug 'incorrect_parameter': Thay đổi hướng rẽ từ {original_dir} thành {bugged_dir}.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except ET.ParseError as e:
        print(f"   - ⚠️ Lỗi khi phân tích XML để tạo lỗi incorrect_parameter: {e}. Trả về chuỗi gốc.")
    print(f"   - ⚠️ Không tìm thấy khối 'maze_turn' để tạo lỗi incorrect_parameter.")
    return xml_string

def _introduce_incorrect_logic_in_function_bug(xml_string: str, config: Dict) -> str:
    """
    Tạo lỗi logic bằng cách thay đổi một khối lệnh bên trong một hàm cụ thể.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        function_name = config.get("function_name")
        if not function_name:
            print("   - ⚠️ Thiếu 'function_name' trong bug_config. Không thể tạo lỗi.")
            return xml_string

        # Tìm đúng hàm cần sửa
        target_function = root.find(f".//block[@type='procedures_defnoreturn'][field[@name='NAME']='{function_name}']")
        if not target_function:
            print(f"   - ⚠️ Không tìm thấy hàm '{function_name}' để tạo lỗi.")
            return xml_string

        # Tìm các khối lệnh đơn giản bên trong hàm đó
        statement = target_function.find("./statement[@name='STACK']")
        if not statement: return xml_string
        
        simple_action_blocks = statement.findall("./block")

        if simple_action_blocks:
            target_block = random.choice(simple_action_blocks)
            original_type = target_block.get('type')
            replacements = {'maze_moveForward', 'maze_jump', 'maze_turn', 'maze_collect'} - {original_type}
            new_type = random.choice(list(replacements))
            target_block.set('type', new_type)
            for child in list(target_block): target_block.remove(child) # Xóa các field/value cũ
            print(f"      -> Bug 'incorrect_logic_in_function': Thay đổi logic trong hàm '{function_name}' từ '{original_type}' thành '{new_type}'.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi incorrect_logic_in_function: {e}. Trả về chuỗi gốc.")
    return xml_string

def _introduce_incorrect_function_call_order_bug(xml_string: str, config: Dict) -> str:
    """
    [SỬA LỖI] Tạo lỗi sai vị trí các khối lệnh trong chương trình chính.
    Hàm này tìm tất cả các khối lệnh trong khối maze_start và hoán đổi vị trí của hai khối ngẫu nhiên,
    ưu tiên hoán đổi các khối gọi hàm nếu có.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        maze_start_block = root.find(".//block[@type='maze_start']")
        if maze_start_block is None: return xml_string

        statement_do = maze_start_block.find("./statement[@name='DO']")
        if statement_do is None or not list(statement_do): return xml_string

        # Tách chuỗi khối lồng nhau thành một danh sách các khối riêng lẻ
        top_level_blocks = []
        current_block = statement_do.find("./block")
        while current_block is not None:
            next_block = current_block.find("./next/block")
            # Xóa thẻ <next> để tách khối ra
            next_element = current_block.find("./next")
            if next_element is not None:
                current_block.remove(next_element)
            top_level_blocks.append(current_block)
            current_block = next_block
        
        if len(top_level_blocks) >= 2:
            idx1, idx2 = random.sample(range(len(top_level_blocks)), 2)
            top_level_blocks[idx1], top_level_blocks[idx2] = top_level_blocks[idx2], top_level_blocks[idx1]
            print(f"      -> Bug 'incorrect_function_call_order': Hoán đổi khối lệnh ở vị trí {idx1} và {idx2} trong chương trình chính.")

            # Xóa hết các khối con cũ và xây dựng lại chuỗi khối đã bị xáo trộn
            for child in list(statement_do): statement_do.remove(child)
            for i in range(len(top_level_blocks) - 1):
                ET.SubElement(top_level_blocks[i], 'next').append(top_level_blocks[i+1])
            statement_do.append(top_level_blocks[0])

        return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi misplaced_function_call: {e}. Trả về chuỗi gốc.")
    return xml_string

def _introduce_incorrect_initial_value_bug(xml_string: str, config: Dict) -> str:
    """
    [MỚI] Tạo lỗi sai giá trị khởi tạo của một biến.
    Tìm khối 'variables_set' và thay đổi giá trị trong khối 'math_number' bên trong nó.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        # [CẢI TIẾN] Tìm tất cả các khối có thể chứa giá trị số để thay đổi (gán hoặc thay đổi)
        # Ưu tiên các khối shadow, là nơi chứa giá trị khởi tạo.
        potential_fields = root.findall(".//field[@name='NUM']")
        
        if potential_fields:
            target_field = random.choice(potential_fields)
            original_num = int(target_field.text or 1)
            # Thay đổi giá trị đi một chút, đảm bảo giá trị mới khác giá trị cũ
            change = random.choice([-2, -1, 1, 2])
            bugged_num = max(0, original_num + change) # Đảm bảo không âm
            if bugged_num == original_num: bugged_num = original_num + 1 if original_num > 0 else 2
            
            target_field.text = str(bugged_num)
            print(f"      -> Bug 'incorrect_initial_value': Thay đổi giá trị khởi tạo của biến từ {original_num} thành {bugged_num}.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi incorrect_initial_value: {e}. Trả về chuỗi gốc.")
    return xml_string

def _introduce_incorrect_math_operator_bug(xml_string: str, config: Dict) -> str:
    """
    [MỚI] Tạo lỗi sai toán tử trong khối 'math_arithmetic'.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        op_map = {
            "ADD": ["SUBTRACT", "MULTIPLY", "DIVIDE"],
            "SUBTRACT": ["ADD", "MULTIPLY", "DIVIDE"],
            "MULTIPLY": ["ADD", "SUBTRACT"],
            "DIVIDE": ["ADD", "SUBTRACT", "MULTIPLY"]
        }
        # Tìm một khối toán học
        math_blocks = root.findall(".//block[@type='math_arithmetic']/field[@name='OP']")
        if math_blocks:
            target_field = random.choice(math_blocks)
            original_op = target_field.text
            if original_op in op_map:
                bugged_op = random.choice(op_map[original_op])
                target_field.text = bugged_op
                print(f"      -> Bug 'incorrect_math_operator': Thay đổi toán tử từ {original_op} thành {bugged_op}.")
                return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi incorrect_math_operator: {e}. Trả về chuỗi gốc.")
    return xml_string

# Hàm _introduce_missing_block_bug đã có thể xử lý việc xóa khối 'variables_set' hoặc 'math_change'
# nên ta có thể dùng nó cho 'missing_variable_update'

# --- SECTION 3: Registry and Dispatcher ---

# --- Bảng đăng ký các trình tạo lỗi (Bug Generator Registry) ---
# Ánh xạ bug_type tới hàm xử lý tương ứng
BUG_GENERATORS: Dict[str, Callable[[Any, Dict], Any]] = {
    # Nhóm 1: Lỗi tuần tự & cấu trúc cơ bản
    'sequence_error': _introduce_sequence_error,
    'missing_block': _introduce_missing_block_bug,
    # 'misplaced_control_structure' cần logic phức tạp hơn, tạm thời bỏ qua

    # Nhóm 2: Lỗi cấu hình khối điều khiển
    'incorrect_loop_count': _introduce_incorrect_loop_count_bug,
    'incorrect_parameter': _introduce_incorrect_parameter_bug,
    # 'incorrect_loop_condition' cần khối 'while', tạm thời bỏ qua

    # Nhóm 3: Lỗi liên quan đến hàm
    'incorrect_logic_in_function': _introduce_incorrect_logic_in_function_bug,
    'incorrect_function_call_order': _introduce_incorrect_function_call_order_bug,
    # 'missing_function_call' có thể được xử lý bằng cách xóa khối 'procedures_callnoreturn'

    # Nhóm 4: Lỗi tối ưu hóa (hoạt động trên raw_actions)
    'optimization': _introduce_optimization_bug,

    # [MỚI] Nhóm 5: Lỗi liên quan đến Biến và Toán học (Topic 4)
    'incorrect_initial_value': _introduce_incorrect_initial_value_bug,
    'incorrect_math_operator': _introduce_incorrect_math_operator_bug,
    'missing_variable_update': _introduce_missing_block_bug, # Dùng lại hàm xóa khối
    'incorrect_math_expression': _introduce_incorrect_math_operator_bug, # Tương tự sai toán tử
    'wrong_logic_in_algorithm': _introduce_sequence_error, # Tạm thời dùng lỗi sai thứ tự
    'optimization_logic': _introduce_optimization_bug, # Dùng lại lỗi tối ưu hóa
}

def create_bug(bug_type: str, data: Any, config: Dict = None) -> Any:
    """
    Hàm điều phối chính để tạo lỗi.
    Nó nhận vào loại lỗi và dữ liệu (có thể là list hành động hoặc chuỗi XML)
    và gọi hàm tạo lỗi tương ứng.

    Args:
        bug_type: Tên của loại lỗi cần tạo.
        data: Dữ liệu đầu vào (List[str] hoặc str).
        config: Cấu hình chi tiết cho việc tạo lỗi.

    Returns:
        Dữ liệu đã được làm lỗi.
    """
    config = config or {}
    generator_func = BUG_GENERATORS.get(bug_type)

    if generator_func:
        print(f"    LOG: Đang tạo lỗi loại '{bug_type}'.")
        data_copy = list(data) if isinstance(data, list) else str(data)
        return generator_func(data_copy, config)
    else:
        print(f"    - ⚠️ Cảnh báo: Không tìm thấy trình tạo lỗi cho loại '{bug_type}'. Trả về hành động gốc.")
        return data