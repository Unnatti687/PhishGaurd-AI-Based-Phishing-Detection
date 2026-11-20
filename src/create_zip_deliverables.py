# -*- coding: utf-8 -*-
"""
PhishGuard - Zip Deliverables Creator
=====================================
Builds the 3 clean distribution zip archives required by the user:
1. phishguard-full-project.zip
2. phishguard-backend.zip
3. phishguard-frontend.zip

Authors: Daksh Jaiswal & Unnatti Dixit
"""

import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR.parent


def should_exclude(rel_path: str) -> bool:
    """Ignore cache and temporary files."""
    parts = Path(rel_path).parts
    exclude_dirs = {"__pycache__", ".pytest_cache", ".git", ".idea", ".vscode", "venv", ".venv"}
    if any(p in exclude_dirs for p in parts):
        return True
    if rel_path.endswith((".pyc", ".pyo", ".pyd")):
        return True
    return False


def create_full_project_zip():
    zip_path = OUTPUT_DIR / "phishguard-full-project.zip"
    print(f"[*] Packaging full project to: {zip_path}")
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(BASE_DIR):
            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(BASE_DIR)
                if should_exclude(str(rel_path)):
                    continue
                archive_name = Path("phishguard") / rel_path
                z.write(full_path, str(archive_name))
                count += 1
    print(f"[+] Full project zip created with {count} files ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    return zip_path


def create_backend_zip():
    zip_path = OUTPUT_DIR / "phishguard-backend.zip"
    print(f"[*] Packaging backend to: {zip_path}")
    backend_include_dirs = ["backend", "src", "tests", "docs"]
    backend_include_files = ["requirements.txt", "README.md", "LICENSE", ".gitignore"]

    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in backend_include_files:
            fp = BASE_DIR / f
            if fp.exists():
                z.write(fp, f"phishguard-backend/{f}")
                count += 1

        for d in backend_include_dirs:
            dp = BASE_DIR / d
            if dp.exists():
                for root, dirs, files in os.walk(dp):
                    for file in files:
                        full_p = Path(root) / file
                        rel_p = full_p.relative_to(BASE_DIR)
                        if should_exclude(str(rel_p)):
                            continue
                        z.write(full_p, f"phishguard-backend/{rel_p}")
                        count += 1

        res_dir = BASE_DIR / "results"
        if res_dir.exists():
            for f in ["best_model.joblib", "feature_names.json", "metrics.csv", "error_analysis.csv"]:
                fp = res_dir / f
                if fp.exists():
                    z.write(fp, f"phishguard-backend/results/{f}")
                    count += 1

    print(f"[+] Backend zip created with {count} files ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    return zip_path


def create_frontend_zip():
    zip_path = OUTPUT_DIR / "phishguard-frontend.zip"
    print(f"[*] Packaging frontend to: {zip_path}")
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        front_dir = BASE_DIR / "frontend"
        for root, dirs, files in os.walk(front_dir):
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(front_dir)
                z.write(full_p, f"phishguard-frontend/{rel_p}")
                count += 1

        res_dir = BASE_DIR / "results"
        if res_dir.exists():
            for img in res_dir.glob("*.png"):
                z.write(img, f"phishguard-frontend/results/{img.name}")
                count += 1
            metrics_csv = res_dir / "metrics.csv"
            if metrics_csv.exists():
                z.write(metrics_csv, f"phishguard-frontend/results/metrics.csv")
                count += 1

    print(f"[+] Frontend zip created with {count} files ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    return zip_path


if __name__ == "__main__":
    create_full_project_zip()
    create_backend_zip()
    create_frontend_zip()
