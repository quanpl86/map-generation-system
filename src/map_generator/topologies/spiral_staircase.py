# src/map_generator/topologies/spiral_staircase.py

from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class SpiralStaircaseTopology(BaseTopology):
    """
    Tạo ra một con đường cầu thang xoắn ốc đi lên.
    Mỗi bước đi sẽ tăng độ cao lên 1.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'spiral_staircase' topology...")

        min_x, max_x = 1, grid_size[0] - 2
        min_z, max_z = 1, grid_size[2] - 2
        
        y = 0
        start_pos: Coord = (min_x, y, min_z)
        
        path_coords: list[Coord] = [start_pos]
        
        current_x, current_z = min_x, min_z

        # [SỬA LỖI] Logic cũ dùng range(min, max) trong khi max thay đổi liên tục,
        # khiến vòng lặp while kết thúc sớm và chỉ vẽ được đường thẳng/chữ L.
        # Logic mới sẽ tính toán độ dài mỗi cạnh trước khi vẽ.
        while min_x < max_x and min_z < max_z:
            # 1. Vẽ cạnh phải ->
            side_length = max_x - min_x
            for _ in range(side_length):
                current_x += 1; y += 1
                path_coords.append((current_x, y, current_z))
            min_z += 2

            # 2. Vẽ cạnh dưới v
            side_length = max_z - min_z
            for _ in range(side_length):
                current_z += 1; y += 1
                path_coords.append((current_x, y, current_z))
            max_x -= 2

            if not (min_x < max_x and min_z < max_z): break

            # 3. Vẽ cạnh trái <-
            side_length = max_x - min_x
            for _ in range(side_length):
                current_x -= 1; y += 1
                path_coords.append((current_x, y, current_z))
            max_z -= 2

            # 4. Vẽ cạnh trên ^
            side_length = max_z - min_z
            for _ in range(side_length):
                current_z -= 1; y += 1
                path_coords.append((current_x, y, current_z))
            min_x += 2

        target_pos = path_coords[-1] if path_coords else start_pos
        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=path_coords)