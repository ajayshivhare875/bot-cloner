"""Weather Bot Template - live weather via Open-Meteo (no API key)."""
INFO = {"name": "Weather Bot", "emoji": "🌤️", "description": "Live weather for any city"}

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
def run(token):
    async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text("🌤️ Weather Bot\n\n/weather Delhi\n/weather Mumbai")
    async def weather(u: Update, c: ContextTypes.DEFAULT_TYPE):
        city = u.message.text[len("/weather"):].strip()
        if not city:
            await u.message.reply_text("❌ /weather <city>")
            return
        import requests
        try:
            g = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=10).json()
            if not g.get("results"):
                await u.message.reply_text("❌ City not found!")
                return
            lat, lon = g["results"][0]["latitude"], g["results"][0]["longitude"]
            name = g["results"][0]["name"]
            w = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m", timeout=10).json()["current"]
            await u.message.reply_text(f"🌤️ {name}\n🌡️ {w['temperature_2m']}°C\n💨 Wind: {w['wind_speed_10m']} km/h")
        except Exception:
            await u.message.reply_text("⚠️ Failed to fetch weather.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("weather", weather))
    app.run_polling()
