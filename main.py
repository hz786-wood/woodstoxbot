import openai
from notion_client import Client as NotionClient
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio

# Load environment variables
load_dotenv()
@@ -46,15 +47,20 @@ def fetch_stock(query_text):
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

    def handle_message(update, context):
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        result = fetch_stock(user_message)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.process_update(update)
    async def process_update():
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        await application.initialize()
        await application.process_update(update)
        await application.shutdown()

    asyncio.run(process_update())
    return "ok"

# Home route
@@ -65,3 +71,5 @@ def index():
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
