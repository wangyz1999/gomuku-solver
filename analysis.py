import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the TSV file
df = pd.read_csv('gomoku_data.tsv', sep='\t')

# Function to process evaluation values
def process_evaluation(eval_str):
    try:
        # Remove any whitespace and convert to string
        eval_str = str(eval_str).strip()
        
        # Check if it contains 'M'
        if 'M' in eval_str:
            # Extract the number after M and preserve the sign
            sign = 1 if eval_str.startswith('+') else -1
            number = int(eval_str.replace('+M', '').replace('-M', ''))
            return ('M', sign * number)
        else:
            # Regular numerical value
            return ('numeric', float(eval_str))
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
sns.histplot(numeric_values, bins=60, ax=ax1)
ax1.set_title('Distribution of Numeric Evaluations')
ax1.set_xlabel('Evaluation Score')
ax1.set_ylabel('Count')

# Plot M-values distribution
if m_values:  # Only plot if there are M-values
    sns.histplot(m_values, bins=60, ax=ax2)
    ax2.set_title('Distribution of M-values (Mate in N moves)')
    ax2.set_xlabel('Number of Moves to Mate (negative means losing)')
    ax2.set_ylabel('Count')

plt.tight_layout()
plt.show()

# Print some basic statistics
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