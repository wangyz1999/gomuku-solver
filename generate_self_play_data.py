import os
import csv
import multiprocessing as mp
from solver import GomokuSolver


def generate_data_worker(engine_path, worker_id, num_games, max_steps, output_file, max_memory_mb=50, timeout_match_ms=180000, timeout_turn_ms=5000, visualize=False, samples_per_position=8):
    solver = GomokuSolver(
        engine_path,
        max_memory_mb=max_memory_mb,
        timeout_match_ms=timeout_match_ms,
        timeout_turn_ms=timeout_turn_ms
    )
    current_step = 0
    
    # Open file in append mode
    with open(output_file, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        for i in range(num_games):
            print(f"Worker {worker_id}: Starting game {i+1}/{num_games}")
            current_board_state = []
            while True:
                # Collect multiple samples for the same position
                move_counts = {}
                score_eval_sum = 0
                score_eval_count = 0
                mate_eval_sum = 0
                mate_eval_count = 0
                
                for _ in range(samples_per_position):
                    parsed_response, raw_output_str = solver.get_best_move(current_board_state)
                    best_move = parsed_response["best_move"]
                    evaluation = parsed_response["evaluation"]
                    
                    # Count occurrences of each move
                    move_key = str(best_move)
                    if move_key in move_counts:
                        move_counts[move_key]["count"] += 1
                        move_counts[move_key]["evaluations"].append(evaluation)
                    else:
                        move_counts[move_key] = {
                            "count": 1, 
                            "move": best_move,
                            "evaluations": [evaluation]
                        }
                    
                    # Handle different evaluation types
                    if evaluation:
                        if isinstance(evaluation, str) and ('+M' in evaluation or '-M' in evaluation):
                            # Handle mate evaluation
                            mate_num = int(evaluation.split('M')[1])
                            sign = 1 if '+M' in evaluation else -1
                            mate_eval_sum += sign * mate_num
                            mate_eval_count += 1
                        else:
                            # Handle score evaluation
                            try:
                                score_eval_sum += float(evaluation)
                                score_eval_count += 1
                            except (ValueError, TypeError):
                                pass  # Skip if evaluation can't be converted to float
                
                # Calculate average evaluations
                avg_score_eval = None
                if score_eval_count > 0:
                    avg_score_eval = score_eval_sum / score_eval_count
                
                avg_mate_eval = None
                if mate_eval_count > 0:
                    avg_mate_eval = mate_eval_sum / mate_eval_count
                    # Reconstruct the mate string (e.g., "+M53")
                    sign = '+' if avg_mate_eval > 0 else '-'
                    avg_mate_eval = f"{sign}M{abs(int(round(avg_mate_eval)))}"
                
                # Determine which moves have mate evaluations
                moves_with_mate = {}
                for move_key, move_data in move_counts.items():
                    for eval_str in move_data["evaluations"]:
                        if isinstance(eval_str, str) and ('+M' in eval_str or '-M' in eval_str):
                            if move_key not in moves_with_mate:
                                moves_with_mate[move_key] = []
                            moves_with_mate[move_key].append(eval_str)
                
                # Choose the majority move, prioritizing mate evaluations
                if moves_with_mate:
                    # If there are mate evaluations, choose the most frequent move with mate
                    mate_move_counts = {k: len(v) for k, v in moves_with_mate.items()}
                    majority_move_key = max(mate_move_counts, key=mate_move_counts.get)
                    majority_move = move_counts[majority_move_key]
                else:
                    # Otherwise, choose the most frequent move overall
                    majority_move = max(move_counts.values(), key=lambda x: x["count"])
                
                # Save data and flush immediately
                if current_board_state:
                    writer.writerow([
                        str(current_board_state),
                        str(majority_move["move"]),
                        str(avg_score_eval),
                        str(avg_mate_eval),
                        str(move_counts)  # Store all candidate moves with their counts
                    ])
                    f.flush()
                
                # update board state with the majority move
                new_board_state = current_board_state.copy()
                new_board_state.append((majority_move["move"][0], majority_move["move"][1], 1))
                current_board_state = new_board_state
                
                # Switch sides for next move
                current_board_state = solver.switch_board_side(current_board_state)
                
                if visualize:
                    solver.visualize_board(current_board_state)
                
                winner = solver.check_winner(current_board_state)
                current_step += 1
                
                if winner or current_step >= max_steps:
                    break

def generate_self_play_data(engine_path, num_games=10, max_steps=100, visualize=False, num_processes=1, output_file="gomoku_data.tsv", max_memory_mb=50, timeout_match_ms=180000, timeout_turn_ms=5000, samples_per_position=8, **kwargs):
    # Create output file with headers if it doesn't exist
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["board_state", "best_move", "score_evaluation", "mate_evaluation", "candidate_moves"])
    
    if num_processes > 1:
        # Split games among processes
        games_per_process = num_games // num_processes
        remaining_games = num_games % num_processes
        
        processes = []
        for i in range(num_processes):
            # Distribute remaining games
            process_games = games_per_process + (1 if i < remaining_games else 0)
            if process_games > 0:
                p = mp.Process(
                    target=generate_data_worker,
                    args=(engine_path, i, process_games, max_steps, output_file, max_memory_mb, timeout_match_ms, timeout_turn_ms, visualize, samples_per_position)
                )
                processes.append(p)
                p.start()
        
        # Wait for all processes to complete
        for p in processes:
            p.join()
    else:
        # Single process mode
        generate_data_worker(engine_path, 0, num_games, max_steps, output_file, max_memory_mb, timeout_match_ms, timeout_turn_ms, visualize, samples_per_position)


if __name__ == "__main__":
    engine_path = os.path.join("engines", "EMBRYO21.E", "pbrain-embryo21_e.exe")
    
    # Create settings dictionary
    settings = {
        "board_size": 15,
        "max_memory_mb_per_process": 80,
        "timeout_match_ms": 50000000,
        "timeout_turn_ms": 60000,  # 60 seconds maximum allowed for each move
        "num_games": 1000000000,  # num_games or max_steps, whichever reaches first, here we set num_games arbitrarily high and uses max_steps 
        "max_steps": 100000,
        "num_processes": 24,
        "output_file": "gomoku_data_repeat8.tsv",
        "samples_per_position": 8,  # Number of samples to collect per position
    }
    
    generate_self_play_data(
        engine_path,
        num_games=settings["num_games"], 
        max_steps=settings["max_steps"], 
        num_processes=settings["num_processes"],  
        output_file=settings["output_file"],
        max_memory_mb=settings["max_memory_mb_per_process"],
        timeout_match_ms=settings["timeout_match_ms"],
        timeout_turn_ms=settings["timeout_turn_ms"],
        samples_per_position=settings["samples_per_position"],
        visualize=False
    )