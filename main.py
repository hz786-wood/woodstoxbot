import os
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from notion_client import Client as NotionClient
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Notion setup
notion = NotionClient(auth=NOTION_TOKEN)

# Flask app
app = Flask(__name__)

# Telegram app setup
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Notion search function
def fetch_stock(query_text):
    response = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
            "filter": {
                "property": "Size",
                "rich_text": {
                    "contains": query_text
                }
            }
        }
    )
    results = []
    for row in response.get("results", []):
        props = row["properties"]
        size = props.get("Size", {}).get("title", [{}])[0].get("text", {}).get("content", "")
        nos = props.get("Nos", {}).get("number", 0)
        cft = props.get("CFT", {}).get("number", 0.0)
        results.append(f"📦 {size}: {nos} pcs | {cft} CFT")
    return "\n".join(results) if results else "❌ No matching size found."

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    result = fetch_stock(user_message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# Webhook route
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "✅ Webhook is active!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

