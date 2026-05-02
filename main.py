import discord
import requests
import asyncio
from pathlib import Path
from datetime import datetime

#* Botのトークンを.envファイルから取得
def load_env():
    env = {}
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        raise RuntimeError(".env が見つかりません。main.py と同じフォルダに .env を作成してください")
    with env_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env

env = load_env()
TOKEN = env.get("DISCORD_BOT_TOKEN")  # .envファイルにDISCORD_BOT_TOKEN=あなたのトークンと記載しておく
if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN が .env に設定されていません")

CHANNEL_ID = 1494984310518972498  # 送信したいチャンネルID

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

last_event_id = None  # 重複送信防止

#* ISO8601形式の日時をdatetimeオブジェクトに変換
def parse_quake_time(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (OSError, ValueError, OverflowError):
            return None
    if isinstance(value, str):
        if value.isdigit():
            try:
                return datetime.fromtimestamp(int(value))
            except (OSError, ValueError, OverflowError):
                return None
        try:
            if value.endswith("Z"):
                value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                return None
    return None

#* 地震情報をDiscordメッセージ用に整形
def build_quake_message(quake):
    place = quake["earthquake"]["hypocenter"]["name"]
    magnitude = quake["earthquake"]["hypocenter"]["magnitude"]
    max_scale = quake["earthquake"]["maxScale"] // 10  # 震度は10倍されているので元に戻す
    occurred_at = parse_quake_time(quake["earthquake"]["time"])
    if occurred_at:
        header = f"**地震発生 (<t:{int(occurred_at.timestamp())}:R>)**"
    else:
        header = "**地震発生**"
    return f"{header} \n震源地: {place}\nマグニチュード: {magnitude}\n最大震度: {max_scale}"

#* 地震情報をチェック&送信（5秒毎)
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

                    # 長野県を含むか判定
                    if "長野" in place:
                        msg = build_quake_message(quake)
                        await channel.send(msg)
                    
                    # msg = f"地震発生 \n震源地: {place}\nマグニチュード: {magnitude}\n最大震度: {max_scale}"
                    # await channel.send(msg)

        except Exception as e:
            print(e)

        await asyncio.sleep(5)  # 5秒ごとにチェック



# *ボット起動
@client.event
async def on_ready():
    print(f"ログイン成功: {client.user}")
    client.loop.create_task(check_earthquake())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.strip() == "!debug":
        await message.channel.send("デバッグ: コマンドを受信しました")
    if message.content.strip() == "!quake":
        try:
            url = "https://api.p2pquake.net/v2/history?codes=551&limit=1"
            res = requests.get(url).json()
            if res:
                msg = build_quake_message(res[0])
                await message.channel.send(msg)
            else:
                await message.channel.send("地震情報が取得できませんでした")
        except Exception as e:
            print(e)
            await message.channel.send("地震情報の取得に失敗しました")

client.run(TOKEN)