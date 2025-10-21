        for obs in self.obstacles:
            potential_ground_coords.add(tuple(obs['pos']))
        
        # --- (CẢI TIẾN) Xử lý trường hợp đặc biệt cho map maze ---
        if self.map_type == 'complex_maze_2d':
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
            # [REWRITTEN] Logic xây dựng địa hình từ dưới lên để đảm bảo không bị chồng chéo.
            
            # --- Bước 1.5.1: Đặt các khối cấu trúc CỐ ĐỊNH vào trước (đường đi, nền móng, viền đá) ---
            # --- Tính toán Grid Size Động ---
            # [SỬA LỖI] final_ground_coords giờ đã chứa tất cả các tọa độ cần thiết.
            all_game_coords = final_ground_coords
                        game_blocks.append({"modelKey": random.choice(ROCK_MODELS), "position": coord_to_obj((seed_x, 1, seed_z))})
                        if random.random() < 0.5:
                            game_blocks.append({"modelKey": random.choice(ROCK_MODELS), "position": coord_to_obj((seed_x, 2, seed_z))})

            # --- Bước 1.5.5: Đặt các khối đường đi ---
            # [SỬA LỖI] Đối với maze, final_ground_coords chứa cả tường, ta cần loại chúng ra.
            # Đối với các map khác, final_ground_coords chỉ chứa đường đi.
            walkable_coords = final_ground_coords - wall_coords if self.map_type == 'complex_maze_2d' else final_ground_coords
            # Đảm bảo start/target luôn có ground, ngay cả khi chúng nằm ngoài path_coords
            walkable_coords.update({self.start_pos, self.target_pos})
            for coord in walkable_coords:
                game_blocks.append({"modelKey": "ground.normal", "position": coord_to_obj(coord)})
        else:
            # Nếu không có theme, sử dụng logic cũ để đặt các khối đất cần thiết

