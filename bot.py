import telebot
import requests
import time
import json
import os
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "PUT_TOKEN_HERE")
BS_API_TOKEN = os.environ.get("BS_API_TOKEN", "PUT_API_TOKEN_HERE")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

HEADERS = {"Authorization": f"Bearer {BS_API_TOKEN}"}
BS_API = "https://api.brawlstars.com/v1"

DATA_FILE = "players.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tracked_players, f, ensure_ascii=False, indent=2)

tracked_players = load_data()

def get_player(tag):
    tag_encoded = tag.replace("#", "%23")
    url = f"{BS_API}/players/{tag_encoded}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code == 200:
            return r.json()

    except Exception as e:
        print(e)

    return None

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "/track #TAG\n"
        "/stop #TAG\n"
        "/status"
    )

@bot.message_handler(commands=["track"])
def track(message):
    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Используй: /track #TAG")
        return

    tag = parts[1].upper()

    if not tag.startswith("#"):
        tag = "#" + tag

    player = get_player(tag)

    if not player:
        bot.reply_to(message, "Игрок не найден")
        return

    brawlers = {}

    for b in player.get("brawlers", []):
        brawlers[b["name"]] = b["trophies"]

    tracked_players[tag] = {
        "group_id": message.chat.id,
        "name": player.get("name", tag),
        "brawlers": brawlers
    }

    save_data()

    bot.reply_to(
        message,
        f"✅ Отслеживание включено\n{player.get('name')} ({tag})"
    )

@bot.message_handler(commands=["stop"])
def stop(message):
    parts = message.text.split()

    if len(parts) < 2:
        return

    tag = parts[1].upper()

    if not tag.startswith("#"):
        tag = "#" + tag

    if tag in tracked_players:
        del tracked_players[tag]
        save_data()
        bot.reply_to(message, "🛑 Удалено")

@bot.message_handler(commands=["status"])
def status(message):
    if not tracked_players:
        bot.reply_to(message, "Пусто")
        return

    text = "📋 Отслеживаемые игроки:\n\n"

    for tag, data in tracked_players.items():
        text += f"{data['name']} {tag}\n"

    bot.reply_to(message, text)

def tracker():
    while True:

        for tag in list(tracked_players.keys()):

            try:
                data = tracked_players[tag]

                player = get_player(tag)

                if not player:
                    continue

                current = {}

                for b in player.get("brawlers", []):
                    current[b["name"]] = b["trophies"]

                old = data["brawlers"]

                for name, new_trophies in current.items():

                    old_trophies = old.get(name)

                    if old_trophies is None:
                        continue

                    if old_trophies != new_trophies:

                        diff = new_trophies - old_trophies

                        if diff > 0:
                            msg = (
                                f"📈 {name}\n"
                                f"{old_trophies} → {new_trophies}\n"
                                f"(+{diff})"
                            )
                        else:
                            msg = (
                                f"📉 {name}\n"
                                f"{old_trophies} → {new_trophies}\n"
                                f"({diff})"
                            )

                        bot.send_message(
                            data["group_id"],
                            msg
                        )

                tracked_players[tag]["brawlers"] = current

                save_data()

            except Exception as e:
                print(e)

        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=tracker, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
