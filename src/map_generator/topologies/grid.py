# src/map_generator/topologies/grid.py

import random
from .base_topology import BaseTopology
from ..models.path_info import PathInfo

class GridTopology(BaseTopology):
    """
    Tạo ra một cấu trúc map dạng lưới (grid) phẳng.
    Tất cả các ô trong một khu vực xác định đều có thể đi được.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        """
        Sinh ra một lưới các tọa độ có thể đi được.
        """
        width = params.get('grid_width', 10)
        depth = params.get('grid_depth', 10)
        
        # Tạo một mặt phẳng các khối đất
        path_coords = []
        for x in range(1, width + 1):
            for z in range(1, depth + 1):
                path_coords.append((x, 0, z))

        # Chọn vị trí bắt đầu và kết thúc ngẫu nhiên trên lưới
        # Đảm bảo chúng không quá gần nhau
        start_coord = (random.randint(1, width // 2), 0, random.randint(1, depth // 2))
        target_coord = (random.randint(width // 2 + 1, width), 0, random.randint(depth // 2 + 1, depth))

        # Vị trí của người chơi là y=1 (trên mặt đất y=0)
        start_pos = {'x': start_coord[0], 'y': start_coord[1] + 1, 'z': start_coord[2], 'direction': 1}
        target_pos = {'x': target_coord[0], 'y': target_coord[1] + 1, 'z': target_coord[2]}

        return PathInfo(
            path_coords=path_coords,
            start_pos=start_pos,
            target_pos=target_pos,
            map_type='grid'
        )
