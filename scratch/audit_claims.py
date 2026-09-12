import re
import glob

patterns = [
    r"100%",
    r"zero leakage",
    r"zero false positive",
    r"production[- ]ready",
    r"scientifically validated",
    r"government[- ]grade",
    r"high accuracy",
    r"state[- ]of[- ]the[- ]art",
    r"zero fabrication",
    r"zero data fabrication",
]

md_files = glob.glob("*.md") + glob.glob("docs/**/*.md", recursive=True) + glob.glob("ml/**/*.md", recursive=True)

findings = []
for f in sorted(md_files):
    try:
        lines = open(f, encoding="utf-8", errors="ignore").readlines()
        for i, line in enumerate(lines, 1):
            for p in patterns:
                if re.search(p, line, re.IGNORECASE):
                    findings.append((f, i, line.strip()))
    except Exception as e:
        pass

print(f"Total claims found: {len(findings)}")
for f, l, text in findings[:30]:
    print(f"[{f}:{l}] {text}")
