# src/map_generator/topologies/t_shape.py

from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class TShapeTopology(BaseTopology):
    """
    Tạo ra một con đường hình chữ T, có một ngã ba.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 't_shape' topology...")
        len_stem = params.get('len1', 4)
        len_cross = params.get('len2', 4)

        start_pos: Coord = (1, 0, 1)
        path_coords: list[Coord] = [start_pos]

        current_x, y, current_z = start_pos

        # 1. Vẽ phần thân của chữ T
        for _ in range(len_stem - 1):
            current_x += 1
            path_coords.append((current_x, y, current_z))

        intersection_pos = (current_x, y, current_z)

        # 2. Vẽ nhánh trái của phần ngang
        for i in range(len_cross // 2):
            path_coords.append((intersection_pos[0], y, intersection_pos[2] - (i + 1)))

        # 3. Vẽ nhánh phải của phần ngang
        for i in range(len_cross // 2):
            path_coords.append((intersection_pos[0], y, intersection_pos[2] + (i + 1)))

        # Đích là điểm cuối cùng được vẽ
        target_pos = path_coords[-1]

        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=path_coords)
