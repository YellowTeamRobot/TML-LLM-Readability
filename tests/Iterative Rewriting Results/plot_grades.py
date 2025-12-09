import pandas as pd
import matplotlib.pyplot as plt
import sys
import re

def plot_grade_deviation_by_target(csv_file):
    # Load CSV
    df = pd.read_csv(csv_file)

    # Identify relevant columns
    target_col = df.columns[1]      # 2nd column: target grade
    cols = [df.columns[i] for i in [4,5,6,8]]   # calculated grades
    #method_cols = df.columns[4:7] + df.columns[8]
    method_cols = df.columns[[4,5,6,8]]
    # Remove rows where the target grade column has that message
    mask_valid = df[target_col] != "Excerpt already at or below desired grade level."
    df = df[mask_valid].copy()

    # Convert to numeric where possible
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    df[method_cols] = df[method_cols].apply(pd.to_numeric, errors='coerce')

    # Drop any rows where target grade is missing
    df = df.dropna(subset=[target_col])

    # For each method, compute deviation = calculated - target
    for method in method_cols:
        df[f"{method}_deviation"] = df[method] - df[target_col]

    # Plot one boxplot per method
    for method in method_cols:
        plt.figure(figsize=(8, 6))
        
        # Only keep rows where deviation and target grade are valid numbers
        valid = df[[target_col, f"{method}_deviation"]].dropna()
        
        # Create boxplot grouped by target grade level
        valid.boxplot(column=f"{method}_deviation", by=target_col, grid=False)
        plt.axhline(0, color='red', linestyle='--', linewidth=1)
        plt.title(f"LLM rewrote text given LLM (uncorrected) Grade Level")
        plt.suptitle("")
        plt.xlabel("Target Grade Level")
        method = re.sub(r"\(of rewritten\)", "", method)
        method = re.sub(r"\(of Rewritten\)", "", method)
        plt.ylabel(f"Deviation of {method} from Target Grade Level")
        plt.tight_layout()
        plt.savefig(f"LLM(uncorrected)_{method}_boxplot.png")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input.csv")
    else:
        plot_grade_deviation_by_target(sys.argv[1])
