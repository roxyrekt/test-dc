import capsolver
import os
import asyncio
import websockets
import json
import sys
import requests
import time
from keep_alive import keep_alive

keep_alive()

authtoken = os.environ["authtoken"]
useragent = os.environ["useragent"]
api_key = os.environ["captchakey"]

capsolver.api_key = api_key

url_get_balance = "https://api.capsolver.com/getBalance"
url_create_task = "https://api.capsolver.com/createTask"
url_get_task_result = "https://api.capsolver.com/getTaskResult"
url_solve_captcha = "https://api.capsolver.com/solveCaptcha"

getbalance = capsolver.balance()
print(f"Capsolver bakiye: {getbalance.get('balance')}")

async def on_message(websocket, message):
    global balance_value

    if message == "2":
        await websocket.send("3")
    try:
        # Özel formattaki veriyi düzenle
        formatted_data = message[2:].replace("'", '"').replace("][", '],[')

        # '[' ve ']' karakterlerini sil
        translation_table = str.maketrans("", "", "[]")
        formatted_data = formatted_data.translate(translation_table)

        # JSON formatına uygun hale getir
        json_data = json.loads(f'[{formatted_data}]')

        await websocket.send('420["rain:join",{}]')

        if json_data and isinstance(json_data, list) and len(json_data) > 0:
            # İlk öğe "rain:balance" mi kontrol et
            if json_data[0] == "rain:balance":
                balance_value = int(json_data[1])

        # JSON formatında bir liste var mı ve en az bir öğe içeriyor mu kontrol et
        if isinstance(json_data, list) and len(json_data) > 0:
            # İlk öğe "rain:state" mi kontrol et
            if json_data[0] == "rain:state" and json_data[1] == "IN_PROGRESS":
                gercek_miktar = (balance_value / 100)
                print(f"Rain balance: {gercek_miktar}")
                print("Joining rain")

                # Capsolver'a HCaptcha çözme isteği gönder
                create_hcaptcha_task_data = {
                    "clientKey": api_key,
                    "task": {
                        "type": "HCaptchaTaskProxyLess",
                        "websiteURL": "https://rustmagic.com",
                        "websiteKey": "2ba97fee-64b6-44ae-b476-058b5802ec03",
                        "userAgent": useragent
                    }
                }

                create_hcaptcha_task_response = requests.post(url_create_task, json=create_hcaptcha_task_data)

                if create_hcaptcha_task_response.status_code == 200:
                    print("HCaptcha görevi başarıyla oluşturuldu.")
                    hcaptcha_task_id = create_hcaptcha_task_response.json()["taskId"]
                    print("Görev ID:", hcaptcha_task_id)

                    # Görev durumunu sorgulama döngüsü
                    while True:
                        get_task_result_data = {
                            "clientKey": api_key,
                            "taskId": hcaptcha_task_id
                        }

                        get_task_result_response = requests.post(url_get_task_result, json=get_task_result_data)

                        if get_task_result_response.status_code == 200:
                            status_data = get_task_result_response.json()
                            print("Görev durumu:", status_data["status"])

                            if status_data["status"] == "ready":
                                # HCaptcha görevi tamamlandı, başka işlemler yapabilirsiniz
                                hcaptcha_solution = status_data["solution"]["gRecaptchaResponse"]
                                print("HCaptcha Çözüm:", hcaptcha_solution)

                                # RustMagic'e katılım için POST isteği
                                url_rustmagic = 'https://api.rustmagic.com/api/rain/join'
                                headers_rustmagic = {
                                    'authority': 'api.rustmagic.com',
                                    'accept': 'application/json, text/plain, */*',
                                    'accept-language': 'tr-TR,tr;q=0.7',
                                    'authorization': authtoken,
                                    'content-type': 'application/json',
                                    'dnt': '1',
                                    'origin': 'https://rustmagic.com',
                                    'referer': 'https://rustmagic.com/',
                                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
                                    'sec-ch-ua-mobile': '?0',
                                    'sec-ch-ua-platform': '"Windows"',
                                    'sec-fetch-dest': 'empty',
                                    'sec-fetch-mode': 'cors',
                                    'sec-fetch-site': 'same-site',
                                    'sec-gpc': '1',
                                    'user-agent': useragent
                                }

                                data_rustmagic = {
                                    'token': hcaptcha_solution
                                }

                                # POST isteği gönder
                                response_rustmagic = requests.post(url_rustmagic, headers=headers_rustmagic, json=data_rustmagic)

                                print(response_rustmagic.json()['message'])
                                getbalance = capsolver.balance()
                                print(f"Capsolver bakiye: {getbalance.get('balance')}")
                                break
                            elif status_data["status"] == "error":
                                # Görevde bir hata oluştu
                                print("Hata:", status_data["errorDescription"])
                                break
                        else:
                            print("Durum sorgulama başarısız oldu. HTTP Hata Kodu:", get_task_result_response.status_code)
                            break

                        time.sleep(5)  # 5 saniye bekleme süresi (isteğe bağlı)

                else:
                    print("HCaptcha görevi oluşturma başarısız oldu. HTTP Hata Kodu:", create_hcaptcha_task_response.status_code)
                    print("Hata mesajı:", create_hcaptcha_task_response.text)

    except json.JSONDecodeError as e:
        if "no close frame received or sent" in str(e):
            restart_program()

async def on_error(error):
    print(f"Hata oluştu: {error}")
    if "no close frame received or sent" in str(error):
        restart_program()

async def connect_websocket():
    uri = "wss://api.rustmagic.com/socket.io/?token=&EIO=4&transport=websocket"  # WebSocket URL'si

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send("40/,{}")
                print("Bağlantı kuruldu")

                while True:
                    message = await websocket.recv()
                    await on_message(websocket, message)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Bağlantı Hatası: {e}")
            restart_program()
            await on_error(e)
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"WebSocket bağlantısı reddedildi. Hata: {e}")
            restart_program()
        except websockets.exceptions.ConnectionClosedOK as e:
            print(f"WebSocket bağlantısı kapandı. Hata: {e}")
            restart_program()
        except requests.exceptions.ConnectionError as e:
            print(f"Bağlantı Hatası: {e}")
            # Programın uygun bir şekilde davranması için gerekli işlemleri burada gerçekleştirin.
            # Örneğin, programı yeniden başlatabilir veya başka bir strateji uygulayabilirsiniz.
            restart_program()


def restart_program():
    print("Program yeniden başlatılıyor...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect_websocket())
