import telebot
import threading
import time
import json
import os
import requests

# =================== НАСТРОЙКИ ===================
BOT_TOKEN = "7876393156:AAH2IeCNjMUGszgtQ9dYZOnyaJxRyLAlG1U"  # замени после revoke
PLAYER_TAG = "#QJYUYQ8GY"
CHAT_ID = "7960700753"
CHECK_INTERVAL = 120
STATE_FILE = "last_battle.json"
# =================================================

API_BASE = "https://api.brawlapi.com/v1"
bot = telebot.TeleBot(BOT_TOKEN)

def load_last_battle():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None

def save_last_battle(battle):
    with open(STATE_FILE, "w") as f:
        json.dump(battle, f)

def get_battle_log(tag):
    encoded = tag.replace("#", "%23")
    url = f"{API_BASE}/players/{encoded}/battlelog"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []

def get_player(tag):
    encoded = tag.replace("#", "%23")
    url = f"{API_BASE}/players/{encoded}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return None

def format_battle(battle, player_tag):
    try:
        event = battle.get("event", {})
        mode = event.get("mode", "Unknown")
        map_name = event.get("map", "Unknown")

        result = battle.get("battle", {})
        outcome = result.get("result", "?")
        trophy_change = result.get("trophyChange", 0)

        brawler_name = "?"
        teams = result.get("teams", [])
        for team in teams:
            for player in team:
                if player.get("tag", "").upper() == player_tag.upper():
                    brawler = player.get("brawler", {})
                    brawler_name = brawler.get("name", "?")
                    break

        emoji = "✅" if outcome == "victory" else "❌" if outcome == "defeat" else "🤝"
        trophy_str = f"+{trophy_change}" if trophy_change > 0 else str(trophy_change)

        return (
            f"{emoji} <b>{outcome.upper()}</b>\n"
            f"🗺 {mode} — {map_name}\n"
            f"🥊 Бравлер: {brawler_name}\n"
            f"🏆 Трофеи: {trophy_str}"
        )
    except Exception as e:
        return f"Новый матч (ошибка парсинга: {e})"

def check_battles():
    while True:
        try:
            battles = get_battle_log(PLAYER_TAG)
            if battles:
                latest = battles[0]
                battle_time = latest.get("battleTime", "")
                last = load_last_battle()
                last_time = last.get("time") if last else None
                if battle_time != last_time:
                    save_last_battle({"time": battle_time})
                    text = format_battle(latest, PLAYER_TAG)
                    bot.send_message(CHAT_ID, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка проверки: {e}")
        time.sleep(CHECK_INTERVAL)

@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    player = get_player(PLAYER_TAG)
    if not player:
        bot.reply_to(message, "Не удалось получить данные.")
        return
    name = player.get("name", "?")
    trophies = player.get("trophies", 0)
    highest = player.get("highestTrophies", 0)
    club = player.get("club", {}).get("name", "Нет клуба")
    text = (
        f"👤 <b>{name}</b>\n"
        f"🏆 Трофеев: {trophies} (макс: {highest})\n"
        f"🤝 Клуб: {club}"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# Запуск проверки в фоне
t = threading.Thread(target=check_battles, daemon=True)
t.start()

print("Бот запущен!")
bot.polling(none_stop=True)
