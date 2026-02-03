import json, os, time, random, re
import requests
from bs4 import BeautifulSoup

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BookoffStockWatcher/1.0)",
    "Accept-Language": "ja,en;q=0.8",
}

def is_in_stock(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # 在庫なし（最優先）
    if any(x in text for x in ["在庫なし", "入荷のお知らせを受け取る"]):
        return False

    # 在庫あり（強い手がかり）
    if any(x in text for x in ["カートに追加する", "カートに入れる"]):
        return True

    # 補助：残り◯点
    if re.search(r"残り\s*\d+\s*点", text):
        return True

    # 判定不能は安全側（誤通知防止）
    return False

def line_push(text: str) -> None:
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"}
    body = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": text}]}
    r = requests.post(url, headers=headers, json=body, timeout=15)
    # 失敗時に落として気づけるようにする
    r.raise_for_status()

with open("targets.json", encoding="utf-8") as f:
    targets = json.load(f)

try:
    with open("state.json", encoding="utf-8") as f:
        prev_state = json.load(f)
except Exception:
    prev_state = {}

new_state = dict(prev_state)
alerts = []

for t in targets:
    url = t["url"]
    label = t.get("label", url)

    # アクセス負荷対策：少し待つ
    time.sleep(random.uniform(1.0, 2.0))

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        now = is_in_stock(resp.text)
    except Exception as e:
        # 取得失敗は状態を変えない（誤通知防止）
        print(f"[WARN] failed: {url} err={e}")
        continue

    before = bool(prev_state.get(url, False))
    new_state[url] = now

    if (not before) and now:
        alerts.append(f"【再入荷】{label}\n{url}")

with open("state.json", "w", encoding="utf-8") as f:
    json.dump(new_state, f, ensure_ascii=False, indent=2)

if alerts:
    # まとめて1通（長すぎる場合は後で分割にします）
    line_push("\n\n".join(alerts))
    print(f"[INFO] notified: {len(alerts)}")
else:
    print("[INFO] no changes")

