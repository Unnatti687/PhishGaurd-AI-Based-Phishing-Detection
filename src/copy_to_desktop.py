# -*- coding: utf-8 -*-
"""
Copy complete PhishGuard project and deliverable zip files
directly to the user's Desktop folder:
C:\\Users\\UNNATTI\\Desktop\\phishgaurd
"""

import os
import shutil
from pathlib import Path

src_project = Path(r"C:\Users\UNNATTI\.gemini\antigravity\scratch\phishguard")
scratch_dir = Path(r"C:\Users\UNNATTI\.gemini\antigravity\scratch")
dest_desktop = Path(r"C:\Users\UNNATTI\Desktop\phishgaurd")

print(f"[*] Copying PhishGuard project to: {dest_desktop}")

# Ensure clean destination directory
if dest_desktop.exists():
    shutil.rmtree(dest_desktop)

# Copy the entire project directory tree
shutil.copytree(
    src_project,
    dest_desktop,
    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")
)

# Also copy the 3 distribution zip files into a 'zips' folder inside Desktop/phishgaurd
zips_folder = dest_desktop / "zips"
zips_folder.mkdir(exist_ok=True)

zip_names = [
    "phishguard-full-project.zip",
    "phishguard-backend.zip",
    "phishguard-frontend.zip"
]

for zn in zip_names:
    src_zip = scratch_dir / zn
    if src_zip.exists():
        shutil.copy2(src_zip, zips_folder / zn)
        print(f"[+] Copied {zn} -> {zips_folder / zn}")

print("\n" + "=" * 60)
print(f"[SUCCESS] All project files successfully saved to:")
print(f"--> {dest_desktop}")
print("=" * 60)
print("Contents:")
for p in sorted(dest_desktop.iterdir()):
    if p.is_dir():
        print(f"  [DIR]  {p.name}/")
    else:
        print(f"  [FILE] {p.name}")
