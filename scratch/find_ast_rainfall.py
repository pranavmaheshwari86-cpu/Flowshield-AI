import os
import ast
import re

repo_dir = r"c:\Users\Pranav\Desktop\Flowshield"

def search_ast():
    findings = []
    for root, _, files in os.walk(repo_dir):
        if any(p in root for p in ["node_modules", ".git", ".pytest_cache", ".gemini"]):
            continue
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                rel = os.path.relpath(path, repo_dir)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                        tree = ast.parse(content, filename=path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                if any(w in node.name.lower() for w in ["rain", "precip", "forecast"]):
                                    findings.append((rel, f"Class: {node.name}", node.lineno))
                            elif isinstance(node, ast.FunctionDef):
                                if any(w in node.name.lower() for w in ["rain", "precip", "forecast"]):
                                    findings.append((rel, f"Func: {node.name}", node.lineno))
                except Exception as e:
                    pass
    return findings

for f in search_ast():
    print(f[0], f[1], f"line {f[2]}")
