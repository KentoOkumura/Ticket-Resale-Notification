import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.message import EmailMessage

URL = "https://tradead.tixplus.jp/wbc2026/buy/bidding/listings/1517"
STATE_FILE = "state.json"

# SMTP設定（GitHub Secrets から取得）
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
MAIL_TO = os.environ.get("MAIL_TO")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GitHub Actions Ticket Monitor)"
}

def fetch_listings():
    """
    出品一覧を取得
    ※ セレクタは実ページに合わせて調整必須
    """
    res = requests.get(URL, headers=HEADERS, timeout=10)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # ここは必ずページに合わせて調整してください
    items = soup.select("div.listing-item")

    return [item.get_text(strip=True) for item in items]

def load_previous():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_current(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_email(new_items):
    msg = EmailMessage()
    msg["Subject"] = "【チケット通知】新しい出品があります"
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO

    body = "新しい出品を検出しました。\n\n"
    body += "\n".join(f"- {item}" for item in new_items)
    body += f"\n\n{URL}"

    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

def main():
    current = fetch_listings()
    previous = load_previous()

    new_items = list(set(current) - set(previous))

    if new_items:
        send_email(new_items)
    #send_email(["これはテストメールです（出品検知ロジックは正常）"],)

    save_current(current)

if __name__ == "__main__":
    main()
