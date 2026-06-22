import telebot
import requests
import time
import json
import os
from datetime import datetime

# ========== КОНФИГ ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "7876393156:AAFf2bNwTdyDNrM3AMuV2Q1OihAsOBC2Qww")
BS_API_TOKEN = os.environ.get("BS_API_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjEwZTc2NzEzLTNlMWItNDNkOS1hMDVjLWVjYTdjZjZhOGU4MCIsImlhdCI6MTc4MjEzMDA1Niwic3ViIjoiZGV2ZWxvcGVyL2E5MWJlODBkLWI2ODktM2MzNS1hNzUzLTdlOWMwMGFjMWE2NyIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiNDUuODIuMTIwLjEzNSJdLCJ0eXBlIjoiY2xpZW50In1dfQ._rHRkL7G42T7pJc69WdY8dWSlLdU70HAI75DF5fhpwAXV8EGq6wFaDt--7WsmVi3aKy8r9kALThBImleNYKAmA")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== ХРАНИЛИЩЕ ==========
# { player_tag: { "group_id": ..., "last_battle": ... } }
tracked_players = {}

# ========== BRAWL STARS API ==========
HEADERS = {"Authorization": f"Bearer {BS_API_TOKEN}"}
BS_API = "https://api.brawlstars.com/v1"

def get_battle_log(tag: str):
    tag_encoded = tag.replace("#", "%23")
    url = f"{BS_API}/players/{tag_encoded}/battlelog"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("items", [])
    except Exception as e:
        print(f"Ошибка API: {e}")
    return None

def get_result_emoji(result: str) -> str:
    if result == "victory":
        return "✅ Победа"
    elif result == "defeat":
        return "❌ Поражение"
    elif result == "draw":
        return "🤝 Ничья"
    return "❓ Неизвестно"

def format_battle_message(battle: dict, player_tag: str) -> str:
    b = battle.get("battle", {})
    event = battle.get("event", {})

    mode = b.get("mode", "?")
    result = b.get("result", "?")
    trophy_change = b.get("trophyChange", 0)
    map_name = event.get("map", "Неизвестная карта")

    # Найти бравлера игрока
    brawler_name = "?"
    teams = b.get("teams", [])
    solo_players = b.get("players", [])

    all_players = []
    for team in teams:
        all_players.extend(team)
    all_players.extend(solo_players)

    for p in all_players:
        p_tag = p.get("tag", "").replace("#", "")
        my_tag = player_tag.replace("#", "")
        if p_tag.upper() == my_tag.upper():
            brawler_name = p.get("brawler", {}).get("name", "?")
            break

    # Иконки режимов
    mode_icons = {
        "gemGrab": "💎 Кража самоцветов",
        "brawlBall": "⚽ Бравлбол",
        "bounty": "⭐ Охота за звёздами",
        "heist": "💰 Налёт",
        "siege": "🏰 Осада",
        "hotZone": "🔥 Горячая зона",
        "knockout": "🥊 Нокаут",
        "duels": "⚔️ Дуэли",
        "soloShowdown": "💀 Бой до последнего (соло)",
        "duoShowdown": "👥 Бой до последнего (дуо)",
        "wipeout": "💥 Уничтожение",
        "payload": "🚂 Груз",
        "basketBrawl": "🏀 Баскетбол",
        "superCity": "🏙️ Мегаполис",
        "present": "🎁 Подарки",
        "roboRumble": "🤖 Восстание роботов",
        "bigGame": "🦈 Большая рыбалка",
        "hunters": "🎯 Охотники",
    }
    mode_text = mode_icons.get(mode, f"🎮 {mode}")

    # Трофеи
    if trophy_change > 0:
        trophy_text = f"📈 +{trophy_change} трофеев"
    elif trophy_change < 0:
        trophy_text = f"📉 {trophy_change} трофеев"
    else:
        trophy_text = "➖ 0 трофеев"

    time_str = datetime.now().strftime("%H:%M | %d.%m.%Y")

    msg = (
        f"🎮 <b>Новый матч!</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🗺 <b>Карта:</b> {map_name}\n"
        f"{mode_text}\n"
        f"🦊 <b>Бравлер:</b> {brawler_name}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{get_result_emoji(result)}\n"
        f"{trophy_text}\n"
        f"━━━━━━━━━━━━━━\n"
        f"⏱ {time_str}"
    )
    return msg

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    bot.reply_to(message, (
        "👋 <b>Brawl Tracker Bot</b>\n\n"
        "Команды:\n"
        "/track #TAG — начать отслеживание игрока\n"
        "/stop #TAG — остановить отслеживание\n"
        "/status — показать кого отслеживаем\n\n"
        "💡 Добавь бота в группу и используй /track там!"
    ), parse_mode="HTML")

@bot.message_handler(commands=["track"])
def cmd_track(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Укажи тег игрока!\nПример: /track #ABC123")
        return

    tag = parts[1].upper()
    if not tag.startswith("#"):
        tag = "#" + tag

    # Проверяем что игрок существует
    battles = get_battle_log(tag)
    if battles is None:
        bot.reply_to(message, f"❌ Не удалось найти игрока с тегом {tag}\nПроверь тег и попробуй снова.")
        return

    group_id = message.chat.id
    last_battle_time = battles[0].get("battleTime", "") if battles else ""

    tracked_players[tag] = {
        "group_id": group_id,
        "last_battle": last_battle_time
    }

    bot.reply_to(message, (
        f"✅ Начинаю отслеживать <b>{tag}</b>!\n"
        f"Буду присылать результаты матчей сюда 🎮"
    ), parse_mode="HTML")
    print(f"[+] Tracking {tag} → chat {group_id}")

@bot.message_handler(commands=["stop"])
def cmd_stop(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Укажи тег!\nПример: /stop #ABC123")
        return

    tag = parts[1].upper()
    if not tag.startswith("#"):
        tag = "#" + tag

    if tag in tracked_players:
        del tracked_players[tag]
        bot.reply_to(message, f"🛑 Отслеживание <b>{tag}</b> остановлено.", parse_mode="HTML")
    else:
        bot.reply_to(message, f"❓ Тег {tag} не отслеживается.")

@bot.message_handler(commands=["status"])
def cmd_status(message):
    if not tracked_players:
        bot.reply_to(message, "📭 Никто не отслеживается.\nИспользуй /track #TAG")
        return

    lines = ["📋 <b>Отслеживаемые игроки:</b>\n"]
    for tag, data in tracked_players.items():
        lines.append(f"• {tag} → чат {data['group_id']}")

    bot.reply_to(message, "\n".join(lines), parse_mode="HTML")

# ========== ФОНОВЫЙ ТРЕКЕР ==========

def check_battles():
    """Проверяет новые матчи каждые 60 секунд"""
    print("[*] Трекер запущен")
    while True:
        for tag, data in list(tracked_players.items()):
            try:
                battles = get_battle_log(tag)
                if not battles:
                    continue

                latest = battles[0]
                latest_time = latest.get("battleTime", "")

                if latest_time != data["last_battle"]:
                    # Новый матч!
                    tracked_players[tag]["last_battle"] = latest_time
                    msg = format_battle_message(latest, tag)
                    bot.send_message(data["group_id"], msg, parse_mode="HTML")
                    print(f"[✓] Новый матч для {tag}")

            except Exception as e:
                print(f"[!] Ошибка для {tag}: {e}")

        time.sleep(60)  # Проверка каждую минуту

@bot.message_handler(commands=["myip"])
def cmd_myip(message):
    try:
        ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
        bot.reply_to(message, f"🌐 IP сервера: <code>{ip}</code>\n\nДобавь этот IP в Brawl Stars API!", parse_mode="HTML")
    except:
        bot.reply_to(message, "❌ Не удалось получить IP")

def send_server_ip():
    """Отправляет IP сервера владельцу при старте"""
    try:
        time.sleep(3)
        ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
        # Берём chat_id из первого отслеживаемого или пропускаем
        print(f"[*] IP сервера: {ip}")
    except Exception as e:
        print(f"[!] Не удалось получить IP: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    import threading

    print("[*] Бот запускается...")

    # Узнаём IP
    ip_thread = threading.Thread(target=send_server_ip, daemon=True)
    ip_thread.start()

    # Запускаем трекер в отдельном потоке
    tracker_thread = threading.Thread(target=check_battles, daemon=True)
    tracker_thread.start()

    # Запускаем бота
    print("[*] Polling...")
    bot.infinity_polling()
