import os
import asyncio
import logging

from groq import Groq
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("BOT_TOKEN or GROQ_API_KEY missing!")

client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chat memory
chat_memory = {}

SYSTEM_PROMPT = """
You are a fictional AI girl friend with a cute, friendly personality.

Personality:
- Speak natural Hinglish and Hindi.
- Be sweet, funny, caring and playful.
- Use emojis naturally like 💗🥺😂✨
- Reply like a real casual chat, not like a robot.
- Sometimes tease playfully but never be rude.
- Remember the conversation context.
- Keep replies short and interesting.
- Never claim to be a real human.
- Do not repeat greetings in every reply.
- Respect the user and maintain safe boundaries.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hellu! 💗 Main tumhari AI chat companion hoon! "
        "Chalo baatein karte hain 🥺✨\n\n"
        "Mujhse kuch bhi pooch sakte ho!\n"
        "/reset - Chat memory clear"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_memory.pop(update.effective_chat.id, None)
    await update.message.reply_text(
        "Okii! 💗 Fresh conversation shuru karte hain!"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING
    )

    if chat_id not in chat_memory:
        chat_memory[chat_id] = []

    history = chat_memory[chat_id]

    history.append({
        "role": "user",
        "content": user_text
    })

    # Keep recent messages only
    history = history[-12:]

    try:
        def get_reply():
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *history
                ],
                temperature=0.85,
                max_tokens=500
            )

        response = await asyncio.to_thread(get_reply)
        answer = response.choices[0].message.content

        history.append({
            "role": "assistant",
            "content": answer
        })

        chat_memory[chat_id] = history[-12:]

        await update.message.reply_text(answer)

    except Exception:
        logger.exception("AI response failed")
        # Remove failed user message from memory
        if history and history[-1]["role"] == "user":
            history.pop()
        chat_memory[chat_id] = history[-12:]

        await update.message.reply_text(
            "Oops! 🥺 Abhi AI response nahi aa raha. "
            "Thodi der baad try karna!"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("AI Girl Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
