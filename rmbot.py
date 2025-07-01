# File: rmbot.py
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from reminder_parser import parse_input
from db import ReminderDB

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я ваш Telegram-напоминатор. Напишите мне, например:"
        "\n🔹 напомни завтра в 18:00 позвонить"
        "\n🔹 через 5 минут сделать растяжку"
        "\n🔹 каждый день в 9:00 медитировать",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    try:
        text, slots, rpt, interval = parse_input(raw)
    except ValueError as e:
        return await update.message.reply_text(str(e))

    db: ReminderDB = context.bot_data['db']
    db.add_reminders(update.effective_chat.id, text, slots, rpt, interval)

    resp = f"✅ Запланировано: «{text}»"
    for dt in slots:
        resp += f"\n  – {dt.strftime('%Y-%m-%d %H:%M:%S')}"
    if rpt:
        resp += f"\n(повтор: {rpt} каждые {interval})"
    await update.message.reply_text(resp)

async def check_and_send(context: ContextTypes.DEFAULT_TYPE):
    db: ReminderDB = context.bot_data['db']
    due = db.get_due()
    for rid, chat_id, text, remind_at, rpt, interval in due:
        await context.bot.send_message(chat_id, f"🔔 Напоминание: {text}")
        base = datetime.fromisoformat(remind_at)
        if rpt:
            next_dt = base + relativedelta(**{
                'daily':   {'days': interval},
                'weekly':  {'weeks': interval},
                'monthly': {'months': interval},
                'yearly':  {'years': interval},
                'days':    {'days': interval},
            }[rpt])
            db.update_reminder(rid, next_dt)
        else:
            db.mark_done(rid)

if __name__ == '__main__':
    if not TOKEN:
        print('❌ BOT_TOKEN не установлен')
        exit(1)
    db = ReminderDB()
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data['db'] = db
    app.job_queue.run_repeating(check_and_send, interval=60, first=10)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print('✅ Бот запущен и готов к работе...')
    app.run_polling()
