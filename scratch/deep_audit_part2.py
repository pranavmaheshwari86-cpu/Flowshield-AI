import os
import subprocess

repo_root = r"c:\Users\Pranav\Desktop\Flowshield"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, cwd=repo_root, capture_output=True, text=True)
    return res.stdout.strip()

print("=== 1. ALL UNTRACKED FILES IN REPO ===")
untracked = run_cmd("git status -s -uall")
print(untracked if untracked else "No untracked files (working tree clean according to current gitignore)")

print("\n=== 2. ROOT SCREENSHOTS TRACKING ===")
for f in os.listdir(repo_root):
    if f.endswith('.png'):
        tracked = run_cmd(f'git ls-files "{f}"')
        print(f"  {f:<35} -> {'TRACKED' if tracked else 'UNTRACKED'}")

print("\n=== 3. MEMORY DIRECTORY DETAILS ===")
mem_dir = os.path.join(repo_root, 'memory')
if os.path.exists(mem_dir):
    for f in os.listdir(mem_dir):
        fp = os.path.join(mem_dir, f)
        print(f"  {f:<35} | {os.path.getsize(fp)/1024:.1f} KB")

print("\n=== 4. GRAPHIFY-OUT DETAILS ===")
g_dir = os.path.join(repo_root, 'graphify-out')
if os.path.exists(g_dir):
    for f in os.listdir(g_dir):
        fp = os.path.join(g_dir, f)
        print(f"  {f:<35} | {os.path.getsize(fp)/1024:.1f} KB")

print("\n=== 5. CODE-REVIEW-GRAPH MCP SERVER CONFIG & USAGE ===")
mcp_dir = r"C:\Users\Pranav\.gemini\antigravity-ide\mcp\code-review-graph"
if os.path.exists(mcp_dir):
    print("code-review-graph mcp dir exists:")
    for f in os.listdir(mcp_dir):
        print(f"  {f}")
