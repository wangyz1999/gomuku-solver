from solver import GomokuSolver
import os

def demo_self_play(solver):
    current_board_state = []
    is_player_1 = True
    while True:
        parsed_response, raw_output_str = solver.get_best_move(current_board_state)

        next_player = "X" if is_player_1 else "O"
        print(f"Current Player: {next_player}")
        print("Current Board State: ")
        if is_player_1:
            solver.visualize_board(current_board_state, player1_symbol="X", player2_symbol="O")
        else:
            solver.visualize_board(current_board_state, player1_symbol="O", player2_symbol="X")
        print("Best Move: ", parsed_response["best_move"])
        print("Evaluation: ", parsed_response["evaluation"])
        
        current_board_state = parsed_response["new_board_state"]
        current_board_state = solver.switch_board_side(current_board_state)
        
        is_player_1 = not is_player_1
        winner = solver.check_winner(current_board_state)
        if winner:
            print("Ending Board State: ")
            if is_player_1:
                solver.visualize_board(current_board_state, player1_symbol="X", player2_symbol="O")
            else:
                solver.visualize_board(current_board_state, player1_symbol="O", player2_symbol="X")
            print(f"Winner: {'O' if is_player_1 else 'X'}")
            break
            
if __name__ == "__main__":
    engine_path = os.path.join("engines", "EMBRYO21.E", "pbrain-embryo21_e.exe")
    solver = GomokuSolver(engine_path)
    demo_self_play(solver)