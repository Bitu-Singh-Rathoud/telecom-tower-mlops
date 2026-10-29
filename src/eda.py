"""
Telecom Tower Failure Prediction — EDA Script
Group 3: Nishant & Bitu
Course: Elective II: Machine Learning Operations (MLOps)
Faculty: Dr. Santosh Kumar

Purpose: Generates reproducible Exploratory Data Analysis outputs:
  - Dataset summary statistics
  - Missing value analysis
  - Target class distribution
  - Feature distributions
  - Correlation analysis
  - Feature vs target relationships

Run from project root:
    python src/eda.py

Outputs written to:  reports/figures/  and  reports/tables/
"""

import os
import sys
import warnings
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(PROJECT_ROOT, "telecom_tower_failure.csv")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures")
TABLES_DIR = os.path.join(PROJECT_ROOT, "reports", "tables")

os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

# Consistent styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 150, "figure.figsize": (10, 6)})

TARGET = "Failure_Within_48Hrs"
RAW_COLS = [
    "Temperature_C",
    "Battery_Voltage",
    "Power_Consumption_W",
    "Signal_Strength_Percent",
    "Fan_Speed_RPM",
    "Humidity_Percent",
    "Traffic_Load",
    "Tower_Age_Years",
]


def load_data() -> pd.DataFrame:
    assert os.path.exists(DATA_FILE), f"Dataset not found: {DATA_FILE}"
    df = pd.read_csv(DATA_FILE)
    print(f"[EDA] Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def save_dataset_summary(df: pd.DataFrame):
    """Section 1: Basic dataset statistics."""
    print("[EDA] Generating dataset summary...")
    summary = df.describe(include="all").T
    summary.to_csv(os.path.join(TABLES_DIR, "dataset_summary.csv"))

    info = {
        "total_rows": int(len(df)),
        "total_columns": int(df.shape[1]),
        "feature_columns": RAW_COLS,
        "target_column": TARGET,
        "failure_count": int(df[TARGET].sum()),
        "normal_count": int((df[TARGET] == 0).sum()),
        "failure_rate_pct": round(100.0 * df[TARGET].mean(), 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values_total": int(df.isnull().sum().sum()),
    }
    with open(os.path.join(TABLES_DIR, "dataset_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(f"  Total rows:       {info['total_rows']}")
    print(f"  Failure rate:     {info['failure_rate_pct']}%")
    print(f"  Duplicate rows:   {info['duplicate_rows']}")
    print(f"  Missing values:   {info['missing_values_total']}")
    return info


def plot_target_distribution(df: pd.DataFrame):
    """Section 2: Target class distribution bar chart."""
    print("[EDA] Plotting target class distribution...")
    counts = df[TARGET].value_counts().sort_index()
    labels = ["Normal (0)", "Failure (1)"]
    colors = ["#4CAF50", "#F44336"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Bar chart
    axes[0].bar(labels, counts.values, color=colors, width=0.5, edgecolor="black", linewidth=0.7)
    axes[0].set_title("Target Class Distribution", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Count")
    for i, v in enumerate(counts.values):
        axes[0].text(i, v + 5, str(v), ha="center", va="bottom", fontweight="bold")

    # Pie chart
    axes[1].pie(
        counts.values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
    )
    axes[1].set_title("Failure Rate (Pie)", fontsize=14, fontweight="bold")

    plt.suptitle("Telecom Tower Failure Prediction — Target Variable Analysis", fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "01_target_distribution.png"), bbox_inches="tight")
    plt.close()
    print(f"  Saved: reports/figures/01_target_distribution.png")


def plot_missing_values(df: pd.DataFrame):
    """Section 3: Missing value heatmap."""
    print("[EDA] Plotting missing values...")
    missing = df[RAW_COLS].isnull().sum()
    missing_df = pd.DataFrame({"Feature": missing.index, "Missing_Count": missing.values})
    missing_df["Missing_Pct"] = round(100.0 * missing_df["Missing_Count"] / len(df), 2)
    missing_df.to_csv(os.path.join(TABLES_DIR, "missing_values.csv"), index=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors_bar = ["#E53935" if x > 0 else "#43A047" for x in missing_df["Missing_Count"]]
    ax.barh(missing_df["Feature"], missing_df["Missing_Pct"], color=colors_bar, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Missing Values (%)")
    ax.set_title("Missing Value Rate per Feature", fontsize=14, fontweight="bold")
    for i, (count, pct) in enumerate(zip(missing_df["Missing_Count"], missing_df["Missing_Pct"])):
        ax.text(pct + 0.1, i, f"{count} ({pct}%)", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "02_missing_values.png"), bbox_inches="tight")
    plt.close()
    print(f"  Saved: reports/figures/02_missing_values.png")


def plot_feature_distributions(df: pd.DataFrame):
    """Section 4: Feature histograms split by target class."""
    print("[EDA] Plotting feature distributions...")
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()

    for idx, col in enumerate(RAW_COLS):
        ax = axes[idx]
        fail_vals = df[df[TARGET] == 1][col].dropna()
        norm_vals = df[df[TARGET] == 0][col].dropna()
        ax.hist(norm_vals, bins=30, alpha=0.6, color="#4CAF50", label="Normal", density=True)
        ax.hist(fail_vals, bins=30, alpha=0.6, color="#F44336", label="Failure", density=True)
        ax.set_title(col, fontsize=10, fontweight="bold")
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        ax.legend(fontsize=8)

    plt.suptitle("Feature Distributions by Target Class", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "03_feature_distributions.png"), bbox_inches="tight")
    plt.close()
    print(f"  Saved: reports/figures/03_feature_distributions.png")


def plot_correlation_heatmap(df: pd.DataFrame):
    """Section 5: Correlation heatmap of features + target."""
    print("[EDA] Plotting correlation heatmap...")
    corr_cols = RAW_COLS + [TARGET]
    corr_matrix = df[corr_cols].corr()
    corr_matrix.to_csv(os.path.join(TABLES_DIR, "correlation_matrix.csv"))

    fig, ax = plt.subplots(figsize=(11, 9))
    mask = np.zeros_like(corr_matrix, dtype=bool)
    mask[np.triu_indices_from(mask)] = True  # Upper triangle mask
    sns.heatmap(
        corr_matrix,
        ax=ax,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        vmin=-1, vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    ax.set_title("Pearson Correlation Matrix (Features + Target)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "04_correlation_heatmap.png"), bbox_inches="tight")
    plt.close()
    print(f"  Saved: reports/figures/04_correlation_heatmap.png")


def plot_boxplots_by_target(df: pd.DataFrame):
    """Section 6: Box plots showing feature values grouped by failure class."""
    print("[EDA] Plotting box plots by target class...")
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    axes = axes.flatten()

    for idx, col in enumerate(RAW_COLS):
        ax = axes[idx]
        groups = [df[df[TARGET] == 0][col].dropna().values,
                  df[df[TARGET] == 1][col].dropna().values]
        try:
            bp = ax.boxplot(groups, tick_labels=["Normal (0)", "Failure (1)"],
                            patch_artist=True,
                            medianprops=dict(color="black", linewidth=2))
        except TypeError:
            bp = ax.boxplot(groups, labels=["Normal (0)", "Failure (1)"],
                            patch_artist=True,
                            medianprops=dict(color="black", linewidth=2))
        bp["boxes"][0].set_facecolor("#A5D6A7")
        bp["boxes"][1].set_facecolor("#EF9A9A")
        ax.set_title(col, fontsize=10, fontweight="bold")
        ax.set_ylabel("Value")

    plt.suptitle("Feature Box Plots Grouped by Failure Class", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "05_boxplots_by_class.png"), bbox_inches="tight")
    plt.close()
    print(f"  Saved: reports/figures/05_boxplots_by_class.png")


def run_eda():
    print("=" * 60)
    print("TELECOM TOWER MLOps — EDA SCRIPT")
    print("Group 3: Nishant & Bitu | Dr. Santosh Kumar")
    print("=" * 60)

    df = load_data()
    info = save_dataset_summary(df)
    plot_target_distribution(df)
    plot_missing_values(df)
    plot_feature_distributions(df)
    plot_correlation_heatmap(df)
    plot_boxplots_by_target(df)

    print("\n" + "=" * 60)
    print(f"EDA COMPLETE — {len(RAW_COLS)} features analysed")
    print(f"Dataset: {info['total_rows']} rows | Failure rate: {info['failure_rate_pct']}%")
    print(f"Figures saved in:  reports/figures/")
    print(f"Tables saved in:   reports/tables/")
    print("=" * 60)


if __name__ == "__main__":
    run_eda()
