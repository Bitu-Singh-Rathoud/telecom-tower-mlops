"""
Project Packaging Script — Creates a clean submission ZIP archive
Excludes temporary caches, virtualenvs, and .git to preserve space.
"""

import os
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
ZIP_OUTPUT = os.path.join(PARENT_DIR, "telecom_tower_mlops_complete_submission.zip")

EXCLUDE_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", ".idea", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".tmp"}

print(f"[*] Packaging project from: {PROJECT_ROOT}")
print(f"[*] Output ZIP archive:    {ZIP_OUTPUT}")

file_count = 0
total_size = 0

with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS or file.endswith("~"):
                continue
                
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
            
            # Put under a clean root folder inside ZIP
            archive_name = os.path.join("telecom-tower-mlops", rel_path)
            zipf.write(abs_path, archive_name)
            file_count += 1
            total_size += os.path.getsize(abs_path)

zip_size_mb = os.path.getsize(ZIP_OUTPUT) / (1024 * 1024)
print(f"[+] Successfully created ZIP with {file_count} files!")
print(f"[+] Total uncompressed size: {total_size / (1024 * 1024):.2f} MB")
print(f"[+] Compressed archive size: {zip_size_mb:.2f} MB")
