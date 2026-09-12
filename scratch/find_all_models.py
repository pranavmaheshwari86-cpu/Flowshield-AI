import os

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"
models = []

for root, _, files in os.walk(repo_dir):
    if any(p in root for p in [".git", ".pytest_cache", ".gemini"]):
        continue
    for f in files:
        if f.endswith((".joblib", ".pkl", ".h5", ".pt", ".pth", ".onnx", ".bin")):
            path = os.path.join(root, f)
            rel = os.path.relpath(path, repo_dir)
            size = os.path.getsize(path)
            models.append((rel, size))

print(f"Total model files found: {len(models)}")
for m, s in sorted(models):
    print(f"{m} ({s} bytes)")
