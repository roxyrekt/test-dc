import os
import asyncio
import websockets
from discord_webhook import DiscordWebhook, DiscordEmbed
from keep_alive import keep_alive
import json
import time
import sys

keep_alive()

webhookurl = os.environ['discord_webhook']
ping = "@everyone"

webhook = DiscordWebhook(url=webhookurl, content=f"{ping}")

balance_value = 0
rain_bitis = 0

async def on_message(websocket, message):
    global balance_value
    global o_anki_cevrimici

    if message == "2":
        await websocket.send("3")
    try:
        # Özel formattaki veriyi düzenle
        formatted_data = message[2:].replace("'", '"').replace("][", '],[')

        # '[' ve ']' karakterlerini sil
        translation_table = str.maketrans("", "", "[]")
        formatted_data = formatted_data.translate(translation_table)

        print(f"Formatted Data: {formatted_data}")

        # JSON formatına uygun hale getir
        json_data = json.loads(f'[{formatted_data}]')

        await websocket.send('420["rain:join",{}]')

        if json_data and isinstance(json_data, list) and len(json_data) > 0:
          # İlk öğe "rain:balance" mi kontrol et
            if json_data[0] == "rain:balance":
              balance_value = int(json_data[1])

        if json_data and isinstance(json_data, list) and len(json_data) > 0:
          # İlk öğe "rain:balance" mi kontrol et
            if json_data[0] == "online-users":
              o_anki_cevrimici = int(json_data[1])

        # JSON formatında bir liste var mı ve en az bir öğe içeriyor mu kontrol et
        if isinstance(json_data, list) and len(json_data) > 0:
            # İlk öğe "rain:balance" mi kontrol et
            if json_data[0] == "rain:state" and json_data[1] == "IN_PROGRESS":
                gercek_miktar = (balance_value / 100)
                print(f"Rain balance: {gercek_miktar}")

                timestamp = int(time.time()) + 180
                embed = DiscordEmbed(title=f"RustMagic Rain", url="https://rustmagic.com", color=0xFF0000)
                embed.add_embed_field(name="Rain Amount", value=f"{gercek_miktar} $")
                embed.add_embed_field(name="Online Users", value=f"{o_anki_cevrimici}")
                embed.add_embed_field(name="Expiration", value=f"<t:{timestamp}:R>")
                embed.set_timestamp()
                embed.set_thumbnail(url="https://rustmagic.com/_next/image?url=%2Fimg%2Flogo.png&w=256&q=75")
                webhook.add_embed(embed)
                webhook.execute()
                webhook.remove_embed(0)
        else:
            # JSON formatında değilse veya boşsa gelen veriyi string olarak yazdır
            print(f"Gelen veri: {formatted_data}")

        # Diğer kodlar...
    except json.JSONDecodeError as e:
        print(f"Hata oluştu: {e}")
        print(f"Gelen veri JSON formatında değil: {message}")
        print("Hata Aldığı JSON:", formatted_data)
        if "no close frame received or sent" in str(e):
            restart_program()


async def on_error(error):
    print(f"Hata oluştu: {error}")
    if "no close frame received or sent" in str(error):
        restart_program()


async def connect_websocket():
    uri = "wss://api.rustmagic.com/socket.io/?token=&EIO=4&transport=websocket"  # WebSocket URL'si

    async with websockets.connect(uri) as websocket:
        await websocket.send("40/,{}")
        print("Bağlantı kuruldu")

        try:
            while True:
                message = await websocket.recv()
                await on_message(websocket, message)
        except websockets.exceptions.ConnectionClosedError as e:
            await on_error(e)


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


asyncio.get_event_loop().run_until_complete(connect_websocket())
