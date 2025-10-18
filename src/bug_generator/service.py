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
    Tạo lỗi thiếu sót bằng cách xóa một hành động quan trọng.
    """
    if len(actions) <= 1:
        return actions

    important_actions = ['collect', 'jump', 'toggleSwitch']
    for act in important_actions:
        if act in actions:
            actions.remove(act)
            print(f"      -> Bug 'missing_block': Đã xóa hành động quan trọng '{act}'.")
            return actions
            
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
    Tạo lỗi tham số trong một chuỗi XML của Blockly.
    Ưu tiên thay đổi số lần lặp, sau đó là hướng rẽ.
    """
    if not xml_string: return ""
    try:
        # Bọc chuỗi XML trong một thẻ gốc tạm thời để phân tích cú pháp an toàn
        root = ET.fromstring(f"<root>{xml_string}</root>")
        
        # Ưu tiên 1: Tìm và thay đổi khối 'maze_repeat'
        repeat_fields = root.findall(".//block[@type='maze_repeat']//field[@name='NUM']")
        if repeat_fields:
            target_field = random.choice(repeat_fields)
            original_num = int(target_field.text)
            # Tạo lỗi một cách thông minh: +1 hoặc -1
            bugged_num = original_num + 1 if original_num > 2 else original_num - 1
            if bugged_num <= 0: bugged_num = 1
            target_field.text = str(bugged_num)
            print(f"      -> Bug 'incorrect_parameter': Thay đổi số lần lặp từ {original_num} thành {bugged_num}.")
            # Trả về nội dung bên trong thẻ <root>
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

def _introduce_misplaced_function_call_bug_xml(xml_string: str) -> str:
    """
    [MỚI] Tạo lỗi sai vị trí các khối GỌI HÀM trong một chuỗi XML.
    Hàm này tìm tất cả các khối gọi hàm và hoán đổi vị trí của hai khối ngẫu nhiên.
    """
    if not xml_string: return ""
    try:
        # Bọc trong thẻ root để phân tích cú pháp an toàn
        root = ET.fromstring(f"<root>{xml_string}</root>")
        
        # Tìm tất cả các khối gọi hàm (procedures_callnoreturn)
        # Lưu ý: Hàm này không xử lý các khối định nghĩa hàm (procedures_defnoreturn)
        call_blocks = root.findall(".//block[@type='procedures_callnoreturn']")
        
        if len(call_blocks) >= 2:
            # Hoán đổi hai khối gọi hàm ngẫu nhiên bằng cách tráo đổi các thuộc tính và con của chúng.
            # Đây là một cách tiếp cận đơn giản và hiệu quả.
            idx1, idx2 = random.sample(range(len(call_blocks)), 2)
            block1, block2 = call_blocks[idx1], call_blocks[idx2]
            
            # Tráo đổi nội dung (mutation tag) và các thuộc tính khác
            block1.tag, block2.tag = block2.tag, block1.tag
            block1.attrib, block2.attrib = block2.attrib, block1.attrib
            block1[:], block2[:] = block2[:], block1[:]
            
            print(f"      -> Bug 'misplaced_function_call': Hoán đổi khối gọi hàm ở vị trí {idx1} và {idx2}.")
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