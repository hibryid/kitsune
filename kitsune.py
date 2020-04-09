# -*- coding: utf-8 -*-
import os, re, sys, time, errno, socket, json
import pickle, select, string, secrets, shutil
from time import sleep
import requests, argparse, colorama
from termcolor import colored
from datetime import datetime


def delimeter():
    count_of_characters = shutil.get_terminal_size().columns
    output_characters = "=" * (count_of_characters - 1)
    return(output_characters)


def time_now():
    print(delimeter())
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    print(f"Время: {now}")


def countdown(string, t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{}{:02d}:{:02d}'.format(string, mins, secs)
        t -= 1
        if t:
            print(timeformat, end='\r')
            time.sleep(1)
        else:
            timeformat = '{}{:02d}:{:02d}'.format(string, mins, secs)
            print(timeformat, end='\n')


def download_update(threads_list):
    try:
        for update_thread in threads_list:
            is_kitsune = update_thread.split("/")[-1:][0] == "kitsune.exe"
            if is_kitsune:
                update_path = os.path.abspath(sys.executable).split("\\")[:-1]
                update_path.append('new.exe')
                new_kitsune_path = update_path = '\\'.join(update_path)
            else:
                updaterName = update_thread.split("/")[-1:][0]
                update_path = os.path.abspath(__file__).split("\\")[:-1]
                update_path.append(updaterName)
                win_updater = update_path = '\\'.join(update_path)
                # print(update_path)

            url = "https://github.com/hibryid/kitsune/releases/download/" + update_thread
            # print(update_path)
            # print(url)

            r = requests.get(url)
            with open(update_path, 'wb') as f:
                f.write(r.content)


        # old_kitsune_pid = os.getpid()
        # print(old_kitsune_pid)
        old_kitsune_path = os.path.abspath(sys.executable)
        # list = [old_kitsune_path, new_kitsune_path]
        os.system('start {} -l {} {}'.format(win_updater, old_kitsune_path, new_kitsune_path))
        print("Самоликвидация")
        sys.exit()

    except(Exception) as e:
        print(e)
        print("Видимо, мы словили ошибку, отпишите @hibryid в telegram")
        time.sleep(2000)


def download(mdc_doc_token):
    try:
        print("Ожидаю ответ Mediacoin...")
        while True:
            try:
                res = requests.get("http://127.0.0.1:8102/-/info?type=debug").json()
                if (res["sessNick"] != ""):
                    print("Подключение установлено!")
                    break
            except(Exception):
                time.sleep(2)

        infoURL = "http://127.0.0.1:8102/-/search?cid={}".format(mdc_doc_token)
        downloadURL = "http://127.0.0.1:8102/-/media-download-start?doc_id={}".format(mdc_doc_token)

        downloaded_info = json.loads(requests.post(infoURL).content.decode('utf-8'))
        results = downloaded_info['results']

        # Выявляем документы из раздачи на скачивание.
        docs_to_download = []
        if results:
            for doc in results:
                try:
                    doc_id = doc['doc']['id']
                    if doc_id:
                        doc_is_downloaded = doc['fs']['status']

                except(Exception):
                    doc_id = doc['doc']['id']
                    docs_to_download.append(doc_id)
                    continue
        else:
            print("Неправильная раздача!")
            sys.exit()

        if docs_to_download:
            started_downloading = 0
            count_docs_to_download = len(docs_to_download)
            print("Найдены документы для скачивания: {}".format(count_docs_to_download))
            print("Ожидаю ответ Mediacoin на скачивание...")
            for doc in docs_to_download:
                downloadURL = "http://127.0.0.1:8102/-/media-download-start?doc_id={}".format(doc)
                counter = 0
                times_to_fail = 3
                while counter < times_to_fail:
                    download_response = requests.post(downloadURL).content.decode('utf-8')
                    time.sleep(3)
                    counter += 1
                    if download_response == 'true':
                        started_downloading += 1
                        downloading_status = "Mediacoin подтвердил скачивание: [ {} / {} ]".format(started_downloading, count_docs_to_download)
                        print(downloading_status, end = (started_downloading==count_docs_to_download) and '\n' or '\r')
                        break
                    elif counter == times_to_fail:
                        print("\nНеуспешная попытка скачивания")

        else:
            print("Все раздачи и так скачаны!")

    except(Exception) as e:
        print("\nОшибка скачивания:")
        print(e)


def get_token():
    tokenFile = "token.cfg"
    if os.path.exists(tokenFile) and os.path.getsize(tokenFile) > 0:
        token = open(tokenFile, "r", encoding='utf-8').read().split()[0]
        print(f"Токен клиента найден в {tokenFile}. НЕ делитесь этим токеном с другими участниками!")
    else:
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for i in range(40))
        open(tokenFile, "w",  encoding='utf-8').write(token)
        print(f"Ваш личный токен был создан и записан в {tokenFile} . НЕ делитесь этим токеном с другими участниками!")
    return(token)


class server():
    HEADER_LENGTH = 10
    def __init__(self, ip, port, seconds):
        connected = False
        while not connected:
            time_now()
            print("Пробую переподключиться MediaKitsune!")
            try:
                self.ip = ip
                self.port = port
                reconnect_seconds = self.seconds = seconds
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.ip, self.port))
                self.server_socket.setblocking(False)
                connected = True
                print("Успешное подключение к серверу Kitsune!")

            except(ConnectionRefusedError, TimeoutError) as e:
                connected = False
                # print(e)
                countdown('Сервер недоступен, переподключение через: ', reconnect_seconds)
                # print("Сервер недоступен, переподключение через 5 секунд")
                # sleep(5)
                continue

    def send(self, query):
        # HEADER_LENGTH = 10
        msg = pickle.dumps(query)
        message = f'{len(msg):<{self.HEADER_LENGTH}}'.encode('utf-8') + msg
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')

        connected = False
        reconnect_seconds = 5
        while not connected:
            try:
                self.server_socket.send(message_header + message)
                connected = True
                continue
            except(ConnectionResetError, TimeoutError) as e:
                print(f'Ошибка(1): {e}')
                connected = False
                self.server_socket.shutdown(socket.SHUT_RDWR)
                countdown('Сервер недоступен, переотправка сообщения через: ', reconnect_seconds)
                mediaKitsune = server(IP, PORT, reconnect_seconds)
                continue

    def receive(self):
        try:
            print('Получаю задание от сервера')
            self.server_socket.settimeout(100)
            message_header = self.server_socket.recv(self.HEADER_LENGTH)
            if not len(message_header):
                return False

            message_length = int(message_header.decode('utf-8').strip())
            return {'header': message_header, 'data': self.server_socket.recv(message_length)}

        except(ConnectionResetError, ConnectionResetError):
            self.server_socket.close()
            self.server_socket.shutdown(socket.SHUT_RDWR)
            return False

        except(socket.timeout) as e:
            print(f'timeout = {e}')
            return False


def main():

    time_now()

    print("Ожидаю ответ Mediacoin...")
    while True:
        try:
            res = requests.get("http://127.0.0.1:8102/-/info?type=debug").json()
            if (res["sessNick"] != ""):
                print("Mediacoin запущен!")
                break
        except(Exception):
            time.sleep(2)

    mediaKitsune = server(IP, PORT, reconnect_seconds)

    while True:
        try:
            res = requests.get("http://127.0.0.1:8102/-/info?type=debug").json()
            pl_downloads = res['fs']['pl_downloads']
            nickname = res["sessNick"]
            platform = res["typeStr"]
            current_downloads = 0
            for playlist in pl_downloads:
                downl_count = int(playlist['downl_count'])
                downl_paused = int(playlist['downl_paused'])
                playlist_is_paused = downl_count - downl_paused != 0

                if playlist_is_paused:
                    current_downloads += 1

            query = {'client_token': client_token, 'platform': platform,
                        'client_version': version,
                        'client_extension': client_extension,
                        'nickname': nickname,
                        'current_downloads': current_downloads}

        except(Exception):
            time.sleep(2)


        if query:
            msg = pickle.dumps(query)
            message = f'{len(msg):<{HEADER_LENGTH}}'.encode('utf-8') + msg
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            mediaKitsune.send(query)

        try:
            answer_data = mediaKitsune.receive()

            if answer_data == False:
                raise Exception('Сервер недоступен(1)')

            answer_header = answer_data['header'].decode('utf-8')
            answer_inside = answer_data['data']
            answer = pickle.loads(answer_inside[HEADER_LENGTH:])
            # print(answer)

        except(Exception):
            mediaKitsune = server(IP, PORT, reconnect_seconds)
            continue

        except(ValueError, TypeError):
            continue

        try:
            while True:
                time_now()
                if type(answer) == list:
                    for dict in answer:
                        if dict['goal'] == 'info':
                            print(f"Ко-во активных клиентов kitsune: {dict['number_of_clients']}")
                            print(f"Раздачи в очереди: {dict['count_client_docs']}")
                            minutes = int(dict['return_minutes'])

                        if dict['goal'] == 'download' and dict['mdc_doc_token']:
                            print(f"Новая раздача: {dict['mdc_doc_token']}")
                            download(dict['mdc_doc_token'])
                        elif dict['goal'] == 'info' and dict['count_client_docs']:
                            print('Задание отсутствует: превышен лимит одновременных скачиваний')

                        if dict['goal'] == 'update':
                            if client_extension == 'exe':
                                # mediaKitsune.disconnect()
                                threads_list = dict['update_threads']
                                download_update(threads_list)
                            else:
                                print(f"{delimeter()}\nОбновите Kitsune клиент вручную!\n{delimeter()}")
                            while True:
                                time.sleep(1)

                seconds = 60 * minutes
                countdown('Следующее обращение через: ', seconds)
                break

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('1 Reading error: {}'.format(str(e)))
                mediaKitsune = server(IP, PORT, reconnect_seconds)

            continue

        except Exception as e:
            print('2 Reading error: {}'.format(str(e)))
            countdown("Произошла ошибка, следующее обращение через:", reconnect_seconds)
            mediaKitsune = server(IP, PORT, reconnect_seconds)
            continue


if __name__ == '__main__':

    print('MediaKitsune приветствует!')
    print('Новостной канал: t.me/MediaKitsune\nНаша группа: t.me/MediaKitsune_group')

    global HEADER_LENGTH, IP, PORT, client_token, version, client_extension
    global platform, my_username, reconnect_seconds

    if getattr(sys, 'frozen', False):
        client_extension = os.path.abspath(sys.executable).split(".")[-1:][0]
    elif __file__:
        client_extension = os.path.abspath(__file__).split(".")[-1:][0]

    print(client_extension)
    HEADER_LENGTH = 10
    IP, PORT = ("5.181.166.103", 37777)
    # IP, PORT = ("127.0.0.1", 37777)
    reconnect_seconds = 30
    version = "1.0.0.8"
    client_token = get_token()

    if os.name =="nt":
        colorama.init()

    while True:
        try:
            main()
        except(KeyboardInterrupt):
            print("\nMediaKitsune ждет вашего возвращения!")
            time.sleep(3)
            sys.exit()
        except(Exception) as e:
            print(e)
            print("Произошла непредвиденная ошибка клиента, перезапуск через 5 секунд")
            time.sleep(5)
            continue
