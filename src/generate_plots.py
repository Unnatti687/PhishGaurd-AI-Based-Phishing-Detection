"""
PhishGuard - Publication-Quality Model Visualization Suite
==========================================================
Generates high-resolution PNG charts:
1. confusion_matrices.png: 2x2 grid of confusion matrices for all 4 models
2. roc_curves.png: Combined ROC curves with AUC annotations
3. feature_importance.png: Top 15 features for Random Forest & LR coefficients
4. model_comparison_bar.png: Grouped bar chart comparing key metrics

Uses professional coffee/warm neutral and slate styling matching project aesthetics.

Authors: Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_curve, auc, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Matplotlib visual styling
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = "#4E342E"
plt.rcParams["axes.linewidth"] = 0.8


def plot_all():
    print("[*] Generating publication-quality charts in results/ ...")
    metrics_path = RESULTS_DIR / "metrics.csv"
    eval_cache_path = RESULTS_DIR / "eval_cache.json"
    feat_imp_path = RESULTS_DIR / "feature_importance.json"

    if not metrics_path.exists() or not eval_cache_path.exists():
        print("[-] Metrics or eval cache missing. Run train.py first.")
        return

    metrics_df = pd.read_csv(metrics_path)
    with open(eval_cache_path, "r") as f:
        eval_cache = json.load(f)

    y_test = np.array(eval_cache["y_test"])
    predictions = eval_cache["predictions"]
    probabilities = eval_cache["probabilities"]

    # -------------------------------------------------------------
    # 1. CONFUSION MATRICES (2x2 Grid)
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    fig.patch.set_facecolor("#FAF8F5")
    models = list(predictions.keys())

    for idx, name in enumerate(models):
        ax = axes[idx // 2, idx % 2]
        ax.set_facecolor("#FFFFFF")
        y_pred = np.array(predictions[name])
        cm = confusion_matrix(y_test, y_pred)
        
        # Color map in warm coffee brown tones
        im = ax.imshow(cm, interpolation="nearest", cmap="YlOrBr")
        ax.set_title(f"{name}", fontsize=13, fontweight="bold", color="#2C1B18", pad=10)
        
        tick_marks = np.arange(2)
        ax.set_xticks(tick_marks)
        ax.set_yticks(tick_marks)
        ax.set_xticklabels(["Legitimate (0)", "Phishing (1)"], fontsize=10, color="#3E2723")
        ax.set_yticklabels(["Legitimate (0)", "Phishing (1)"], fontsize=10, color="#3E2723")

        # Annotations
        thresh = cm.max() / 2.0
        for i in range(2):
            for j in range(2):
                val = cm[i, j]
                pct = val / cm.sum() * 100
                color = "white" if val > thresh else "#2C1B18"
                ax.text(j, i, f"{val:,}\n({pct:.1f}%)",
                        ha="center", va="center", color=color,
                        fontsize=11, fontweight="bold")

        ax.set_ylabel("True Ground Truth", fontsize=11, color="#3E2723")
        ax.set_xlabel("Predicted Label", fontsize=11, color="#3E2723")

    plt.suptitle("Confusion Matrices - PhishGuard URL Classifier Suite", fontsize=15, fontweight="bold", color="#2C1B18", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    cm_path = RESULTS_DIR / "confusion_matrices.png"
    plt.savefig(cm_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {cm_path}")

    # -------------------------------------------------------------
    # 2. ROC CURVES
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#FAF8F5")
    ax.set_facecolor("#FFFFFF")

    palette = {
        "Logistic Regression": "#8D6E63",
        "Decision Tree": "#BCAAA4",
        "Random Forest": "#4E342E",
        "Support Vector Machine": "#212121"
    }

    for name in models:
        y_prob = np.array(probabilities[name])
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_auc = auc(fpr, tpr)
        color = palette.get(name, "#3E2723")
        lw = 2.5 if "Random Forest" in name else 1.8
        ax.plot(fpr, tpr, color=color, lw=lw, label=f"{name} (AUC = {roc_auc:.4f})")

    ax.plot([0, 1], [0, 1], color="#9E9E9E", lw=1.2, linestyle="--", label="Chance Baseline (AUC = 0.5000)")
    ax.set_xlim([-0.01, 1.0])
    ax.set_ylim([0.0, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold", color="#2C1B18")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold", color="#2C1B18")
    ax.set_title("Receiver Operating Characteristic (ROC) Curves", fontsize=14, fontweight="bold", color="#2C1B18", pad=12)
    ax.legend(loc="lower right", fontsize=10, framealpha=0.95, edgecolor="#4E342E")
    ax.grid(True, linestyle=":", alpha=0.6, color="#BCAAA4")

    roc_path = RESULTS_DIR / "roc_curves.png"
    plt.tight_layout()
    plt.savefig(roc_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {roc_path}")

    # -------------------------------------------------------------
    # 3. FEATURE IMPORTANCES & LR COEFFICIENTS
    # -------------------------------------------------------------
    if feat_imp_path.exists():
        with open(feat_imp_path, "r") as f:
            feat_imp = json.load(f)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
        fig.patch.set_facecolor("#FAF8F5")

        # RF Top 15
        rf_top = feat_imp.get("Random_Forest", {})
        features_rf = list(reversed(list(rf_top.keys())))
        scores_rf = list(reversed(list(rf_top.values())))

        ax1.set_facecolor("#FFFFFF")
        ax1.barh(features_rf, scores_rf, color="#4E342E", edgecolor="#2C1B18", height=0.65)
        ax1.set_title("Random Forest: Top 15 Features (Gini Importance)", fontsize=12, fontweight="bold", color="#2C1B18")
        ax1.set_xlabel("Mean Decrease in Impurity", fontsize=10, fontweight="bold", color="#3E2723")
        ax1.grid(True, axis="x", linestyle=":", alpha=0.6, color="#BCAAA4")

        # LR Top 15 coefficients
        lr_top = feat_imp.get("Logistic_Regression", {})
        features_lr = list(reversed(list(lr_top.keys())))
        coeffs_lr = list(reversed(list(lr_top.values())))
        colors_lr = ["#8D6E63" if c > 0 else "#212121" for c in coeffs_lr]

        ax2.set_facecolor("#FFFFFF")
        ax2.barh(features_lr, coeffs_lr, color=colors_lr, edgecolor="#2C1B18", height=0.65)
        ax2.set_title("Logistic Regression: Top 15 Feature Weights", fontsize=12, fontweight="bold", color="#2C1B18")
        ax2.set_xlabel("Coefficient (Brown: +Phishing, Dark: -Safe)", fontsize=10, fontweight="bold", color="#3E2723")
        ax2.axvline(0, color="#4E342E", linewidth=1.0)
        ax2.grid(True, axis="x", linestyle=":", alpha=0.6, color="#BCAAA4")

        plt.tight_layout()
        fi_path = RESULTS_DIR / "feature_importance.png"
        plt.savefig(fi_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close()
        print(f"[+] Saved: {fi_path}")

    # -------------------------------------------------------------
    # 4. MODEL COMPARISON GROUPED BAR CHART
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#FAF8F5")
    ax.set_facecolor("#FFFFFF")

    metrics_names = ["Test_Accuracy", "Test_Precision", "Test_Recall", "Test_F1", "Test_ROC_AUC"]
    display_labels = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC-AUC"]
    x = np.arange(len(display_labels))
    width = 0.18

    model_colors = ["#8D6E63", "#BCAAA4", "#4E342E", "#212121"]

    for i, row in metrics_df.iterrows():
        m_name = row["Model"]
        values = [row[m] for m in metrics_names]
        offset = (i - 1.5) * width
        rects = ax.bar(x + offset, values, width, label=m_name, color=model_colors[i % len(model_colors)], edgecolor="#1A1412")
        # Text above bar
        for rect in rects:
            h = rect.get_height()
            ax.annotate(f"{h:.3f}",
                        xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, rotation=45, color="#1A1412")

    ax.set_ylabel("Score", fontsize=11, fontweight="bold", color="#2C1B18")
    ax.set_title("Model Performance Benchmark (Held-Out Test Set)", fontsize=14, fontweight="bold", color="#2C1B18", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(display_labels, fontsize=11, fontweight="bold", color="#2C1B18")
    ax.set_ylim([0.70, 1.05])
    ax.legend(loc="lower right", fontsize=10, framealpha=0.95, edgecolor="#4E342E")
    ax.grid(True, axis="y", linestyle=":", alpha=0.6, color="#BCAAA4")

    comp_path = RESULTS_DIR / "model_comparison_bar.png"
    plt.tight_layout()
    plt.savefig(comp_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"[+] Saved: {comp_path}")
    print("[+] All publication charts generated successfully!")


if __name__ == "__main__":
    plot_all()
