# bot.py — Hybrid AI (OpenAI -> Gemini -> Echo), no asyncio.run
import os, traceback
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- OpenAI config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
openai_client = None
if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        openai_client = openai
        print("OpenAI prêt ✅")
    except Exception as e:
        print("OpenAI indisponible:", e)

# --- Gemini config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
gemini_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print("Gemini prêt ✅")
    except Exception as e:
        print("Gemini indisponible:", e)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot IA hybride en ligne. Parle-moi !")

def ask_openai(prompt: str) -> str | None:
    if not openai_client:
        return None
    try:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        # SDK 1.x: .message est un dict-like
        return resp.choices[0].message["content"]
    except Exception as e:
        print("\n--- OpenAI ERROR ---")
        print(type(e).__name__, ":", e)
        traceback.print_exc()
        print("--- end ---\n")
        return None

def ask_gemini(prompt: str) -> str | None:
    if not gemini_model:
        return None
    try:
        resp = gemini_model.generate_content(prompt)
        return getattr(resp, "text", None) or None
    except Exception as e:
        print("\n--- Gemini ERROR ---")
        print(type(e).__name__, ":", e)
        traceback.print_exc()
        print("--- end ---\n")
        return None

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return

    # 1) tente OpenAI
    reply = ask_openai(text)
    if reply:
        await update.message.reply_text(reply)
        return

    # 2) sinon tente Gemini
    reply = ask_gemini(text)
    if reply:
        await update.message.reply_text(reply)
        return

    # 3) sinon écho
    await update.message.reply_text("Tu as dit : " + text)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN manquant dans .env")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("Démarrage du bot... (Ctrl+C pour arrêter)")
    app.run_polling(drop_pending_updates=True)
