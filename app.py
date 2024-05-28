from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('RzWJktVPSrCZr9qgmpeAXMr3sY41EsclVqRfpnPNU+T/KGIF1u1j9DDbQtUsY89z5MMI9mt13ymkP275Ic0z1tpjPM1KTtm4WZC8QhUO8xuQSD66jdWyQw4CjHro6kzkS6koCeTmCIfoRMpyXBgFeAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('77a61b2fc6697bbfbad2f15ebf0eac0b')

# 建立資料庫
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            amount INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    if user_message.startswith("記帳"):
        try:
            amount = int(user_message.split(" ")[1].replace("元", ""))
            date = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect('expenses.db')
            c = conn.cursor()
            c.execute('INSERT INTO expenses (amount, date) VALUES (?, ?)', (amount, date))
            conn.commit()
            conn.close()
            reply_message = TextSendMessage(text=f"已記錄 {amount} 元")
        except:
            reply_message = TextSendMessage(text="記帳格式錯誤，請使用「記帳 xxx 元」格式")
    elif user_message == "查詢 當日":
        date = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT SUM(amount) FROM expenses WHERE date = ?', (date,))
        result = c.fetchone()[0]
        conn.close()
        result = result if result else 0
        reply_message = TextSendMessage(text=f"當日花費總額為 {result} 元")
    elif user_message == "查詢 當月":
        month = datetime.now().strftime("%Y-%m")
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT SUM(amount) FROM expenses WHERE date LIKE ?', (month + '%',))
        result = c.fetchone()[0]
        conn.close()
        result = result if result else 0
        reply_message = TextSendMessage(text=f"當月花費總額為 {result} 元")
    else:
        reply_message = TextSendMessage(text="未知指令，請使用「記帳 xxx 元」、「查詢 當日」或「查詢 當月」")

    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
