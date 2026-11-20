"""
PhishGuard - Data Loader & Preprocessing Module
================================================
Loads the Hannousse & Yahiouche benchmark dataset (11,430 URLs),
inspects class balance, handles missing values/duplicates, and prepares
the dataset for feature extraction and modeling.

Authors: Daksh Jaiswal (RA2411003030048) & Unnatti Dixit (RA2411003030009)
"""

import os
import shutil
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "dataset_phishing.csv"
FALLBACK_SOURCE = Path(r"C:\Users\UNNATTI\.gemini\antigravity\brain\adddb36b-35ac-4963-941c-9bdeff77f1b7\.system_generated\steps\19\content.md")


def ensure_dataset_exists() -> Path:
    """Ensure the benchmark dataset file is present and clean in data/ directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_DATA_PATH.exists() and RAW_DATA_PATH.stat().st_size > 100000:
        return RAW_DATA_PATH

    if FALLBACK_SOURCE.exists():
        print(f"[*] Preparing dataset from cache source: {FALLBACK_SOURCE}")
        with open(FALLBACK_SOURCE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        # Locate the header line starting with 'url,length_url'
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("url,length_url"):
                start_idx = i
                break
        
        with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
            for line in lines[start_idx:]:
                if line.strip():
                    f.write(line)
        print(f"[+] Dataset saved to: {RAW_DATA_PATH} ({RAW_DATA_PATH.stat().st_size:,} bytes)")
        return RAW_DATA_PATH

    raise FileNotFoundError(
        f"Dataset not found at {RAW_DATA_PATH} or {FALLBACK_SOURCE}. "
        "Please provide dataset_phishing.csv."
    )


def map_status_label(val) -> int:
    """Map string status to binary 0 (legitimate) or 1 (phishing)."""
    s = str(val).strip().lower()
    if s in ("1", "phishing", "malicious", "bad"):
        return 1
    return 0


def load_and_clean_data(verbose: bool = True) -> pd.DataFrame:
    """
    Load the dataset, verify columns, remove duplicates and missing values.
    Returns cleaned pandas DataFrame.
    """
    csv_path = ensure_dataset_exists()
    df = pd.read_csv(csv_path)

    if verbose:
        print("=" * 60)
        print("PHISHGUARD DATASET INSPECTION")
        print("=" * 60)
        print(f"Initial shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print("\nClass distribution (raw):")
        print(df["status"].value_counts(dropna=False))
        print(f"\nMissing values in dataset: {df.isnull().sum().sum()}")
        print(f"Duplicate rows based on 'url': {df.duplicated(subset=['url']).sum()}")

    # Clean: Drop duplicates by URL and missing values before train-test split
    df_clean = df.drop_duplicates(subset=["url"]).dropna(subset=["url", "status"]).copy()

    # Map status: legitimate -> 0, phishing -> 1
    df_clean["label"] = df_clean["status"].apply(map_status_label)

    if verbose:
        print("\nCleaned shape:", df_clean.shape)
        print("Cleaned class balance:")
        print(df_clean["label"].value_counts().rename({0: "0 (legitimate)", 1: "1 (phishing)"}))
        print("=" * 60)

    return df_clean


if __name__ == "__main__":
    df = load_and_clean_data(verbose=True)
