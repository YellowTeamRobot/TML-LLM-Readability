import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.linear_model import LinearRegression

def compare_scores(
    csv1_path: str,
    csv2_path: str,
    csv2_col_index: int,
    plot_output: str = "correlation_plot.png",
    title: str = "Correlation between Human and Automated Difficulty Scores"
):

    df1 = pd.read_csv(csv1_path)
    df2 = pd.read_csv(csv2_path)

    if "ID" not in df1.columns or "ID" not in df2.columns:
        raise ValueError("Both CSVs must have an 'ID' column in the header.")
    if df1.shape[1] < 23:
        raise ValueError("First CSV must have at least 23 columns.")
    if df2.shape[1] < csv2_col_index:
        raise ValueError(f"Second CSV must have at least {csv2_col_index} columns.")

    id_col = "ID"
    human_col = df1.columns[22]  # 23rd column (0-based index)
    auto_col = df2.columns[csv2_col_index - 1]

    df1_sub = df1[[id_col, human_col]]
    df2_sub = df2[[id_col, auto_col]]

    # --- Merge by ID ---
    merged = pd.merge(df1_sub, df2_sub, on=id_col, how="inner").dropna()
    y = merged[human_col].astype(float).to_numpy()
    x = merged[auto_col].astype(float).to_numpy()

    # --- Compute correlation stats ---
    pearson_corr, pearson_p = pearsonr(x, y)
    spearman_corr, spearman_p = spearmanr(x, y)
    kendall_corr, kendall_p = kendalltau(x, y)

    model = LinearRegression().fit(x.reshape(-1, 1), y)
    y_pred = model.predict(x.reshape(-1, 1))

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, label="Data points", alpha=0.7)
    plt.plot(x, y_pred, color="red", label="Line of best fit")
    plt.xlabel(f"Automated Score ({auto_col})")
    plt.ylabel(f"Human-Labelled Score ({human_col})")
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(plot_output, dpi=300)
    plt.show()

    print(f"Number of matching entries: {len(x)}")
    print(f"\nPearson correlation: {pearson_corr:.4f} (p = {pearson_p:.4e})")
    print(f"Spearman correlation: {spearman_corr:.4f} (p = {spearman_p:.4e})")
    print(f"Kendall correlation: {kendall_corr:.4f} (p = {kendall_p:.4e})")
    print(f"\nLinear regression: y = {model.coef_[0]:.4f}x + {model.intercept_:.4f}")
    print(f"R² = {model.score(x.reshape(-1,1), y):.4f}")
    print(f"Plot saved as: {plot_output}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 6:
        print("Usage: python script.py <human_csv> <automated_csv> <automated_col_index>")
        sys.exit(1)

    human_csv = sys.argv[1]
    automated_csv = sys.argv[2]
    automated_col_index = int(sys.argv[3])
    plot_output = sys.argv[4]
    title = sys.argv[5]
    

    compare_scores(human_csv, automated_csv, automated_col_index, plot_output, title)
