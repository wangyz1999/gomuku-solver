import os
import csv
import multiprocessing as mp
from solver import GomokuSolver


def generate_data_worker(engine_path, worker_id, num_games, max_steps, output_file, visualize=False):
    solver = GomokuSolver(engine_path)
    current_step = 0
    
    # Open file in append mode
    with open(output_file, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        
        for i in range(num_games):
            print(f"Worker {worker_id}: Starting game {i+1}/{num_games}")
            current_board_state = []
            while True:
                parsed_response, raw_output_str = solver.get_best_move(current_board_state)
                
                # Save data and flush immediately
                if current_board_state:
                    writer.writerow([
                        str(current_board_state),
                        str(parsed_response["best_move"]),
                        str(parsed_response["evaluation"])
                    ])
                    f.flush()
                
                # update board state
                current_board_state = parsed_response["new_board_state"]
                # Switch sides for next move
                current_board_state = solver.switch_board_side(current_board_state)
                
                if visualize:
                    solver.visualize_board(current_board_state)
                
                winner = solver.check_winner(current_board_state)
                current_step += 1
                
                if winner or current_step >= max_steps:
                    break

def generate_self_play_data(engine_path, num_games=10, max_steps=100, visualize=False, num_processes=1, output_file="gomoku_data.tsv", **kwargs):
    # Create output file with headers if it doesn't exist
    if not os.path.exists(output_file):
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["board_state", "best_move", "evaluation"])
    
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
                    args=(engine_path, i, process_games, max_steps, output_file, visualize)
                )
                processes.append(p)
                p.start()
        
        # Wait for all processes to complete
        for p in processes:
            p.join()
    else:
        # Single process mode
        generate_data_worker(engine_path, 0, num_games, max_steps, output_file, visualize)


if __name__ == "__main__":
    engine_path = os.path.join("engines", "EMBRYO21.E", "pbrain-embryo21_e.exe")
    
    # Create settings dictionary
    settings = {
        "board_size": 15,
        "max_memory_mb_per_process": 80,
        "timeout_match_ms": 50000000,
        "timeout_turn_ms": 60000,  # 60 seconds maximum allowed for each move
        "num_games": 1000000000,  # num_games or max_steps, whichever reaches first, here we set num_games arbitrarily high and uses max_steps 
        "max_steps": 10000,
        "num_processes": 24,
        "output_file": "gomoku_data.tsv",
    }
    
    generate_self_play_data(
        engine_path,
        num_games=settings["num_games"], 
        max_steps=settings["max_steps"], 
        num_processes=settings["num_processes"],  
        output_file=settings["output_file"],
        visualize=False
    )