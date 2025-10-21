# src/map_generator/topologies/l_shape.py

from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class LShapeTopology(BaseTopology):
    """
    Tạo ra một con đường đơn giản hình chữ L.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'l_shape' topology...")
        len1 = params.get('len1', 5)
        len2 = params.get('len2', 5)

        start_pos: Coord = (1, 0, 1)
        path_coords: list[Coord] = []

        current_x, y, current_z = start_pos

        # Vẽ nhánh thứ nhất của chữ L
        for _ in range(len1 - 1):
            current_x += 1
            path_coords.append((current_x, y, current_z))

        # Vẽ nhánh thứ hai của chữ L
        for _ in range(len2 - 1):
            current_z += 1
            path_coords.append((current_x, y, current_z))

        target_pos = path_coords[-1] if path_coords else start_pos
        full_path = [start_pos] + path_coords

        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=full_path)
