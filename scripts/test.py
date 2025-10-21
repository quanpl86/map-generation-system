    logic_type = world.solution_config.get('logic_type', 'sequencing')

    # --- [REWRITTEN] Xử lý các trường hợp đặc biệt dựa trên logic_type ---
    if logic_type in ['variable_loop', 'variable_counter', 'math_basic', 'math_complex', 'math_expression_loop', 'advanced_algorithm', 'config_driven_execution', 'math_puzzle']:
        # Đối với các logic này, chúng ta muốn tạo ra một lời giải tường minh sử dụng biến
        # mà không cố gắng tạo ra các hàm (function) phức tạp.
        if not actions: return {"main": [], "procedures": {}}

        # Logic cho bài toán dùng biến để lặp
        if logic_type == 'variable_loop':
            # Tìm hành động lặp lại nhiều nhất, thường là 'moveForward'
            action_counts = Counter(a for a in actions if a in ['moveForward', 'collect'])
            if not action_counts: # Nếu không có hành động nào, trả về giải pháp tuần tự
                return {"main": compress_actions_to_structure(actions, available_blocks), "procedures": {}}
            
            most_common_action, num_repeats = action_counts.most_common(1)[0]
            
            # Tạo lời giải: set steps = N; repeat (steps) { action }
            main_program = [
                {"type": "variables_set", "variable": "steps", "value": num_repeats},
                {
                    "type": "maze_repeat_variable", # Loại khối đặc biệt để chỉ định dùng biến
                    "variable": "steps",
                    "body": [{"type": f"maze_{most_common_action}" if most_common_action in ['collect', 'toggleSwitch'] else most_common_action}]
                }
            ]
            # Thêm các hành động còn lại (nếu có)
            # Đây là một cách đơn giản hóa, có thể cần cải tiến
            remaining_actions_after_loop = [a for a in actions if a != most_common_action or (actions.count(a) > num_repeats)]
            main_program.extend(compress_actions_to_structure(remaining_actions_after_loop, available_blocks))
            return {"main": main_program, "procedures": {}}

        # Logic cho bài toán dùng biểu thức toán học
        if logic_type in ['math_expression_loop', 'math_complex', 'math_basic']:
            # Giả lập tạo 2 biến và dùng chúng trong vòng lặp
            total_moves = actions.count('moveForward')
            if total_moves < 2: # Cần ít nhất 2 bước để chia thành a+b
                return {"main": compress_actions_to_structure(actions, available_blocks), "procedures": {}}

            val_a = random.randint(1, total_moves - 1)
            val_b = total_moves - val_a
            
            main_program = [
                {"type": "variables_set", "variable": "a", "value": val_a},
                {"type": "variables_set", "variable": "b", "value": val_b},
                {
                    "type": "maze_repeat_expression", # Loại khối đặc biệt
                    "expression": {
                        "type": "math_arithmetic",
                        "op": "ADD",
                        "var_a": "a",
                        "var_b": "b"
                    },
                    "body": [{"type": "moveForward"}]
                }
            ]
            # Thêm các hành động không phải moveForward
            other_actions = [a for a in actions if a != 'moveForward']
            main_program.extend(compress_actions_to_structure(other_actions, available_blocks))
            return {"main": main_program, "procedures": {}}

        # Logic cho các bài toán thuật toán phức tạp (Fibonacci, config-driven)
        if logic_type in ['advanced_algorithm', 'config_driven_execution']:
            # Tạm thời, tạo một cấu trúc có nhiều biến để bug_generator có thể hoạt động
            main_program = [
                {"type": "variables_set", "variable": "param1", "value": 1},
                {"type": "variables_set", "variable": "param2", "value": 1},
                {"type": "variables_set", "variable": "temp", "value": 0},
            ]
            # Nối với lời giải tuần tự
            main_program.extend(compress_actions_to_structure(actions, available_blocks))
            return {"main": main_program, "procedures": {}}

        # Nếu không có logic đặc biệt nào khớp, trả về lời giải tuần tự đã được nén vòng lặp cơ bản
        return {"main": compress_actions_to_structure(remaining_actions, available_blocks), "procedures": procedures}

