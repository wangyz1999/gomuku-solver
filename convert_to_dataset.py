import csv
import json
import numpy as np
import ast
from tqdm import tqdm

def board_state_to_array(board_state):
    """Convert a board state string to a 15x15 numpy array."""
    # Initialize empty 15x15 board
    board = np.zeros((15, 15), dtype=int)
    
    # Parse the board state string
    moves = ast.literal_eval(board_state)
    for x, y, player in moves:
        board[y][x] = player
    
    return board

def board_to_string_representation(board):
    """Convert a board array to a human-readable string representation."""
    symbols = {0: ".", 1: "X", 2: "O"}
    rows = []
    
    # Add column numbers at the top
    header = "   " + " ".join([f"{i:2d}" for i in range(15)])
    rows.append(header)
    rows.append("   " + "-" * 29)
    
    for i in range(15):
        row = f"{i:2d}|"
        for j in range(15):
            row += f" {symbols[board[i][j]]}"
        rows.append(row)
    
    return "\n".join(rows)

def get_isomorphisms(board, move):
    """Generate all isomorphic versions of the board and corresponding move."""
    isomorphisms = []
    x, y = move
    
    # Original board
    isomorphisms.append((board.copy(), (x, y)))
    
    # Rotations (90, 180, 270 degrees)
    for k in range(1, 4):
        rotated_board = np.rot90(board, k=k)
        # For a 15x15 board, the new coordinates after rotation
        if k == 1:  # 90 degrees
            new_x, new_y = 14-y, x
        elif k == 2:  # 180 degrees
            new_x, new_y = 14-x, 14-y
        else:  # 270 degrees
            new_x, new_y = y, 14-x
        
        isomorphisms.append((rotated_board.copy(), (new_x, new_y)))
    
    # Flips and their rotations
    flipped_board = np.fliplr(board)
    flipped_x, flipped_y = 14-x, y
    isomorphisms.append((flipped_board.copy(), (flipped_x, flipped_y)))
    
    for k in range(1, 4):
        rotated_flipped_board = np.rot90(flipped_board, k=k)
        if k == 1:
            new_x, new_y = 14-flipped_y, flipped_x
        elif k == 2:
            new_x, new_y = 14-flipped_x, 14-flipped_y
        else:
            new_x, new_y = flipped_y, 14-flipped_x
        
        isomorphisms.append((rotated_flipped_board.copy(), (new_x, new_y)))
    
    return isomorphisms

def board_to_hash(board):
    """Convert a board array to a string representation for hashing."""
    return ''.join(str(int(cell)) for cell in board.flatten())

def convert_to_dataset(input_file, output_file, confidence_threshold=8):
    """
    Convert the TSV file to a clean dataset with isomorphism handling.
    
    Args:
        input_file: Path to the input TSV file
        output_file: Path to the output JSON file
        confidence_threshold: Only keep moves with this count or higher
    """
    dataset = []
    seen_positions = set()
    
    # Statistics counters
    total_positions = 0
    positions_after_confidence_filter = 0
    positions_after_isomorphism_filter = 0
    
    with open(input_file, 'r', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)  # Skip header
        
        # Count total rows first
        rows = list(reader)
        total_positions = len(rows)
        
        for row in tqdm(rows, desc="Processing positions"):
            board_state_str = row[0]
            best_move_str = row[1]
            candidate_moves_str = row[4]
            
            # Parse the best move
            best_move = ast.literal_eval(best_move_str)
            
            # Parse candidate moves to check confidence
            candidate_moves = ast.literal_eval(candidate_moves_str)
            best_move_key = str(best_move)
            
            # Only keep positions where the best move has high confidence
            if best_move_key in candidate_moves and candidate_moves[best_move_key]["count"] >= confidence_threshold:
                positions_after_confidence_filter += 1
                
                # Convert board state to array
                board = board_state_to_array(board_state_str)
                
                # Generate all isomorphic versions
                isomorphisms = get_isomorphisms(board, best_move)
                
                # Check if we've seen any isomorphic version of this position
                is_new_position = True
                for iso_board, _ in isomorphisms:
                    board_hash = board_to_hash(iso_board)
                    if board_hash in seen_positions:
                        is_new_position = False
                        break
                
                if is_new_position:
                    positions_after_isomorphism_filter += 1
                    
                    # Add the canonical version to the dataset
                    board_hash = board_to_hash(board)
                    seen_positions.add(board_hash)
                    
                    # Create string representation of the board
                    board_str = board_to_string_representation(board)
                    
                    # Format the move as a string (e.g., "C4")
                    move_str = f"({best_move[0]}, {best_move[1]})"
                    
                    # Create the prompt and ground truth
                    prompt = f"Here is a Gomoku board game state, find the best next move:\n\n{board_str}"
                    ground_truth = move_str
                    
                    dataset.append({
                        "prompt": prompt,
                        "ground_truth": ground_truth
                    })
    
    # Print statistics
    print("\nDataset Statistics:")
    print(f"Total positions in input file: {total_positions}")
    print(f"Positions after confidence filter (count >= {confidence_threshold}): {positions_after_confidence_filter} ({positions_after_confidence_filter/total_positions*100:.2f}%)")
    print(f"Positions after isomorphism filter: {positions_after_isomorphism_filter} ({positions_after_isomorphism_filter/positions_after_confidence_filter*100:.2f}% of confident positions)")
    print(f"Final dataset size: {len(dataset)}")
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\nDataset saved to {output_file}")

if __name__ == "__main__":
    # Settings
    input_file = "gomoku_data_repeat8.tsv"
    output_file = "gomoku_dataset.json"
    confidence_threshold = 8  # Only keep moves with this count or higher
    
    print(f"Processing {input_file} with confidence threshold {confidence_threshold}")
    convert_to_dataset(input_file, output_file, confidence_threshold) 