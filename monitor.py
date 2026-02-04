import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

URL = "https://tradead.tixplus.jp/wbc2026/buy/bidding/listings/1517"
STATE_FILE = "state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (TicketMonitor/1.0)"
}

# =====================
# 出品数を取得
# =====================
def extract_listing_count(html: str) -> int | None:
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find("main")
    if not main:
        return None

    # script/style除去
    for tag in main(["script", "style", "noscript"]):
        tag.decompose()

    # pタグで「数字のみ」のものを列挙
    numeric_ps = [
        p for p in main.find_all("p")
        if p.get_text(strip=True).isdigit()
    ]

    if not numeric_ps:
        return None

    # XPathの深さ的に「最も深い p」を採用（重要）
    def depth(tag):
        d = 0
        while tag.parent:
            d += 1
            tag = tag.parent
        return d

    target = max(numeric_ps, key=depth)
    return int(target.get_text(strip=True))


# =====================
# メール送信
# =====================
def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["MAIL_TO"]

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.send_message(msg)


# =====================
# state 操作
# =====================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =====================
# main
# =====================
def main():
    res = requests.get(URL, headers=HEADERS, timeout=15)
    res.raise_for_status()

    count = extract_listing_count(res.text)
    if count is None:
        print("出品数を取得できませんでした")
        return

    state = load_state()
    prev = state.get("count")

    # 0 → 1以上 の瞬間だけ通知
    if prev is not None and prev == 0 and count > 0:
        send_email(
            subject="【チケット出品あり】",
            body=f"{count} 件の出品が確認されました。\n\n{URL}"
        )

    save_state({"count": count})
    print(f"現在の出品数: {count}")


if __name__ == "__main__":
    main()
