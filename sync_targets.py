import csv
import json
import os
from urllib.request import urlopen

CSV_URL = os.environ["TARGETS_CSV_URL"]

def main() -> None:
    with urlopen(CSV_URL) as r:
        text = r.read().decode("utf-8")

    rows = list(csv.DictReader(text.splitlines()))
    targets = []

    for row in rows:
        url = (row.get("bookoff_url") or row.get("url") or "").strip()
        label = (row.get("title") or row.get("label") or "").strip()

        # 空行は無視
        if not url:
            continue

        targets.append({
            "url": url,
            "label": label or url
        })

    with open("targets.json", "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False, indent=2)

    print(f"[INFO] targets.json updated: {len(targets)} items")

if __name__ == "__main__":
    main()
