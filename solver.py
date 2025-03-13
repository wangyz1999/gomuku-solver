import subprocess
import re


class GomokuSolver:
    def __init__(self, engine_path, board_size=15, max_memory_mb=50, timeout_match_ms=180000, timeout_turn_ms=5000):
        self.engine_process = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.board_size = board_size
        self.max_memory = max_memory_mb * 1024 * 1024
        self.timeout_match_ms = timeout_match_ms
        self.timeout_turn_ms = timeout_turn_ms
        self.send_command(f"START {self.board_size}\n")
        
    def send_command(self, command):
        self.engine_process.stdin.write(command)
        self.engine_process.stdin.flush()
        
    def read_move_response(self):
        # Read all output until we get a line in the format "number,number"
        all_output = []
        move_coordinates = None
        depth = None
        evaluation = None
        time_ms = None
        
        while True:
            line = self.engine_process.stdout.readline().strip()
            all_output.append(line)

            if line.startswith("MESSAGE"):
                message_parts = line.split()
                for i, part in enumerate(message_parts):
                    if part == "depth" and i+1 < len(message_parts):
                        depth = message_parts[i+1]
                    elif part == "ev" and i+1 < len(message_parts):
                        evaluation = message_parts[i+1]
                    elif part == "tm" and i+1 < len(message_parts):
                        time_ms = message_parts[i+1]
            
            # Check if the line matches the pattern "number,number"
            if re.match(r'^\d+,\d+$', line):
                x, y = map(int, line.split(','))
                move_coordinates = (x, y)
                break
                
        raw_output_str = chr(10).join(all_output)
        
        return move_coordinates, depth, evaluation, time_ms, raw_output_str
        
    def parse_opening_states_from_file(self, openings_file):
        opening_states = []
        current_state = []
        with open(openings_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    continue
                if line == '':
                    opening_states.append(current_state)
                    current_state = []
                    continue
                
                try:
                    x, y, player = map(int, line.split(','))
                    current_state.append((x, y, player))
                except ValueError:
                    print(f"Warning: Skipping invalid line format: {line}")
            
            if current_state:
                opening_states.append(current_state)
            
        return opening_states

    def generate_data_from_openings_file(self, openings_file, max_steps=100):
        """
        Parse an openings file and generate game data from each starting position.
        
        Args:
            openings_file (str): Path to the file containing opening positions
            max_steps (int): Maximum number of moves to play from each opening
            
        Returns:
            list: List of game data generated from the openings
        """
        opening_states = self.parse_opening_states_from_file(openings_file)
        for opening_state in opening_states:
            print(opening_state)
            parsed_response, raw_output_str = self.get_best_move(opening_state)
            print(parsed_response["best_move"])
            print(parsed_response["evaluation"])
            
    def switch_board_side(self, board_state):
        new_board_state = []
        for move in board_state:
            new_board_state.append((move[0], move[1], 1 if move[2] == 2 else 2))
        return new_board_state
            
    def get_best_move(self, board_state):
        ## Treating each move as independent
        self.send_command("RESTART\n")
        self.send_command(f"INFO max_memory {self.max_memory}\n")
        self.send_command(f"INFO timeout_match {self.timeout_match_ms}\n")
        self.send_command(f"INFO timeout_turn {self.timeout_turn_ms}\n")
        self.send_command(f"INFO time_left {self.timeout_match_ms}\n")
        self.send_command("BOARD\n")
        for move in board_state:
            self.send_command(f"{move[0]},{move[1]},{move[2]}\n")
        self.send_command("DONE\n")
        
        # Read the response
        move_coordinates, depth, evaluation, time_ms, raw_output_str = self.read_move_response()
        
        new_board_state = board_state.copy()
        new_board_state.append((move_coordinates[0], move_coordinates[1], 1))
    
        parsed_response = {
            "best_move": move_coordinates,
            "new_board_state": new_board_state,
            "search_depth": depth,
            "evaluation": evaluation,
            "time_ms": time_ms,
        }    
        
        return parsed_response, raw_output_str
    
    def check_winner(self, board_state):
        """
        Check if there is a winner in the current board state.
        
        Args:
            board_state (list): List of tuples (x, y, player) representing the board
            
        Returns:
            int or None: 1 or 2 if there's a winner, None otherwise
        """
        # Create a dictionary to represent the board for faster lookups
        board_dict = {(move[0], move[1]): move[2] for move in board_state}
        
        # Check all positions on the board
        for x, y, player in board_state:
            # Check horizontal (→)
            if self._check_direction(board_dict, x, y, player, 1, 0):
                return player
                
            # Check vertical (↓)
            if self._check_direction(board_dict, x, y, player, 0, 1):
                return player
                
            # Check diagonal (↘)
            if self._check_direction(board_dict, x, y, player, 1, 1):
                return player
                
            # Check diagonal (↗)
            if self._check_direction(board_dict, x, y, player, 1, -1):
                return player
                
        return None
        
    def _check_direction(self, board_dict, x, y, player, dx, dy):
        """
        Check if there are 5 consecutive stones of the same player in a given direction.
        
        Args:
            board_dict (dict): Dictionary mapping (x, y) coordinates to player
            x, y (int): Starting coordinates
            player (int): Player to check for (1 or 2)
            dx, dy (int): Direction to check
            
        Returns:
            bool: True if there are 5 consecutive stones, False otherwise
        """
        # Check if this position could be the start of a winning line
        # Look backward to see if there's a stone of the same player
        if (x - dx, y - dy) in board_dict and board_dict[(x - dx, y - dy)] == player:
            return False
            
        # Count consecutive stones
        count = 0
        for i in range(5):  # Need 5 in a row to win
            curr_x, curr_y = x + i * dx, y + i * dy
            
            # Check if position is within board boundaries
            if not (0 <= curr_x < self.board_size and 0 <= curr_y < self.board_size):
                break
                
            # Check if position has the player's stone
            if (curr_x, curr_y) in board_dict and board_dict[(curr_x, curr_y)] == player:
                count += 1
            else:
                break
                
        return count >= 5
    
    def visualize_board(self, board_state, player1_symbol="X", player2_symbol="O"):
        """
        Visualize the current board state using ASCII art.
        
        Args:
            board_state (list): List of tuples (x, y, player) representing the board
        """
        # Create an empty board
        board = [[' ' for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # Fill in the board with player moves
        for x, y, player in board_state:
            if 0 <= x < self.board_size and 0 <= y < self.board_size:
                board[y][x] = player1_symbol if player == 1 else player2_symbol
        
        # Print column numbers
        print('  ', end='')
        for i in range(self.board_size):
            print(f'{i:3d}', end=' ')
        print()
        
        # Print top border
        print('  ┌' + '───┬' * (self.board_size - 1) + '───┐')
        
        # Print rows with borders
        for y in range(self.board_size):
            print(f'{y:2d}│', end='')
            for x in range(self.board_size):
                print(f' {board[y][x]} │', end='')
            print()
            
            # Print row separator (except after the last row)
            if y < self.board_size - 1:
                print('  ├' + '───┼' * (self.board_size - 1) + '───┤')
            else:
                print('  └' + '───┴' * (self.board_size - 1) + '───┘')

if __name__ == "__main__":
    generator = GomokuSolver(r"engines\EMBRYO21.E\pbrain-embryo21_e.exe")
    # generator.generate_data_from_openings_file(r"openings.txt")
    generator.generate_self_play_data()
    
    
    # generator = GomokuSolver(r"engines\EMBRYO21.E\pbrain-embryo21_e.exe")
    # print(generator.check_winner([(7, 7, 1), (6, 7, 2), (8, 6, 1), (6, 8, 2), (7, 5, 1), (7, 8, 2), (9, 7, 1), (6, 4, 2), (8,8,1),(9,9,1), (10,10,1), (11,11,1)]))
