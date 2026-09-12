import os
import re

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"
keywords = ["rainfall", "precipitation", "weather_forecast", "numerical_weather"]

results = []
for root, dirs, files in os.walk(repo_dir):
    # skip node_modules, .git, venv, .pytest_cache
    if any(p in root for p in ["node_modules", ".git", ".pytest_cache", ".gemini"]):
        continue
    for f in files:
        if f.endswith((".py", ".json", ".md", ".joblib", ".pt", ".h5", ".csv")):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, repo_dir)
            f_lower = f.lower()
            if any(k in f_lower for k in ["rain", "precip", "forecast", "weather", "meteo"]):
                results.append(relpath)

print(f"Found {len(results)} files matching keywords:")
for r in sorted(results)[:60]:
    print(r)
if len(results) > 60:
    print(f"... and {len(results) - 60} more")
