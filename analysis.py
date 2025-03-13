import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
import ast

# Read the TSV file
df = pd.read_csv('gomoku_data.tsv', sep='\t')

# Function to process evaluation values
def process_evaluation(eval_str):
    try:
        eval_str = str(eval_str).strip()
        if 'M' in eval_str:
            sign = 1 if eval_str.startswith('+') else -1
            number = int(eval_str.replace('+M', '').replace('-M', ''))
            return ('M', sign * number)
        else:
            return ('numeric', float(eval_str))
    except:
        return None

# Function to normalize board state
def normalize_board_state(board_state_str):
    try:
        # Convert string representation to list
        board_state = ast.literal_eval(board_state_str)
        # Sort the board state tuples
        return tuple(sorted(board_state))
    except:
        return None

# Process evaluations
processed_evals = df['evaluation'].apply(process_evaluation).dropna()

# Separate M-values and numeric values
m_values = [val[1] for val in processed_evals if val[0] == 'M']
numeric_values = [val[1] for val in processed_evals if val[0] == 'numeric']

# Create a figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Plot numeric values distribution
sns.histplot(numeric_values, bins=50, ax=ax1)
ax1.set_title('Distribution of Numeric Evaluations')
ax1.set_xlabel('Evaluation Score')
ax1.set_ylabel('Count')

# Plot M-values distribution
if m_values:
    sns.histplot(m_values, bins=20, ax=ax2)
    ax2.set_title('Distribution of M-values (Mate in N moves)')
    ax2.set_xlabel('Number of Moves to Mate (negative means losing)')
    ax2.set_ylabel('Count')

plt.tight_layout()
plt.show()

# Analyze duplicates with normalized board states
position_moves = df.apply(
    lambda row: (
        normalize_board_state(row['board_state']), 
        ast.literal_eval(row['best_move']) if isinstance(row['best_move'], str) else row['best_move']
    ), 
    axis=1
)
duplicate_counts = Counter(position_moves)

# Get statistics about duplicates
total_positions = len(position_moves)
unique_positions = len(duplicate_counts)
positions_with_duplicates = sum(1 for count in duplicate_counts.values() if count > 1)
max_duplicates = max(duplicate_counts.values())

# Print statistics
print("\nDuplicate Analysis:")
print(f"Total positions: {total_positions}")
print(f"Unique positions: {unique_positions}")
print(f"Positions with duplicates: {positions_with_duplicates}")
print(f"Maximum times a position appears: {max_duplicates}")

# Print most common duplicates (top 5)
print("\nTop 5 most repeated positions:")
for pos, count in sorted(duplicate_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"Board state: {pos[0]}")
    print(f"Best move: {pos[1]}")
    print(f"Appears {count} times\n")

print("\nNumeric Evaluations Statistics:")
print(f"Count: {len(numeric_values)}")
print(f"Mean: {np.mean(numeric_values):.2f}")
print(f"Median: {np.median(numeric_values):.2f}")
print(f"Min: {np.min(numeric_values):.2f}")
print(f"Max: {np.max(numeric_values):.2f}")

if m_values:
    print("\nM-values Statistics:")
    print(f"Count: {len(m_values)}")
    print(f"Mean moves to mate: {np.mean(m_values):.2f}")
    print(f"Median moves to mate: {np.median(m_values):.2f}")
    print(f"Min moves to mate: {np.min(m_values)}")
    print(f"Max moves to mate: {np.max(m_values)}")