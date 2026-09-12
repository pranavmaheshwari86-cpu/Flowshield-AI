import os

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"
results = []
for root, dirs, files in os.walk(repo_dir):
    if any(p in root for p in ["node_modules", ".git", ".pytest_cache", ".gemini"]):
        continue
    for f in files:
        if f.endswith((".py", ".json", ".md", ".joblib", ".pt", ".h5")):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, repo_dir)
            f_lower = f.lower()
            if any(k in f_lower for k in ["rain", "precip", "forecast", "weather", "meteo"]):
                results.append(relpath)

for r in sorted(results):
    print(r)
