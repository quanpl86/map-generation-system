# src/bug_generator/service.py
import random
from typing import List, Callable, Dict, Any
import xml.etree.ElementTree as ET

# --- SECTION 1: Bug Generators for Raw Action Lists ---

def _introduce_order_bug(actions: List[str]) -> List[str]:
    """
    Tạo lỗi thứ tự bằng cách tráo đổi hai hành động.
    """
    if len(actions) < 2:
        return actions
    
    idx1, idx2 = random.sample(range(len(actions)), 2)
    actions[idx1], actions[idx2] = actions[idx2], actions[idx1]
    print(f"      -> Bug 'misplaced_block': Hoán đổi hành động ở vị trí {idx1} và {idx2}.")
    return actions # type: ignore

def _introduce_missing_block_bug(actions: List[str]) -> List[str]:
    """
    [REFACTORED] Tạo lỗi thiếu sót. Hỗ trợ cả list hành động và XML.
    """
    if isinstance(actions, str): # Xử lý XML
        try:
            root = ET.fromstring(f"<root>{actions}</root>")
            # Ưu tiên xóa một khối trong hàm
            proc_body = root.find(".//block[@type='procedures_defnoreturn']/statement[@name='STACK']")
            target_statement = proc_body if proc_body is not None and len(list(proc_body)) > 1 else root.find(".//block[@type='maze_start']/statement[@name='DO']")
            
            if target_statement is not None and len(list(target_statement)) > 1:
                blocks_in_statement = list(target_statement)
                remove_idx = random.randint(0, len(blocks_in_statement) - 1)
                removed_block = blocks_in_statement.pop(remove_idx)
                
                # Xóa hết và nối lại
                for child in list(target_statement): target_statement.remove(child)
                if blocks_in_statement:
                    for i in range(len(blocks_in_statement) - 1):
                        ET.SubElement(blocks_in_statement[i], 'next').append(blocks_in_statement[i+1])
                    target_statement.append(blocks_in_statement[0])
                print(f"      -> Bug 'missing_block' (XML): Đã xóa khối '{removed_block.get('type')}'")
                return "".join(ET.tostring(child, encoding='unicode') for child in root)
        except Exception:
            return actions # Trả về chuỗi gốc nếu có lỗi
    
    # Logic cũ cho list hành động
    if len(actions) <= 1: return actions

    important_actions = ['collect', 'jump', 'toggleSwitch']
    for act in important_actions:
        if act in actions:
            actions.remove(act)
            print(f"      -> Bug 'missing_block': Đã xóa hành động quan trọng '{act}'.")
            return actions # type: ignore
            
    # Nếu không có hành động quan trọng, xóa một hành động ngẫu nhiên
    remove_idx = random.randint(0, len(actions) - 1)
    removed_action = actions.pop(remove_idx)
    print(f"      -> Bug 'missing_block': Đã xóa hành động ngẫu nhiên '{removed_action}' ở vị trí {remove_idx}.")
    return actions

def _introduce_redundant_block_bug(actions: List[str]) -> List[str]:
    """
    Tạo lỗi tối ưu hóa bằng cách thêm các khối lệnh thừa (tự triệt tiêu).
    """
    if not actions:
        return actions
        
    insert_idx = random.randint(0, len(actions))
    actions.insert(insert_idx, 'turnRight')
    actions.insert(insert_idx, 'turnLeft')
    print(f"      -> Bug 'optimization': Chèn cặp lệnh rẽ thừa ở vị trí {insert_idx}.")
    return actions

# --- SECTION 2: Bug Generators for XML Strings ---

def _introduce_parameter_bug_xml(xml_string: str) -> str:
    """
    [REFACTORED] Tạo lỗi tham số trong một chuỗi XML của Blockly.
    Hàm này sẽ chỉ thay đổi giá trị của tham số (số lần lặp, hướng rẽ),
    chứ không thay đổi loại khối lệnh.
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
            print(f"      -> Bug 'incorrect_parameter': Thay đổi số lần lặp từ {original_num} thành {bugged_num}.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)

        # Ưu tiên 2: Tìm và thay đổi khối 'maze_turn'
        turn_fields = root.findall(".//block[@type='maze_turn']/field[@name='DIR']")
        if turn_fields:
            target_field = random.choice(turn_fields)
            original_dir = target_field.text
            bugged_dir = "turnRight" if original_dir == "turnLeft" else "turnLeft"
            target_field.text = bugged_dir
            print(f"      -> Bug 'incorrect_parameter': Thay đổi hướng rẽ từ {original_dir} thành {bugged_dir}.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)

    except ET.ParseError as e:
        print(f"   - ⚠️ Lỗi khi phân tích XML để tạo lỗi tham số: {e}. Trả về chuỗi gốc.")
        return xml_string

    print(f"   - ⚠️ Không tìm thấy mục tiêu (vòng lặp/rẽ) để tạo lỗi tham số. Trả về chuỗi gốc.")
    return xml_string

def _introduce_wrong_block_in_loop_bug_xml(xml_string: str) -> str:
    """
    [MỚI] Tạo lỗi logic bằng cách thay đổi một khối lệnh bên trong vòng lặp hoặc hàm.
    """
    if not xml_string: return ""
    try:
        root = ET.fromstring(f"<root>{xml_string}</root>")
        possible_targets = root.findall(".//block[@type='procedures_defnoreturn']/statement/block") + root.findall(".//block[@type='maze_repeat']/statement/block")
        simple_action_blocks = [b for b in possible_targets if b.get('type') in ['maze_moveForward', 'maze_jump', 'maze_turn', 'maze_collect']]

        if simple_action_blocks:
            target_block = random.choice(simple_action_blocks)
            original_type = target_block.get('type')
            replacements = {'maze_moveForward', 'maze_jump', 'maze_turn', 'maze_collect'} - {original_type}
            new_type = random.choice(list(replacements))
            target_block.set('type', new_type)
            for child in list(target_block): target_block.remove(child) # Xóa các field/value cũ
            print(f"      -> Bug 'wrong_block_in_loop': Thay đổi logic từ '{original_type}' thành '{new_type}'.")
            return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi wrong_block_in_loop: {e}. Trả về chuỗi gốc.")
    return xml_string

def _introduce_misplaced_function_call_bug_xml(xml_string: str) -> str:
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
            print(f"      -> Bug 'misplaced_function_call': Hoán đổi khối lệnh ở vị trí {idx1} và {idx2} trong chương trình chính.")

            # Xóa hết các khối con cũ và xây dựng lại chuỗi khối đã bị xáo trộn
            for child in list(statement_do): statement_do.remove(child)
            for i in range(len(top_level_blocks) - 1):
                ET.SubElement(top_level_blocks[i], 'next').append(top_level_blocks[i+1])
            statement_do.append(top_level_blocks[0])

        return "".join(ET.tostring(child, encoding='unicode') for child in root)
    except Exception as e:
        print(f"   - ⚠️ Lỗi khi tạo lỗi misplaced_function_call: {e}. Trả về chuỗi gốc.")
    return xml_string

# --- SECTION 3: Registry and Dispatcher ---

# --- Bảng đăng ký các trình tạo lỗi (Bug Generator Registry) ---
# Ánh xạ bug_type tới hàm xử lý tương ứng
BUG_GENERATORS: Dict[str, Callable[[Any], Any]] = {
    # Các hàm này nhận vào list[str] và trả về list[str]
    'misplaced_block': _introduce_order_bug,
    'missing_block': _introduce_missing_block_bug,
    'optimization': _introduce_redundant_block_bug,

    # Hàm này nhận vào chuỗi XML và trả về chuỗi XML
    'incorrect_parameter': _introduce_parameter_bug_xml,
    'misplaced_function_call': _introduce_misplaced_function_call_bug_xml,
    'wrong_block_in_loop': _introduce_wrong_block_in_loop_bug_xml,
    
    # 'refactor_challenge' được xử lý đặc biệt trong generate_all_maps.py
    # và không cần một hàm tạo lỗi ở đây.
}

def create_bug(bug_type: str, data: Any) -> Any:
    """
    Hàm điều phối chính để tạo lỗi.
    Nó nhận vào loại lỗi và dữ liệu (có thể là list hành động hoặc chuỗi XML)
    và gọi hàm tạo lỗi tương ứng.

    Args:
        bug_type: Tên của loại lỗi cần tạo.
        data: Dữ liệu đầu vào (List[str] hoặc str).

    Returns:
        Dữ liệu đã được làm lỗi.
    """
    generator_func = BUG_GENERATORS.get(bug_type)

    if generator_func:
        print(f"    LOG: Đang tạo lỗi loại '{bug_type}'.")
        # Tạo bản sao để không thay đổi dữ liệu gốc
        data_copy = list(data) if isinstance(data, list) else str(data)
        return generator_func(data_copy)
    else:
        print(f"    - ⚠️ Cảnh báo: Không tìm thấy trình tạo lỗi cho loại '{bug_type}'. Trả về hành động gốc.")
        return data