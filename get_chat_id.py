from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8695719013:AAGXwWXiyi1FkG5_y5aj4n1d1W7LT5wcoIo"

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    print(f"Chat name : {chat.title or chat.full_name}")
    print(f"Chat ID   : {chat.id}")
    print(f"Chat type : {chat.type}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle))
print("Listening... send any message in your group then press Ctrl+C")
app.run_polling()
