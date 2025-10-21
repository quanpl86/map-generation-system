# src/map_generator/topologies/symmetrical_islands.py

import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class SymmetricalIslandsTopology(BaseTopology):
    """
    Tạo ra các khu vực (đảo) có cấu trúc giống hệt nhau, được ngăn cách
    bởi các khoảng trống hoặc hành lang.
    
    Đây là dạng map lý tưởng để dạy về việc nhận biết mẫu lặp lại
    và phân rã vấn đề thành các hàm có thể tái sử dụng.
    """

    def _create_island_pattern(self, top_left_corner: Coord) -> tuple[list[Coord], list[dict]]:
        """
        Tạo ra một mẫu hình hòn đảo lớn hơn (hình vuông rỗng 3x3)
        và một viền đá xung quanh nó.
        
        Args:
            top_left_corner (Coord): Tọa độ góc trên bên trái của hòn đảo.
            
        Returns:
            tuple[list[Coord], list[dict]]: Một tuple chứa (danh sách tọa độ đường đi, danh sách chướng ngại vật viền đá).
        """
        x, y, z = top_left_corner
        path = []
        obstacles = []
        
        # Tạo một mẫu hình vuông rỗng 3x3
        path.extend([(x, y, z), (x + 1, y, z), (x + 2, y, z)]) # Cạnh trên
        path.extend([(x + 2, y, z + 1), (x + 2, y, z + 2)])    # Cạnh phải
        path.extend([(x + 1, y, z + 2), (x, y, z + 2)])       # Cạnh dưới
        path.append((x, y, z + 1))                             # Cạnh trái

        # Tạo viền đá xung quanh đường đi
        path_set = set(path)
        border_coords = set()
        for px, py, pz in path:
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if dx == 0 and dz == 0: continue
                    neighbor = (px + dx, py, pz + dz)
                    if neighbor not in path_set:
                        border_coords.add(neighbor)
        
        for b_coord in border_coords:
            obstacles.append({'type': 'stone_border', 'pos': b_coord})
            
        return path, obstacles

    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        """
        Tạo ra một chuỗi các hòn đảo giống hệt nhau.

        Args:
            params (dict): Có thể chứa 'num_islands' để tùy chỉnh số lượng đảo.

        Returns:
            PathInfo: Một đối tượng chứa thông tin về tất cả các hòn đảo.
        """
        print("    LOG: Generating 'symmetrical_islands' topology...")
        
        # --- (CẢI TIẾN) Đọc và ngẫu nhiên hóa số lượng đảo ---
        num_islands_param = params.get('num_islands', 2)
        if isinstance(num_islands_param, list) and len(num_islands_param) == 2:
            # Nếu num_islands là một khoảng [min, max], chọn ngẫu nhiên một giá trị
            num_islands = random.randint(num_islands_param[0], num_islands_param[1])
        else:
            # Nếu không, sử dụng giá trị được cung cấp hoặc mặc định
            num_islands = num_islands_param

        # --- (CẢI TIẾN) Tự động tính toán khoảng cách tối ưu giữa các đảo ---
        # Chiều rộng của mỗi hòn đảo là 3 (từ x đến x+2)
        island_width = 3
        # Tổng chiều rộng mà tất cả các đảo chiếm dụng
        # Khoảng cách giữa các đảo
        gap_between_islands = 3
        total_islands_width = (num_islands * island_width) + ((num_islands - 1) * gap_between_islands)
        
        # Khoảng cách giữa các góc bắt đầu của hai đảo liên tiếp
        island_spacing = island_width + gap_between_islands

        # [SỬA] Tính toán vị trí bắt đầu để căn giữa toàn bộ cụm đảo
        start_x = (grid_size[0] - total_islands_width) // 2
        # Kích thước của đảo theo chiều sâu là 3, cộng thêm viền đá 2 bên là 5
        island_depth = 5
        start_z = (grid_size[2] - island_depth) // 2
        y = 0
        
        start_pos: Coord = (start_x, y, start_z)
        
        all_path_coords: list[Coord] = []
        all_obstacles: list[dict] = []
        
        # Vòng lặp để tạo ra các hòn đảo
        for i in range(num_islands):
            # Tọa độ góc của mỗi hòn đảo được tính toán dựa trên khoảng cách
            island_corner = (start_x + i * island_spacing, y, start_z)
            
            # Tạo đường đi và viền đá cho hòn đảo hiện tại
            island_path, island_obstacles = self._create_island_pattern(island_corner)
            all_path_coords.extend(island_path)
            all_obstacles.extend(island_obstacles)
            
            # Tạo "cây cầu" nối giữa các đảo (nếu không phải đảo cuối cùng)
            if i < num_islands - 1:
                # Cầu nối từ điểm (x+2, y, z) của đảo hiện tại
                bridge_start = (island_corner[0] + 2, y, start_z)
                # đến điểm (x, y, z) của đảo tiếp theo
                bridge_end = (start_x + (i + 1) * island_spacing, y, start_z) # Điểm đầu của đảo tiếp theo
                
                # (SỬA LỖI) Tạo cầu nối từ điểm sau bridge_start đến trước bridge_end
                for step in range(bridge_start[0] + 1, bridge_end[0]):
                    all_path_coords.append((step, y, start_z))

        target_pos = all_path_coords[-1]
        
        return PathInfo(
            start_pos=start_pos,
            target_pos=target_pos,
            path_coords=all_path_coords, # Chứa tất cả các điểm của các đảo và cầu
            obstacles=all_obstacles
        )