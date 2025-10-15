# src/map_generator/placements/algorithm_placer.py

from .base_placer import BasePlacer
from src.map_generator.models.path_info import PathInfo
import random

class AlgorithmPlacer(BasePlacer):
    """
    Đặt các đối tượng cho các bài toán thuật toán phức tạp.
    
    Placer này hoạt động với các Topology như ComplexMaze, nơi không có
    đường đi định trước. Nó chỉ đặt mục tiêu ở một vị trí khó,
    buộc người chơi phải tự thiết kế thuật toán để tìm ra nó.
    """

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        """
        Nhận một map mê cung và đặt một vật phẩm duy nhất ở một vị trí khó tìm.

        Args:
            path_info (PathInfo): Thông tin từ ComplexMazeTopology, chủ yếu
                                  chứa chướng ngại vật (tường).
            params (dict): Các tham số bổ sung.

        Returns:
            dict: Một dictionary chứa layout map hoàn chỉnh.
        """
        print("    LOG: Placing items with 'algorithm' logic...")
        
        # Trong một bài toán thuật toán, thường chỉ có một mục tiêu duy nhất
        # để người chơi tập trung vào việc tìm đường.
        
        # Chúng ta có thể đặt vật phẩm ở gần đích để làm mục tiêu cuối cùng.
        # Một cách khác là chọn một vị trí ngẫu nhiên không phải là tường.
        # Ở đây, chúng ta sẽ đặt nó ở gần đích.
        
        target_x, target_y, target_z = path_info.target_pos
        
        # Chọn một vị trí gần đích nhưng không trùng với đích
        # để người chơi phải nhặt nó trước khi kết thúc.
        item_pos = (target_x - 1, target_y, target_z - 1)
        
        # Kiểm tra để đảm bảo vị trí item không nằm ngoài map (dù hiếm)
        if item_pos[0] < 0 or item_pos[2] < 0:
            item_pos = path_info.target_pos # Nếu tính toán bị lỗi, đặt ngay tại đích

        return {
            "start_pos": path_info.start_pos,
            "target_pos": path_info.target_pos,
            "items": [{"type": "gem", "pos": item_pos}],
            "obstacles": path_info.obstacles
        }