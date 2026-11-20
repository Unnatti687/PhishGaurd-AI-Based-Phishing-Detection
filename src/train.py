"""
PhishGuard - Model Training, Tuning, Evaluation & Explainability
================================================================
Trains 4 machine learning models (Logistic Regression, Decision Tree,
Random Forest, SVM) strictly on URL-only extracted features.

Features:
- Stratified 80/20 train/test split (random_state=42)
- Scaling ONLY for LR and SVM via Pipeline fitted on training set
- 5-fold cross-validation on training set
- Complete evaluation metrics: Accuracy, Precision, Recall, F1, ROC-AUC
- Real test set Error Analysis (False Positives & False Negatives)
- Feature Importance & Model Explainability
- Exporting best model, metrics.csv, error_analysis.csv, and model comparisons

Authors: Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)
"""

import time
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from data_loader import load_and_clean_data
from feature_extractor import extract_url_features, FEATURE_NAMES

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_features_from_dataframe(df: pd.DataFrame, cache_path: Path = None) -> pd.DataFrame:
    """Extract URL-only features for all rows in df, using caching for speed."""
    if cache_path and cache_path.exists():
        print(f"[*] Loading pre-extracted features from: {cache_path}")
        return pd.read_csv(cache_path)

    print(f"[*] Extracting URL-only features from {len(df)} URLs...")
    start_t = time.time()
    feature_rows = []
    for url in df["url"]:
        feature_rows.append(extract_url_features(url))
    
    feat_df = pd.DataFrame(feature_rows)
    feat_df["url"] = df["url"].values
    feat_df["label"] = df["label"].values

    elapsed = time.time() - start_t
    print(f"[+] Feature extraction completed in {elapsed:.2f}s ({elapsed / len(df) * 1000:.3f} ms/URL)")

    if cache_path:
        feat_df.to_csv(cache_path, index=False)
        print(f"[+] Cached extracted features to: {cache_path}")

    return feat_df


def train_and_evaluate_all():
    """Execute complete end-to-end ML pipeline according to SRM IST presentation specs."""
    print("=" * 70)
    print("PHISHGUARD: MACHINE LEARNING PIPELINE EXECUTION")
    print("SRM Institute of Science and Technology")
    print("Authors: Daksh Jaiswal & Unnatti Dixit")
    print("=" * 70)

    # 1. Load and clean raw data
    df_raw = load_and_clean_data(verbose=True)

    # 2. Extract URL-only features
    cache_file = DATA_DIR / "extracted_url_features.csv"
    features_df = extract_features_from_dataframe(df_raw, cache_path=cache_file)

    # Prepare feature matrix X and ground-truth y
    feature_cols = [c for c in features_df.columns if c not in ["url", "label"]]
    X = features_df[feature_cols].copy()
    y = features_df["label"].copy()
    urls = features_df["url"].copy()

    # Save feature names list
    with open(RESULTS_DIR / "feature_names.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    joblib.dump(feature_cols, RESULTS_DIR / "feature_names.joblib")
    print(f"[+] Saved {len(feature_cols)} feature column names to results/")

    # 3. Stratified 80/20 train/test split (random_state=42, test set untouched)
    X_train, X_test, y_train, y_test, urls_train, urls_test = train_test_split(
        X, y, urls, test_size=0.20, stratify=y, random_state=42
    )

    print(f"\n[+] Train set: {X_train.shape[0]} samples (Class 0: {(y_train == 0).sum()}, Class 1: {(y_train == 1).sum()})")
    print(f"[+] Test set:  {X_test.shape[0]} samples (Class 0: {(y_test == 0).sum()}, Class 1: {(y_test == 1).sum()})")

    # 4. Define models (Pipelines for scaling where appropriate)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    model_definitions = {
        "Logistic Regression": {
            "pipeline": Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=1000, C=1.0, random_state=42))
            ]),
            "param_grid": {
                "classifier__C": [0.1, 1.0, 10.0]
            }
        },
        "Decision Tree": {
            "pipeline": Pipeline([
                ("classifier", DecisionTreeClassifier(max_depth=10, min_samples_split=10, random_state=42))
            ]),
            "param_grid": {
                "classifier__max_depth": [6, 10, 14],
                "classifier__min_samples_split": [5, 10]
            }
        },
        "Random Forest": {
            "pipeline": Pipeline([
                ("classifier", RandomForestClassifier(n_estimators=120, max_depth=16, min_samples_split=5, random_state=42, n_jobs=-1))
            ]),
            "param_grid": {
                "classifier__n_estimators": [100, 150],
                "classifier__max_depth": [12, 16]
            }
        },
        "Support Vector Machine": {
            "pipeline": Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", SVC(kernel="rbf", C=1.5, probability=True, max_iter=3000, random_state=42, cache_size=500))
            ]),
            "param_grid": {
                "classifier__C": [1.0, 2.0]
            }
        }
    }

    metrics_records = []
    trained_models = {}
    test_predictions = {}
    test_probabilities = {}
    cv_scores = {}

    print("\n" + "=" * 70)
    print("5-FOLD CROSS VALIDATION & HYPERPARAMETER TUNING (TRAINING SET)")
    print("=" * 70)

    for name, config in model_definitions.items():
        print(f"\n---> Training & Tuning: {name} ...")
        t0 = time.time()

        # Grid search tuning on training set only
        grid = GridSearchCV(
            config["pipeline"],
            config["param_grid"],
            cv=cv,
            scoring="f1",
            n_jobs=-1,
            refit=True
        )
        grid.fit(X_train, y_train)
        train_time = time.time() - t0

        best_estimator = grid.best_estimator_
        best_cv_f1 = grid.best_score_
        best_params = grid.best_params_
        trained_models[name] = best_estimator
        cv_scores[name] = best_cv_f1

        print(f"     Best 5-Fold CV F1: {best_cv_f1:.4f}")
        print(f"     Best Parameters:  {best_params}")
        print(f"     Training Time:    {train_time:.2f}s")

        # Evaluate on the untouched test set
        t_infer_start = time.time()
        y_pred = best_estimator.predict(X_test)
        infer_time = time.time() - t_infer_start
        pred_time_per_url_ms = (infer_time / len(X_test)) * 1000.0

        if hasattr(best_estimator, "predict_proba"):
            y_prob = best_estimator.predict_proba(X_test)[:, 1]
        else:
            y_prob = best_estimator.decision_function(X_test)

        test_predictions[name] = y_pred
        test_probabilities[name] = y_prob

        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        print(f"     [Test Results] Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | AUC: {auc:.4f}")
        print(f"     [Confusion Matrix] TN={tn}, FP={fp}, FN={fn}, TP={tp}")
        print(f"     Latency: {pred_time_per_url_ms:.3f} ms/URL")

        metrics_records.append({
            "Model": name,
            "CV_F1_Mean": round(best_cv_f1, 4),
            "Test_Accuracy": round(acc, 4),
            "Test_Precision": round(prec, 4),
            "Test_Recall": round(rec, 4),
            "Test_F1": round(f1, 4),
            "Test_ROC_AUC": round(auc, 4),
            "True_Negatives": int(tn),
            "False_Positives": int(fp),
            "False_Negatives": int(fn),
            "True_Positives": int(tp),
            "Train_Time_Sec": round(train_time, 2),
            "Inference_Latency_ms": round(pred_time_per_url_ms, 3),
            "Best_Params": str(best_params)
        })

    # Save metrics to CSV
    metrics_df = pd.DataFrame(metrics_records)
    metrics_path = RESULTS_DIR / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"\n[+] Saved test metrics table to: {metrics_path}")

    # 5. Best Model Selection
    # High recall on phishing (minimize FN) + balanced precision + low latency
    metrics_df["Score"] = metrics_df["Test_F1"] * 0.5 + metrics_df["Test_Recall"] * 0.3 + metrics_df["Test_Accuracy"] * 0.2
    best_row = metrics_df.sort_values(by="Score", ascending=False).iloc[0]
    best_model_name = best_row["Model"]
    best_model = trained_models[best_model_name]

    print("\n" + "=" * 70)
    print(f"BEST MODEL SELECTED: {best_model_name}")
    print(f"Selection Justification: Highest overall balance (F1={best_row['Test_F1']:.4f}, Recall={best_row['Test_Recall']:.4f}, Accuracy={best_row['Test_Accuracy']:.4f})")
    print(f"Low False Negatives: {best_row['False_Negatives']} missed out of {best_row['True_Positives'] + best_row['False_Negatives']} phishing URLs.")
    print("=" * 70)

    # Save best model
    best_model_path = RESULTS_DIR / "best_model.joblib"
    joblib.dump(best_model, best_model_path)
    print(f"[+] Saved best model to: {best_model_path}")

    # Also save all models for comparison dashboard
    for m_name, m_obj in trained_models.items():
        fname = m_name.lower().replace(" ", "_") + ".joblib"
        joblib.dump(m_obj, RESULTS_DIR / fname)

    # 6. Feature Importance & Coefficients Analysis
    print("\n" + "=" * 70)
    print("MODEL INTERPRETABILITY & FEATURE CONTRIBUTIONS (TOP 15)")
    print("=" * 70)

    importance_dict = {}

    # Random Forest importances
    rf_clf = trained_models["Random Forest"].named_steps["classifier"]
    rf_importances = pd.Series(rf_clf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    importance_dict["Random_Forest"] = rf_importances.head(15).to_dict()
    print("\n[Random Forest Top 15 Features (Gini Importance)]:")
    for f, imp in rf_importances.head(15).items():
        print(f"  - {f:26s}: {imp:.4f}")

    # Decision Tree importances
    dt_clf = trained_models["Decision Tree"].named_steps["classifier"]
    dt_importances = pd.Series(dt_clf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    importance_dict["Decision_Tree"] = dt_importances.head(15).to_dict()

    # Logistic Regression coefficients
    lr_clf = trained_models["Logistic Regression"].named_steps["classifier"]
    lr_coeffs = pd.Series(lr_clf.coef_[0], index=feature_cols).sort_values(key=abs, ascending=False)
    importance_dict["Logistic_Regression"] = lr_coeffs.head(15).to_dict()
    print("\n[Logistic Regression Top 15 Coefficients (Magnitude)]:")
    for f, coef in lr_coeffs.head(15).items():
        sign = "(+ Phishing)" if coef > 0 else "(- Safe)"
        print(f"  - {f:26s}: {coef:+.4f} {sign}")

    with open(RESULTS_DIR / "feature_importance.json", "w") as f:
        json.dump(importance_dict, f, indent=2)

    # 7. Error Analysis: Real False Positives and False Negatives
    print("\n" + "=" * 70)
    print(f"ERROR ANALYSIS FOR BEST MODEL ({best_model_name})")
    print("=" * 70)

    best_pred = test_predictions[best_model_name]
    best_prob = test_probabilities[best_model_name]

    test_analysis_df = pd.DataFrame({
        "url": urls_test.values,
        "true_label": y_test.values,
        "predicted_label": best_pred,
        "phishing_probability": best_prob
    })

    # False Positives: Legitimate website wrongly flagged as phishing
    fps = test_analysis_df[(test_analysis_df["true_label"] == 0) & (test_analysis_df["predicted_label"] == 1)].copy()
    # False Negatives: Phishing website wrongly flagged as legitimate
    fns = test_analysis_df[(test_analysis_df["true_label"] == 1) & (test_analysis_df["predicted_label"] == 0)].copy()

    fps["error_type"] = "False Positive (Legitimate -> Phishing)"
    fns["error_type"] = "False Negative (Phishing -> Legitimate)"

    error_df = pd.concat([fps, fns]).sort_values(by="phishing_probability", ascending=False)
    error_csv_path = RESULTS_DIR / "error_analysis.csv"
    error_df.to_csv(error_csv_path, index=False)
    print(f"[+] Total False Positives: {len(fps)}")
    print(f"[+] Total False Negatives: {len(fns)}")
    print(f"[+] Saved error analysis dataset to: {error_csv_path}")

    print("\nSample False Positives (Legitimate flagged as Phishing):")
    for _, row in fps.head(5).iterrows():
        print(f"  * URL: {row['url'][:70]} (Prob: {row['phishing_probability']:.3f})")

    print("\nSample False Negatives (Phishing missed as Safe):")
    for _, row in fns.head(5).iterrows():
        print(f"  * URL: {row['url'][:70]} (Prob: {row['phishing_probability']:.3f})")

    # Save test dataset predictions for plotting ROC and confusion matrix
    eval_cache = {
        "y_test": y_test.tolist(),
        "predictions": {k: v.tolist() for k, v in test_predictions.items()},
        "probabilities": {k: v.tolist() for k, v in test_probabilities.items()}
    }
    with open(RESULTS_DIR / "eval_cache.json", "w") as f:
        json.dump(eval_cache, f)

    print("\n[+] ML Pipeline executed successfully!")
    return metrics_df, best_model_name


if __name__ == "__main__":
    train_and_evaluate_all()
