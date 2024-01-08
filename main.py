elif status_data["status"] == "failed":
    # Görev başarısız oldu, yeniden HCaptcha çözüm yap
    print("Görev başarısız oldu. Yeniden HCaptcha çözüm yapılıyor...")

    # Yeniden HCaptcha çözümü için işlemler
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

        # Görev durumunu sorgulama döngüsü (diğer kodlar aynı kalacak)
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
