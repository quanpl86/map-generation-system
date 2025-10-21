# src/map_generator/topologies/terraced_field.py

import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class TerracedFieldTopology(BaseTopology):
    """
    Tạo ra một con đường đi theo kiểu "ruộng bậc thang" 3D.
    Đường đi sẽ theo dạng zic-zac và đi lên một bậc sau mỗi hàng.
    Đồng thời tạo ra các khối đá nền bên dưới để tạo thành một ngọn đồi.
    Đây là dạng map lý tưởng để dạy về vòng lặp lồng nhau trong không gian 3D.
    """
    
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        """
        Tạo ra một đường đi zic-zac đi lên.

        Args:
            params (dict): Cần chứa 'rows' và 'cols' để xác định kích thước.

        Returns:
            PathInfo: Một đối tượng chứa thông tin về đường đi và các khối đá nền
                      của ruộng bậc thang.
        """
        print("    LOG: Generating 'terraced_field' topology...")
        
        rows_param = params.get('rows', [3, 4])
        cols_param = params.get('cols', [4, 6])

        rows = random.randint(*rows_param) if isinstance(rows_param, list) else rows_param
        cols = random.randint(*cols_param) if isinstance(cols_param, list) else cols_param

        # Đảm bảo khu vực này nằm gọn trong map (cả chiều rộng, sâu và cao)
        max_width = grid_size[0] - 2
        max_depth = grid_size[2] - 2
        max_height = grid_size[1] - 2
        
        if cols >= max_width: cols = max_width
        if rows >= max_depth: rows = max_depth
        if rows >= max_height: rows = max_height # Số bậc thang chính là số hàng

        # Tính toán vị trí bắt đầu an toàn
        start_x = random.randint(1, grid_size[0] - cols - 2)
        start_z = random.randint(1, grid_size[2] - rows - 2)
        y = 0

        # Vị trí bắt đầu của người chơi sẽ là một bước trước khi vào "ruộng"
        start_pos: Coord = (start_x - 1, y, start_z)
        
        path_coords: list[Coord] = []
        obstacles: list[dict] = []
        
        current_x, current_y, current_z = start_x, y, start_z
        
        direction = 1 # 1: đi theo chiều dương X, -1: đi theo chiều âm X

        # Vòng lặp ngoài: lặp qua từng hàng (row)
        for r in range(rows):
            # Lưu tọa độ bắt đầu của hàng hiện tại để xây nền
            row_start_x = current_x

            # Vòng lặp trong: đi hết một hàng và tạo đường đi
            for _ in range(cols - 1):
                path_coords.append((current_x, current_y, current_z))
                current_x += direction
            path_coords.append((current_x, current_y, current_z))

            # Xây nền đá bên dưới hàng vừa tạo
            for y_fill in range(current_y): # Lấp đầy từ y=0 đến y=current_y-1
                for x_offset in range(cols):
                    fill_x = row_start_x + (x_offset * direction)
                    obstacles.append({'type': 'foundation_stone', 'pos': (fill_x, y_fill, current_z)})
            
            # Chuyển sang hàng tiếp theo (nếu chưa phải hàng cuối)
            if r < rows - 1:
                # Đi lên một bậc và tiến một bước để tạo bậc thang
                current_y += 1
                current_z += 1
                # Thêm khối đá nền ngay dưới bậc thang chuyển tiếp
                obstacles.append({'type': 'foundation_stone', 'pos': (current_x, current_y - 1, current_z)})
                path_coords.append((current_x, current_y, current_z))
                direction *= -1 # Đảo chiều

        target_pos = path_coords[-1]

        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=path_coords, obstacles=obstacles)