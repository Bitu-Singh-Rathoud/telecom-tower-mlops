"""
Telecom Tower Failure Prediction — Model Evaluation Script
Group 3: Nishant & Bitu
Course: Elective II: Machine Learning Operations (MLOps)
Faculty: Dr. Santosh Kumar

Purpose: Reproducibly evaluates the saved model artifact on the held-out test set.
  - Loads model bundle and CSV dataset
  - Replicates the exact same 80/20 stratified split used in train.py
  - Computes all classification metrics: confusion matrix, accuracy, precision,
    recall, F1, ROC-AUC, PR-AUC
  - Compares RandomForest (main model) vs Logistic Regression (baseline)
  - Saves results to reports/results/ and reports/figures/

Run from project root:
    python src/evaluate.py

NOTE: This script does NOT re-train; it uses the existing saved bundle.
      It does re-create the test split identically (same seed=42, stratify=y).
"""

import os
import json
import sys
import warnings
import joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timezone

warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.features import TowerFeatureTransformer, RAW_COLS

DATA_FILE   = os.path.join(PROJECT_ROOT, "telecom_tower_failure.csv")
BUNDLE_PATH = os.path.join(PROJECT_ROOT, "artifacts", "model_v1.0.0.joblib")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "reports", "results")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures")
TABLES_DIR  = os.path.join(PROJECT_ROOT, "reports", "tables")

for d in [RESULTS_DIR, FIGURES_DIR, TABLES_DIR]:
    os.makedirs(d, exist_ok=True)

TARGET = "Failure_Within_48Hrs"
RANDOM_STATE = 42
sns.set_theme(style="whitegrid")


def load_data_and_split():
    """Load dataset and reproduce the exact same 80/20 stratified split."""
    assert os.path.exists(DATA_FILE), f"Dataset not found: {DATA_FILE}"
    df = pd.read_csv(DATA_FILE)
    X = df[RAW_COLS]
    y = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    return X_train, X_test, y_train, y_test, df


def evaluate_model(model, transformer, X_test_raw, y_test, threshold, model_name):
    """Compute full classification metrics for a model."""
    X_test_tf = transformer.transform(X_test_raw)
    probs = model.predict_proba(X_test_tf)[:, 1]
    preds = (probs >= threshold).astype(int)

    cm = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel()

    roc_auc = roc_auc_score(y_test, probs)
    pr_auc  = average_precision_score(y_test, probs)
    acc     = accuracy_score(y_test, preds)
    prec    = precision_score(y_test, preds, zero_division=0)
    rec     = recall_score(y_test, preds, zero_division=0)
    f1      = f1_score(y_test, preds, zero_division=0)
    spec    = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    report = classification_report(y_test, preds, output_dict=True, zero_division=0)

    metrics = {
        "model_name":  model_name,
        "threshold":   threshold,
        "test_samples": len(y_test),
        "positives":   int(y_test.sum()),
        "negatives":   int((y_test == 0).sum()),
        "TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn),
        "accuracy":    round(acc, 4),
        "precision":   round(prec, 4),
        "recall":      round(rec, 4),
        "specificity": round(spec, 4),
        "f1_score":    round(f1, 4),
        "roc_auc":     round(roc_auc, 4),
        "pr_auc":      round(pr_auc, 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }
    return metrics, probs


def plot_confusion_matrix(cm_data, model_name, filename):
    """Confusion matrix heatmap."""
    cm = np.array(cm_data)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Predicted Normal", "Predicted Failure"],
                yticklabels=["Actual Normal", "Actual Failure"],
                linewidths=0.5, linecolor="gray", ax=ax)
    ax.set_title(f"Confusion Matrix — {model_name}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), bbox_inches="tight")
    plt.close()


def plot_roc_curves(roc_data, filename):
    """Overlay ROC curves for all evaluated models."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1.5, label="Random baseline (AUC = 0.50)")

    for name, fpr, tpr, auc_val in roc_data:
        ax.plot(fpr, tpr, lw=2, label=f"{name} (AUC = {auc_val:.4f})")

    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=12)
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=12)
    ax.set_title("ROC Curves — Model Comparison", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), bbox_inches="tight")
    plt.close()


def plot_pr_curves(pr_data, filename):
    """Overlay Precision-Recall curves."""
    fig, ax = plt.subplots(figsize=(8, 6))

    for name, prec_vals, rec_vals, auc_val in pr_data:
        ax.plot(rec_vals, prec_vals, lw=2, label=f"{name} (PR-AUC = {auc_val:.4f})")

    ax.set_xlabel("Recall (Sensitivity)", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title("Precision-Recall Curves — Model Comparison", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), bbox_inches="tight")
    plt.close()


def plot_feature_importance(model, feature_names, filename):
    """Feature importance bar chart (for tree-based models)."""
    if not hasattr(model, "feature_importances_"):
        print("  (Skipping feature importance: model does not expose feature_importances_)")
        return

    imp = pd.Series(model.feature_importances_, index=feature_names).sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    imp.plot(kind="barh", ax=ax, color="#1565C0", edgecolor="white")
    ax.set_xlabel("Mean Decrease in Impurity (Feature Importance)", fontsize=11)
    ax.set_title("Random Forest — Feature Importances", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, filename), bbox_inches="tight")
    plt.close()


def run_evaluation():
    print("=" * 60)
    print("TELECOM TOWER MLOps — MODEL EVALUATION SCRIPT")
    print("Group 3: Nishant & Bitu | Dr. Santosh Kumar")
    print("=" * 60)

    # ---------- Load data and split ----------
    X_train, X_test, y_train, y_test, df = load_data_and_split()
    print(f"\n[EVAL] Dataset: {len(df)} rows | Test set: {len(X_test)} rows")
    print(f"  Test set failure rate: {100*y_test.mean():.1f}%")

    # ---------- Load saved Random Forest bundle ----------
    assert os.path.exists(BUNDLE_PATH), f"Model bundle not found: {BUNDLE_PATH}"
    bundle = joblib.load(BUNDLE_PATH)
    rf_model = bundle["model"]
    transformer = bundle["transformer"]
    threshold = bundle.get("threshold", 0.5)
    print(f"\n[EVAL] Loaded model: {type(rf_model).__name__} | threshold={threshold}")

    # ---------- Evaluate Random Forest ----------
    rf_metrics, rf_probs = evaluate_model(
        rf_model, transformer, X_test, y_test, threshold, "RandomForestClassifier"
    )

    print("\n--- Random Forest Test Set Results ---")
    print(f"  Accuracy:    {rf_metrics['accuracy']:.4f}")
    print(f"  Precision:   {rf_metrics['precision']:.4f}")
    print(f"  Recall:      {rf_metrics['recall']:.4f}  <- (failure detection rate)")
    print(f"  Specificity: {rf_metrics['specificity']:.4f}")
    print(f"  F1-Score:    {rf_metrics['f1_score']:.4f}")
    print(f"  ROC-AUC:     {rf_metrics['roc_auc']:.4f}")
    print(f"  PR-AUC:      {rf_metrics['pr_auc']:.4f}")
    print(f"  Confusion Matrix: TN={rf_metrics['TN']}, FP={rf_metrics['FP']}, FN={rf_metrics['FN']}, TP={rf_metrics['TP']}")

    # ---------- Baseline: Logistic Regression ----------
    print("\n[EVAL] Training baseline Logistic Regression for comparison...")
    lr_transformer = TowerFeatureTransformer()
    lr_transformer.fit(X_train)
    X_train_tf = lr_transformer.transform(X_train)
    X_test_tf  = lr_transformer.transform(X_test)

    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE)
    lr.fit(X_train_tf, y_train)

    lr_metrics, lr_probs = evaluate_model(
        lr, lr_transformer, X_test, y_test, threshold, "LogisticRegression (Baseline)"
    )

    print("\n--- Logistic Regression (Baseline) Test Set Results ---")
    print(f"  Accuracy:    {lr_metrics['accuracy']:.4f}")
    print(f"  Precision:   {lr_metrics['precision']:.4f}")
    print(f"  Recall:      {lr_metrics['recall']:.4f}")
    print(f"  F1-Score:    {lr_metrics['f1_score']:.4f}")
    print(f"  ROC-AUC:     {lr_metrics['roc_auc']:.4f}")
    print(f"  PR-AUC:      {lr_metrics['pr_auc']:.4f}")

    # ---------- Save confusion matrices ----------
    plot_confusion_matrix(rf_metrics["confusion_matrix"], "RandomForestClassifier",
                          "06_confusion_matrix_rf.png")
    plot_confusion_matrix(lr_metrics["confusion_matrix"], "LogisticRegression (Baseline)",
                          "07_confusion_matrix_lr.png")
    print("\n[EVAL] Confusion matrix figures saved.")

    # ---------- ROC curves ----------
    fpr_rf, tpr_rf, _ = roc_curve(y_test, rf_probs)
    fpr_lr, tpr_lr, _ = roc_curve(y_test, lr_probs)
    roc_data = [
        ("RandomForestClassifier", fpr_rf, tpr_rf, rf_metrics["roc_auc"]),
        ("LogisticRegression (Baseline)", fpr_lr, tpr_lr, lr_metrics["roc_auc"]),
    ]
    plot_roc_curves(roc_data, "08_roc_curves.png")
    print("[EVAL] ROC curves saved.")

    # ---------- PR curves ----------
    prec_rf, rec_rf, _ = precision_recall_curve(y_test, rf_probs)
    prec_lr, rec_lr, _ = precision_recall_curve(y_test, lr_probs)
    pr_data = [
        ("RandomForestClassifier", prec_rf, rec_rf, rf_metrics["pr_auc"]),
        ("LogisticRegression (Baseline)", prec_lr, rec_lr, lr_metrics["pr_auc"]),
    ]
    plot_pr_curves(pr_data, "09_pr_curves.png")
    print("[EVAL] PR curves saved.")

    # ---------- Feature importance ----------
    X_test_tf_rf = transformer.transform(X_test)
    feature_names = list(X_test_tf_rf.columns)
    plot_feature_importance(rf_model, feature_names, "10_feature_importance.png")
    print("[EVAL] Feature importance chart saved.")

    # ---------- Model comparison table ----------
    comparison = pd.DataFrame([
        {
            "Model": rf_metrics["model_name"],
            "Accuracy": rf_metrics["accuracy"],
            "Precision": rf_metrics["precision"],
            "Recall": rf_metrics["recall"],
            "Specificity": rf_metrics["specificity"],
            "F1-Score": rf_metrics["f1_score"],
            "ROC-AUC": rf_metrics["roc_auc"],
            "PR-AUC": rf_metrics["pr_auc"],
            "Threshold": threshold,
        },
        {
            "Model": lr_metrics["model_name"],
            "Accuracy": lr_metrics["accuracy"],
            "Precision": lr_metrics["precision"],
            "Recall": lr_metrics["recall"],
            "Specificity": lr_metrics["specificity"],
            "F1-Score": lr_metrics["f1_score"],
            "ROC-AUC": lr_metrics["roc_auc"],
            "PR-AUC": lr_metrics["pr_auc"],
            "Threshold": threshold,
        },
    ])
    comparison.to_csv(os.path.join(TABLES_DIR, "model_comparison.csv"), index=False)
    print("[EVAL] Model comparison table saved.")

    # ---------- Full metrics JSON ----------
    results = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": DATA_FILE,
        "test_split": "80/20 stratified (random_state=42)",
        "test_samples": len(y_test),
        "RandomForestClassifier": rf_metrics,
        "LogisticRegression_Baseline": lr_metrics,
    }
    # Remove non-serializable classification_report nested structure complexity
    for key in ["RandomForestClassifier", "LogisticRegression_Baseline"]:
        del results[key]["classification_report"]

    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("[EVAL] Metrics JSON saved.")

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print(f"  RandomForest  ROC-AUC = {rf_metrics['roc_auc']:.4f} | Recall = {rf_metrics['recall']:.4f}")
    print(f"  LR Baseline   ROC-AUC = {lr_metrics['roc_auc']:.4f} | Recall = {lr_metrics['recall']:.4f}")
    print(f"\nAll outputs saved to:")
    print(f"  reports/figures/  (confusion matrix, ROC, PR, feature importance)")
    print(f"  reports/tables/   (model_comparison.csv)")
    print(f"  reports/results/  (metrics.json)")
    print("=" * 60)
    return results


if __name__ == "__main__":
    run_evaluation()
