import os,json,time,threading,requests,telebot

bot=telebot.TeleBot(os.environ.get('TELEGRAM_TOKEN'))
HEADERS={'Authorization':'Bearer '+os.environ.get('BS_API_TOKEN','')}
API='https://api.brawlstars.com/v1'
players={}


def api(tag):
    r=requests.get(f"{API}/players/%23{tag.replace('#','')}",headers=HEADERS,timeout=15)
    return r.status_code,r.text


def get(tag):
    s,t=api(tag)
    if s==200:return json.loads(t)
    return None

@bot.message_handler(commands=['track'])
def track(m):
    a=m.text.split()
    if len(a)<2:return
    tag=a[1].upper()
    if not tag.startswith('#'):tag='#'+tag
    p=get(tag)
    if not p:
        s,t=api(tag);bot.reply_to(m,f'🛠 API DEBUG\nSTATUS: {s}\n{t[:800]}');return
    players[tag]={'chat':m.chat.id,'b':{x['name']:x['trophies'] for x in p['brawlers']}}
    bot.reply_to(m,'✅ Отслеживание включено '+tag)

@bot.message_handler(commands=['status'])
def status(m):bot.reply_to(m,'\n'.join(players) if players else 'Пусто')


def loop():
    while True:
        for tag,d in list(players.items()):
            p=get(tag)
            if not p: continue
            now={x['name']:x['trophies'] for x in p['brawlers']}
            for n,v in now.items():
                if n in d['b'] and d['b'][n]!=v:
                    old=d['b'][n];bot.send_message(d['chat'],f"{'📈' if v>old else '📉'} {n}\n{old} → {v}\n({v-old:+})")
            d['b']=now
        time.sleep(60)

threading.Thread(target=loop,daemon=True).start()
bot.infinity_polling()
