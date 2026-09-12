import os

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"
matches = []

for root, _, files in os.walk(repo_dir):
    if any(p in root for p in ["node_modules", ".git", ".pytest_cache", ".gemini", "quarantined"]):
        continue
    for f in files:
        if f.endswith((".py", ".md")):
            path = os.path.join(root, f)
            rel = os.path.relpath(path, repo_dir)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fl:
                    content = fl.read().lower()
                    if "rainfall" in content and "model" in content:
                        # count occurrences or search for specific phrases
                        if any(phrase in content for phrase in ["rainfall model", "rainfall_model", "predict rainfall", "rainfall prediction", "rainfall forecast model"]):
                            matches.append(rel)
            except Exception:
                pass

print(f"Files with exact phrases ({len(matches)}):")
for m in matches:
    print(m)
