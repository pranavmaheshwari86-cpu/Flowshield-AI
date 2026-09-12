import os
import re

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"

print("--- Inspecting PRD.md ---")
if os.path.exists(os.path.join(repo_dir, "PRD.md")):
    with open(os.path.join(repo_dir, "PRD.md"), "r", encoding="utf-8") as f:
        print(f.read()[:2000])

print("\n--- Inspecting TRD.md ---")
if os.path.exists(os.path.join(repo_dir, "TRD.md")):
    with open(os.path.join(repo_dir, "TRD.md"), "r", encoding="utf-8") as f:
        print(f.read()[:2000])

print("\n--- Inspecting README.md ---")
if os.path.exists(os.path.join(repo_dir, "README.md")):
    with open(os.path.join(repo_dir, "README.md"), "r", encoding="utf-8") as f:
        print(f.read()[:2000])
