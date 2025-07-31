import os
from dotenv import load_dotenv
from flask import Flask, request
import openai
from notion_client import Client as NotionClient
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# Initialize clients
openai.api_key = OPENAI_API_KEY
notion = NotionClient(auth=NOTION_TOKEN)
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

# Fetch data from Notion stocklist
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

# Handle Telegram webhook
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

    def handle_message(update, context):
        user_message = update.message.text
        result = fetch_stock(user_message)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.process_update(update)
    return "ok"

# Home route
@app.route("/", methods=["GET"])
def index():
    return "✅ WoodStox Bot is live!"

