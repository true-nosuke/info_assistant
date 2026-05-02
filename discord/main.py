import discord
import requests
import asyncio

# Botのトークンを.envファイルから取得
def load_env():
    env = {}
    with open(".env", "r") as f:
        for line in f:
            key, value = line.strip().split("=", 1)
            env[key] = value
    return env

env = load_env()
TOKEN = env.get("DISCORD_BOT_TOKEN")  # .envファイルにDISCORD_BOT_TOKEN=あなたのトークンと記載しておく

CHANNEL_ID = 123456789012345678  # 送信したいチャンネルID

intents = discord.Intents.default()
client = discord.Client(intents=intents)

last_event_id = None  # 重複送信防止

async def check_earthquake():
    global last_event_id
    await client.wait_until_ready()

    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            url = "https://api.p2pquake.net/v2/history?codes=551&limit=1"
            res = requests.get(url).json()

            if res:
                quake = res[0]
                event_id = quake["id"]

                if event_id != last_event_id:
                    last_event_id = event_id

                    place = quake["earthquake"]["hypocenter"]["name"]
                    magnitude = quake["earthquake"]["hypocenter"]["magnitude"]
                    max_scale = quake["earthquake"]["maxScale"]

                    # 長野県を含むか判定
                    if "長野" in place:
                        msg = f"⚠️ 地震発生！\n震源地: {place}\nマグニチュード: {magnitude}\n最大震度: {max_scale}"
                        await channel.send(msg)

        except Exception as e:
            print(e)

        await asyncio.sleep(10)  # 10秒ごとにチェック

@client.event
async def on_ready():
    print(f"ログイン成功: {client.user}")
    client.loop.create_task(check_earthquake())

client.run(TOKEN)