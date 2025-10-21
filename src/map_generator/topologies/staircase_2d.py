# src/map_generator/topologies/staircase_2d.py

from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class Staircase2DTopology(BaseTopology):
    """
    Tạo ra một con đường zic-zac trên mặt phẳng 2D.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'staircase_2d' topology...")
        num_steps = params.get('num_steps', 4)

        start_pos: Coord = (1, 0, 1)
        path_coords: list[Coord] = [start_pos]

        current_x, y, current_z = start_pos

        for i in range(num_steps):
            if i % 2 == 0: # Đi theo trục X
                current_x += 1
            else: # Đi theo trục Z
                current_z += 1
            path_coords.append((current_x, y, current_z))

        target_pos = path_coords[-1]

        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=path_coords)
