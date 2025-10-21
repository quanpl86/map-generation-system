# src/map_generator/models/map_data.py

import random
import json
import os
from typing import List, Tuple, Dict, Any

# Định nghĩa các kiểu dữ liệu tùy chỉnh để code dễ đọc hơn
Coord = Tuple[int, int, int]
Item = Dict[str, Any]
Obstacle = Dict[str, Any]

class MapData:
    """
    Lớp chứa toàn bộ dữ liệu cấu thành một map game hoàn chỉnh.
    Nó hoạt động như một cấu trúc dữ liệu chuẩn cho đầu ra của hệ thống sinh map.
    """
    def __init__(self,
                 grid_size: Tuple[int, int, int],
                 start_pos: Coord,
                 target_pos: Coord,
                 items: List[Item] = None,
                 obstacles: List[Obstacle] = None,
                 path_coords: List[Coord] = None,
                 params: Dict[str, Any] = None, # [MỚI] Thêm params để đọc cấu hình trang trí
                 map_type: str = 'unknown',
                 logic_type: str = 'unknown'):
        """
        Khởi tạo một đối tượng dữ liệu map.

        Args:
            grid_size (Tuple[int, int, int]): Kích thước của lưới (rộng, cao, sâu).
            start_pos (Coord): Tọa độ bắt đầu của người chơi.
            target_pos (Coord): Tọa độ đích của màn chơi.
            items (List[Item], optional): Danh sách các vật phẩm. Mặc định là None.
            obstacles (List[Obstacle], optional): Danh sách các chướng ngại vật. Mặc định là None.
            path_coords (List[Coord], optional): Danh sách tọa độ của các ô trên đường đi.
            params (dict, optional): Các tham số từ curriculum, có thể chứa theme trang trí.
            map_type (str, optional): Tên của dạng map (topology) đã tạo ra nó.
            logic_type (str, optional): Tên của logic (placer) đã được áp dụng.
        """
        self.grid_size = grid_size
        self.start_pos = start_pos
        self.target_pos = target_pos
        
        # Xử lý an toàn cho các tham số mặc định là list để tránh lỗi
        self.items = items if items is not None else []
        self.path_coords = path_coords if path_coords is not None else []
        self.obstacles = obstacles if obstacles is not None else []
        self.params = params if params is not None else {} # [MỚI] Lưu lại params
        
        # Metadata để dễ dàng truy vết và gỡ lỗi
        self.map_type = map_type
        self.logic_type = logic_type

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi đối tượng MapData thành một dictionary có cấu trúc rõ ràng.
        Cấu trúc này được thiết kế để game engine có thể dễ dàng đọc và phân tích.

        Returns:
            Dict[str, Any]: Một dictionary đại diện cho toàn bộ map.
        """
        return {
            "metadata": {
                "grid_size": self.grid_size,
                "map_type_source": self.map_type,
                "logic_type_source": self.logic_type
            },
            "player": {
                "start_position": self.start_pos
            },
            "world_objects": {
                "target_position": self.target_pos,
                "path_coords": self.path_coords,
                "items": self.items,
                "obstacles": self.obstacles
            }
        }

    def save_to_json(self, filepath: str):
        """

        Lưu dữ liệu map vào một file JSON tại đường dẫn được chỉ định.
        Tự động tạo thư mục nếu nó chưa tồn tại.

        Args:
            filepath (str): Đường dẫn đầy đủ đến file JSON đầu ra.
        """
        # Đảm bảo thư mục cha của file tồn tại
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"❌ Lỗi: Không thể tạo thư mục tại '{directory}'. Lỗi: {e}")
                return

        # Ghi file JSON với định dạng đẹp và hỗ trợ UTF-8
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
            
            print(f"✅ Map đã được lưu thành công tại: {filepath}")
        except IOError as e:
            print(f"❌ Lỗi: Không thể ghi file tại '{filepath}'. Lỗi: {e}")

    def to_game_engine_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi dữ liệu map từ định dạng "bản thiết kế" sang định dạng "game engine"
        dựa trên cấu trúc của map-config-template.json.

        Returns:
            Dict[str, Any]: Một dictionary có cấu trúc để game engine đọc.
        """
        # --- Hàm tiện ích ---
        def coord_to_obj(coord: Coord, y_offset: int = 0) -> Dict[str, int]:
            """Chuyển tuple (x,y,z) thành object {"x":x, "y":y, "z":z} và áp dụng offset y."""
            return {"x": coord[0], "y": coord[1] + y_offset, "z": coord[2]}

        # --- Bước 1: Tạo mặt đất (ground) ---
        # path_coords là "nguồn chân lý" cho toàn bộ các ô có thể đi được.
        # Bao gồm cả start_pos và target_pos nếu topology đã cung cấp đúng.
        potential_ground_coords = set(self.path_coords)
        # Thêm start và target để đảm bảo chúng luôn có ground bên dưới.
        potential_ground_coords.add(self.start_pos)
        potential_ground_coords.add(self.target_pos)

        # --- (CẢI TIẾN) Xử lý trường hợp đặc biệt cho map maze ---
        if not self.path_coords and self.map_type == 'complex_maze_2d':
            print("    LOG: (Game Engine) Phát hiện map maze, dùng BFS để tìm các ô ground cần thiết...")
            
            # Tạo một set chứa tọa độ của tất cả các bức tường để tra cứu nhanh.
            wall_coords = {tuple(obs['pos']) for obs in self.obstacles if obs.get('type') == 'wall'}
            
            # Sử dụng thuật toán BFS để tìm tất cả các ô ground có thể đi được.
            # Hàng đợi (queue) cho BFS, bắt đầu từ vị trí của người chơi.
            queue = [self.start_pos]
            # Set để lưu các ô đã ghé thăm, tránh lặp vô hạn.
            visited_grounds = {self.start_pos}

            while queue:
                current_pos = queue.pop(0)
                
                # Khám phá 4 hướng xung quanh (trên mặt phẳng XZ)
                for dx, _, dz in [(1,0,0), (-1,0,0), (0,0,1), (0,0,-1)]:
                    next_pos = (current_pos[0] + dx, 0, current_pos[2] + dz)
                    
                    # Kiểm tra các điều kiện để một ô là hợp lệ:
                    # 1. Nằm trong biên của lưới.
                    # 2. Chưa được ghé thăm.
                    # 3. Không phải là một bức tường.
                    if (0 <= next_pos[0] < self.grid_size[0] and
                        0 <= next_pos[2] < self.grid_size[2] and
                        next_pos not in visited_grounds and
                        next_pos not in wall_coords):
                        visited_grounds.add(next_pos)
                        queue.append(next_pos)
            
            # Ground cuối cùng bao gồm các ô đi được và các ô nền móng của tường.
            final_ground_coords = visited_grounds.union(wall_coords)
        else:
            # Logic cũ cho các map có đường đi định trước
            final_ground_coords = potential_ground_coords

        # --- Hàm tiện ích để tạo cây ---
        def _create_tree(root_pos: Coord, occupied_coords: set) -> list:
            """Tạo một cây hoàn chỉnh với thân, cành và tán lá."""
            tree_blocks = []
            trunk_height = random.randint(3, 5)
            trunk_x, trunk_y, trunk_z = root_pos
            
            # [SỬA] Chọn model thân và lá cây dựa trên theme
            trunk_model = "ground.mud" if self.params.get('decoration_theme') == 'rocky_mountain' else "ground.mud"
            leaf_model = "ground.checker" if self.params.get('decoration_theme') == 'rocky_mountain' else "tree.leaves01"

            # 1. Tạo thân cây
            for i in range(trunk_height):
                trunk_pos = (trunk_x, trunk_y + i, trunk_z)
                if trunk_pos in occupied_coords: return [] # Thân cây va chạm
                tree_blocks.append({"modelKey": trunk_model, "position": coord_to_obj(trunk_pos)})

            # 2. Tạo tán lá
            canopy_center_y = trunk_y + trunk_height
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    for dz in range(-1, 2):
                        # Tạo hình dạng cầu cho tán lá, bỏ các góc
                        if abs(dx) + abs(dy) + abs(dz) > 2: continue
                        leaf_pos = (trunk_x + dx, canopy_center_y + dy, trunk_z + dz)
                        # Kiểm tra va chạm với đường đi và đảm bảo khoảng trống cho người chơi
                        if any(c[0] == leaf_pos[0] and c[2] == leaf_pos[2] and leaf_pos[1] < c[1] + 3 for c in final_ground_coords):
                            continue # Bỏ qua lá cây nếu nó quá gần đường đi
                        tree_blocks.append({"modelKey": leaf_model, "position": coord_to_obj(leaf_pos)})
            return tree_blocks

        # --- [REWRITTEN] Bước 1.5: Logic trang trí địa hình nâng cao với Grid Size Động ---
        game_blocks = []
        decoration_theme = self.params.get('decoration_theme')

        if decoration_theme:
            print(f"    LOG: (Game Engine) Applying '{decoration_theme}' decoration theme...")
            
            # --- Tính toán Grid Size Động ---
            # [SỬA LỖI] Đảm bảo bao gồm cả start_pos và target_pos khi tính toán biên
            all_game_coords = final_ground_coords.union({obs['pos'] for obs in self.obstacles}, {self.start_pos, self.target_pos})
            
            if not all_game_coords: # Xử lý trường hợp không có tọa độ nào
                min_x, max_x, min_z, max_z = 0, 1, 0, 1
            else:
                min_x = min(c[0] for c in all_game_coords)
                max_x = max(c[0] for c in all_game_coords)
                min_z = min(c[2] for c in all_game_coords)
                max_z = max(c[2] for c in all_game_coords)

            margin = 2 # [SỬA] Giảm khoảng đệm để base nhỏ lại
            grid_min_x = max(0, min_x - margin)
            grid_max_x = min(self.grid_size[0] - 1, max_x + margin)
            grid_min_z = max(0, min_z - margin)
            grid_max_z = min(self.grid_size[2] - 1, max_z + margin)
            
            print(f"    LOG: (Game Engine) Dynamic grid calculated: X({grid_min_x}-{grid_max_x}), Z({grid_min_z}-{grid_max_z})")

            # --- Bắt đầu xây dựng cảnh quan ---
            ROCK_MODELS = ["stone.stone01", "stone.stone02", "stone.stone03", "stone.stone04"]
            decoration_density = self.params.get('decoration_density', 0.15)

            # [REWRITTEN] Logic xây dựng địa hình từ dưới lên
            
            # 1. Đặt các khối nền móng (foundation_stone) trước tiên
            foundation_coords = set()
            for obs in self.obstacles:
                if obs.get('type') == 'foundation_stone':
                    pos = obs['pos']
                    game_blocks.append({"modelKey": "stone.stone01", "position": coord_to_obj(pos)})
                    foundation_coords.add(pos)

            # 2. [REWRITTEN] Tạo các cụm trang trí (cluster) thay vì các cột đơn lẻ
            available_deco_coords = set()
            for x in range(grid_min_x, grid_max_x + 1):
                for z in range(grid_min_z, grid_max_z + 1):
                    # Chỉ thêm vào nếu ô (x, 0, z) không bị chiếm bởi đường đi
                    is_occupied = any(c[0] == x and c[2] == z for c in final_ground_coords) or \
                                  any(f[0] == x and f[2] == z and f[1] == 0 for f in foundation_coords)
                    if not is_occupied:
                        available_deco_coords.add((x, z))

            # Đặt lớp nền cho tất cả các ô trang trí
            if self.map_type == 'spiral_path' and decoration_theme == 'forest':
                # [MỚI] Trường hợp đặc biệt cho map xoắn ốc, dùng nền đá để làm nổi bật
                base_model = "stone.stone01"
            else:
                base_model = "water.water01" if decoration_theme == "water_world" else \
                             "ground.mud" if decoration_theme == "rocky_mountain" else "ground.earth"
            
            for x, z in available_deco_coords:
                game_blocks.append({"modelKey": base_model, "position": coord_to_obj((x, 0, z))})

            # Tạo các cụm
            num_features = int(len(available_deco_coords) * decoration_density)
            
            # [REWRITTEN] Tạo cây và núi đá riêng biệt
            coords_for_trees = random.sample(list(available_deco_coords), k=min(num_features // 2, len(available_deco_coords)))
            coords_for_rocks = available_deco_coords - set(coords_for_trees)
            
            # 1. Tạo cây
            for x, z in coords_for_trees:
                # Đảm bảo cây không mọc quá gần đường đi
                too_close = any(abs(c[0] - x) < 2 and abs(c[2] - z) < 2 for c in final_ground_coords)
                if not too_close:
                    tree_blocks = _create_tree((x, 1, z), final_ground_coords)
                    game_blocks.extend(tree_blocks)

            # 2. Tạo các cụm đá
            num_rock_clusters = int(len(coords_for_rocks) * decoration_density / 3)
            for _ in range(num_rock_clusters):
                if not available_deco_coords: break
                if not coords_for_rocks: break
                seed_x, seed_z = random.choice(list(coords_for_rocks))
                coords_for_rocks.remove((seed_x, seed_z))
                for _ in range(random.randint(2, 5)): # Mỗi cụm có 2-5 khối
                    # Lớp đế (y=1)
                    game_blocks.append({"modelKey": random.choice(ROCK_MODELS), "position": coord_to_obj((seed_x, 0, seed_z), y_offset=1)})
                    # Lớp đỉnh (y=2) với xác suất thấp hơn để tạo hình dạng đồi
                    if random.random() < 0.5:
                        game_blocks.append({"modelKey": random.choice(ROCK_MODELS), "position": coord_to_obj((seed_x, 0, seed_z), y_offset=2)})
            
            # 4. Cuối cùng, đặt các khối đất cho đường đi chính (bảo toàn cấu trúc 3D)
            for coord in final_ground_coords:
                game_blocks.append({"modelKey": "ground.normal", "position": coord_to_obj(coord)})
        else:
            # Nếu không có theme, sử dụng logic cũ để đặt các khối đất cần thiết
            game_blocks = [{"modelKey": "ground.normal", "position": coord_to_obj(pos)} for pos in sorted(list(final_ground_coords))]


        # --- Bước 2: Đặt các đối tượng lên trên mặt đất ---
        collectibles = []
        interactibles = []

        # Đặt vật phẩm (crystal, switch) với tọa độ y+1
        for i, item in enumerate(self.items):
            item_type = item.get('type')
            item_pos_on_ground = coord_to_obj(item['pos'], y_offset=1)
            
            if item_type in ['crystal', 'gem']: # [SỬA] Chấp nhận cả 'gem' và 'crystal'
                collectibles.append({
                    "id": f"c{i+1}",
                    "type": "crystal", # Luôn xuất ra là 'crystal' để game engine hiểu
                    "position": item_pos_on_ground
                })
            elif item_type == 'switch':
                interactibles.append({
                    "id": f"s{i+1}",
                    "type": item_type,
                    "position": item_pos_on_ground,
                    "initialState": item.get("initial_state", "off")
                })

        # Đặt chướng ngại vật (wall) với tọa độ y+1
        # (SỬA LỖI) Coi 'pit' như một loại 'wall' khi chuyển đổi sang định dạng game.
        for obs in self.obstacles:
            obs_type = obs.get('type')
            if obs_type == 'wall' or obs_type == 'pit':
                game_blocks.append({
                    "modelKey": "wall.brick01",
                    "position": coord_to_obj(obs['pos'], y_offset=1)
                })

        # --- Bước 3: Hoàn thiện cấu trúc JSON ---
        return {
            "gameConfig": {
                "type": "maze",
                "renderer": "3d",
                "blocks": game_blocks,
                "players": [{
                    "id": "player1",
                    "start": {
                        **coord_to_obj(self.start_pos, y_offset=1),
                        "direction": 1 # Mặc định hướng về +X
                    }
                }],
                "collectibles": collectibles,
                "interactibles": interactibles,
                "finish": coord_to_obj(self.target_pos, y_offset=1)
            }
        }

    def save_to_game_engine_json(self, filepath: str):
        """Lưu dữ liệu map vào một file JSON theo định dạng của game engine."""
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_game_engine_dict(), f, indent=4, ensure_ascii=False)
            print(f"✅ Map (định dạng game) đã được lưu thành công tại: {filepath}")
        except IOError as e:
            print(f"❌ Lỗi: Không thể ghi file tại '{filepath}'. Lỗi: {e}")