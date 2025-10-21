# src/map_generator/topologies/spiral_platform_staircase.py

from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord

class SpiralPlatformStaircaseTopology(BaseTopology):
    """
    Tạo ra một biến thể của cầu thang xoắn ốc.
    Bao gồm các đoạn đường thẳng (platform) và chỉ đi lên ở các góc cua.
    Điều này giúp cấu trúc không bị quá cao và phù hợp với grid size giới hạn.
    """
    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'spiral_platform_staircase' topology...")

        min_x, max_x = 1, grid_size[0] - 2
        min_z, max_z = 1, grid_size[2] - 2
        
        y = 0
        start_pos: Coord = (min_x, y, min_z)
        
        path_coords: list[Coord] = [start_pos]
        
        current_x, current_z = min_x, min_z

        while min_x < max_x and min_z < max_z:
            # 1. Vẽ platform phải -> (tăng X)
            side_length = max_x - min_x
            if side_length <= 0: break # Should not happen here if loop condition is met, but good for safety
            for _ in range(side_length - 1): # Các bước đi trên platform
                current_x += 1
                path_coords.append((current_x, y, current_z))
            # Bậc thang ở góc: đi tới và đi lên
            if y + 1 >= grid_size[1] - 1: break # Kiểm tra giới hạn chiều cao trước khi đi lên
            current_x += 1; y += 1
            path_coords.append((current_x, y, current_z))
            min_z += 2 # Thu hẹp biên Z từ phía "trên" (nhỏ hơn)

            # 2. Vẽ platform dưới v (tăng Z)
            side_length = max_z - min_z
            if side_length <= 0: break # Không còn không gian cho đoạn này
            for _ in range(side_length - 1): # Các bước đi trên platform
                current_z += 1
                path_coords.append((current_x, y, current_z))
            # Bậc thang ở góc: đi tới và đi lên
            if y + 1 >= grid_size[1] - 1: break # Kiểm tra giới hạn chiều cao trước khi đi lên
            current_z += 1; y += 1
            path_coords.append((current_x, y, current_z))
            max_x -= 2 # Thu hẹp biên X từ phía "phải" (lớn hơn)

            # 3. Vẽ platform trái <- (giảm X)
            side_length = max_x - min_x
            if side_length <= 0: break # Không còn không gian cho đoạn này
            for _ in range(side_length - 1): # Các bước đi trên platform
                current_x -= 1
                path_coords.append((current_x, y, current_z))
            # Bậc thang ở góc: đi tới và đi lên
            if y + 1 >= grid_size[1] - 1: break # Kiểm tra giới hạn chiều cao trước khi đi lên
            current_x -= 1; y += 1
            path_coords.append((current_x, y, current_z))
            max_z -= 2 # Thu hẹp biên Z từ phía "dưới" (lớn hơn)

            # 4. Vẽ platform trên ^ (giảm Z)
            side_length = max_z - min_z
            if side_length <= 0: break # Không còn không gian cho đoạn này
            for _ in range(side_length - 1): # Các bước đi trên platform
                current_z -= 1
                path_coords.append((current_x, y, current_z))
            # Bậc thang ở góc: đi tới và đi lên
            if y + 1 >= grid_size[1] - 1: break # Kiểm tra giới hạn chiều cao trước khi đi lên
            current_z -= 1; y += 1
            path_coords.append((current_x, y, current_z))
            min_x += 2 # Thu hẹp biên X từ phía "trái" (nhỏ hơn)


            # Không cần thêm bậc thang ở 2 góc cuối để tạo lối ra dễ dàng hơn

        target_pos = path_coords[-1] if path_coords else start_pos
        return PathInfo(start_pos=start_pos, target_pos=target_pos, path_coords=path_coords)