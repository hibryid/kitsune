# -*- coding: utf-8 -*-
import errno
import json
import os
import pickle
import secrets
import shutil
import socket
import string
import sys
import time
from datetime import datetime

import colorama
import requests


def divider():
    count_of_characters = shutil.get_terminal_size().columns
    output_characters = "=" * (count_of_characters - 1)
    return output_characters


def time_now():
    print(divider())
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    print(f"Время: {now}")


def countdown(message_string, t):
    while t:
        mins, secs = divmod(t, 60)
        time_format = '{}{:02d}:{:02d}'.format(message_string, mins, secs)
        t -= 1
        if t:
            print(time_format, end='\r')
            time.sleep(1)
        else:
            time_format = '{}{:02d}:{:02d}'.format(message_string, mins, secs)
            print(time_format, end='\n')


def remove_playlists(playlists_to_remove):
    print("Запущен процесс автоудаления")
    for mdc_token in playlists_to_remove:
        try:
            pause_url = pause_pattern.format(mdc_token)
            requests.post(pause_url)
            time.sleep(0.5)
            delete_url = "http://127.0.0.1:8102/-/media-delete?doc_id={}".format(mdc_token)
            requests.post(delete_url)
            time.sleep(0.5)
        except requests.exceptions.RequestException as err:
            print(err)
            pass

    print("Автоудаление завершено")


def clean_space_init(nickname):
    if not nickname:
        print("Не удалось получть никнейм! Kitsune не рискнет удалить плейлисты!")
        return

    try:
        downloaded_info = json.loads(requests.post(playlists_url).content.decode('utf-8'))
        results = downloaded_info['results']

        # Выявляем документы из плейлисты на скачивание.
        playlists_to_remove = []
        if results:
            for file_info in results:
                if nickname not in (file_info['user_tx']['sender_nick'], file_info['user_tx']['obj']['nick']):
                    token = file_info['doc_id']
                    playlists_to_remove.append(token)

        if playlists_to_remove:
            remove_playlists(playlists_to_remove)

    except Exception as err:
        print("\nОшибка автоудаления:")
        print(err)


def get_space_info(path):
    space_left = (shutil.disk_usage(path).free / 1024**3)
    return space_left


def get_nickname():
    try:
        res = requests.get(debug_url).json()
        if res["sessNick"] != "":
            return res["sessNick"]
    except requests.exceptions.RequestException:
        return


def download_update(threads_list):
    win_updater = new_kitsune_path = None
    print("Скачиваю обновление")
    try:
        for update_thread in threads_list:
            is_kitsune = update_thread.split("/")[-1:][0] == "kitsune.exe"
            if is_kitsune:
                update_path = os.path.abspath(sys.executable).split("\\")[:-1]
                update_path.append('new.exe')
                new_kitsune_path = update_path = '\\'.join(update_path)
            else:
                updater_name = update_thread.split("/")[-1:][0]
                update_path = os.path.abspath(__file__).split("\\")[:-1]
                update_path.append(updater_name)
                win_updater = update_path = '\\'.join(update_path)

            url = github_url + update_thread

            r = requests.get(url)

            with open(update_path, 'wb') as f:
                f.write(r.content)

        old_kitsune_path = os.path.abspath(sys.executable)
        os.system('start {} -l {} {}'.format(win_updater, old_kitsune_path, new_kitsune_path))
        print("Самоликвидация")
        sys.exit()

    except Exception as err:
        print(err)
        print("Видимо, мы словили ошибку, отпишите @hibryid в telegram")
        time.sleep(200000)


def download(mdc_doc_token):
    try:
        print("Ожидаю ответ Mediacoin...")
        while True:
            nickname = get_nickname()
            if nickname:
                break
            else:
                time.sleep(2)

        info_url = "http://127.0.0.1:8102/-/search?cid={}".format(mdc_doc_token)

        downloaded_info = json.loads(requests.post(info_url).content.decode('utf-8'))
        results = downloaded_info['results']

        # Выявляем документы из плейлисты на скачивание.
        docs_to_download = []
        if results:
            for doc in results:
                try:
                    doc_id = doc['doc']['id']
                    if doc_id:
                        doc_is_downloaded = doc['fs']['status']

                except Exception:
                    doc_id = doc['doc']['id']
                    docs_to_download.append(doc_id)
                    continue
        else:
            print("Неправильный плейлист! Kitsune скачивает плейлисты только целиком!")

        if docs_to_download:
            started_downloading = 0
            count_docs_to_download = len(docs_to_download)
            print("Найдены документы для скачивания: {}".format(count_docs_to_download))
            print("Ожидаю ответ Mediacoin на скачивание...")
            for doc in docs_to_download:
                download_url = "http://127.0.0.1:8102/-/media-download-start?doc_id={}".format(doc)
                counter = 0
                times_to_fail = 3
                while counter < times_to_fail:
                    download_response = requests.post(download_url).content.decode('utf-8')
                    time.sleep(1)
                    counter += 1
                    if download_response == 'true':
                        started_downloading += 1
                        downloading_status = "Mediacoin подтвердил скачивание: [ {} / {} ]".format(
                            started_downloading, count_docs_to_download
                        )

                        print(downloading_status, end=(started_downloading == count_docs_to_download) and '\n' or '\r')
                        break
                    elif counter == times_to_fail:
                        print("\nНеуспешная попытка скачивания")
        else:
            print("Все файлы из плейлиста и так скачаны!")

    except Exception as err:
        print("\nОшибка скачивания:")
        print(err)


def get_token():
    token_file = "token.cfg"
    if os.path.exists(token_file) and os.path.getsize(token_file) > 0:
        token = open(token_file, "r", encoding='utf-8').read().split()[0]
        print(f"Токен клиента найден в {token_file}. НЕ делитесь этим токеном с другими участниками!")
    else:
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for i in range(40))
        open(token_file, "w", encoding='utf-8').write(token)
        print(f"Ваш личный токен был создан и записан в {token_file} . НЕ делитесь этим токеном с другими участниками!")
    return token


class Server:
    HEADER_LENGTH = 10

    def __init__(self, ip, port, seconds):
        connected = False
        while not connected:
            time_now()
            print("Пробую переподключиться MediaKitsune!")
            reconnect_in_seconds = self.seconds = seconds
            try:
                self.ip = ip
                self.port = port
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.ip, self.port))
                self.server_socket.setblocking(False)
                connected = True
                print("Успешное подключение к серверу Kitsune!")

            except(ConnectionRefusedError, TimeoutError):
                connected = False
                countdown('Сервер недоступен, переподключение через: ', reconnect_in_seconds)
                continue

    def send(self, query):
        msg = pickle.dumps(query)
        message = f'{len(msg):<{self.HEADER_LENGTH}}'.encode('utf-8') + msg
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')

        try:
            self.server_socket.send(message_header + message)
        except(ConnectionResetError, TimeoutError) as err:
            print(f'Ошибка(1): {err}')
            self.server_socket.shutdown(socket.SHUT_RDWR)
            countdown('Сервер недоступен, переотправка сообщения через: ', reconnect_seconds)
            # mediaKitsune = Server(IP, PORT, reconnect_seconds)
            Server(IP, PORT, reconnect_seconds)

    def receive(self):
        try:
            print('Получаю задание от сервера')
            self.server_socket.settimeout(100)
            message_header = self.server_socket.recv(self.HEADER_LENGTH)
            if not len(message_header):
                return False

            message_length = int(message_header.decode('utf-8').strip())
            return {'header': message_header, 'data': self.server_socket.recv(message_length)}

        except(ConnectionResetError, ConnectionResetError) as err:
            print(f'ошибка = {err}')
            self.server_socket.close()
            self.server_socket.shutdown(socket.SHUT_RDWR)
            return False

        except socket.timeout as err:
            print(f'timeout = {err}')
            self.server_socket.close()
            self.server_socket.shutdown(socket.SHUT_RDWR)
            return False


def main():
    minutes = 1
    time_now()

    print("Ожидаю ответ Mediacoin...")
    while True:
        if get_nickname():
            break

        else:
            time.sleep(2)

    mediaKitsune = Server(IP, PORT, reconnect_seconds)

    while True:

        query = current_path = nickname = None
        auto_remove = False
        try:
            res = requests.get(debug_url).json()
            pl_downloads = res['fs']['pl_downloads']

            if pl_downloads:
                downloading_playlists = pl_downloads[0]
            else:
                downloading_playlists = []


            nickname = res['sessNick']
            os_platform = res['typeStr']
            current_path = [x['path'] for x in res['fs']['dirs'] if x['current']][0]
            current_downloads = 0

            space_left = get_space_info(current_path)

            for playlist in pl_downloads:
                download_count = int(playlist['downl_count'])
                download_paused = int(playlist['downl_paused'])
                playlist_is_paused = download_count - download_paused != 0

                if playlist_is_paused:
                    current_downloads += 1

            query = {'client_token': client_token, 'platform': os_platform,
                     'client_version': version,
                     'client_extension': client_extension,
                     'nickname': nickname,
                     'current_downloads': current_downloads,
                     'space_left': space_left}

        except(requests.exceptions.RequestException, BaseException) as err:
            print(err)
            time.sleep(2)

        if query:
            mediaKitsune.send(query)

            try:
                answer_data = mediaKitsune.receive()

                if not answer_data:
                    raise Exception('Сервер недоступен(1)')

                # answer_header = answer_data['header'].decode('utf-8')
                answer_inside = answer_data['data']
                answer = pickle.loads(answer_inside[HEADER_LENGTH:])

            except BaseException:
                mediaKitsune = Server(IP, PORT, reconnect_seconds)
                continue

            # Этот Г..легаси код нужно будет исправить
            # P.S. Исправлять дальше некуда, придется поломоать на актуальной версии автообновление
            try:
                while True:
                    goal_download = goal_info = goal_update = False
                    number_of_clients = count_client_docs = mdc_doc_token = threads_list = None
                    time_now()

                    if type(answer) == list:
                        for dictionary in answer:
                            if dictionary['goal'] == 'info':
                                goal_info = True
                                count_client_docs = dictionary['count_client_docs']
                                number_of_clients = dictionary['number_of_clients']
                                minutes = int(dictionary['return_minutes'])

                            if dictionary['goal'] == 'download' and dictionary['mdc_doc_token']:
                                goal_download = True
                                print(dictionary)
                                mdc_doc_token = dictionary['mdc_doc_token']
                                # auto_remove = dictionary['auto_remove']
                                # minimum_space = dictionary['minimum_space']

                                try:
                                    auto_remove = dictionary['auto_remove']
                                    minimum_space = dictionary['minimum_space']
                                except:
                                    auto_remove = False
                                    minimum_space = 5

                            if dictionary['goal'] == 'update':
                                goal_update = True
                                threads_list = dictionary['update_threads']

                            if dictionary['goal'] == 'no_space_left':
                                print("Недостаточно места!")

                    if goal_info:
                        print(f"Ко-во активных клиентов kitsune: {number_of_clients}")
                        print(f"Плейлисты в очереди: {count_client_docs}")

                    if goal_download:
                        text = f"Новый плейлист на загрузку: {mdc_doc_token}"
                        if auto_remove and space_left < minimum_space:
                            clean_space_init(nickname)
                        print(text)
                        if mdc_doc_token not in downloading_playlists:
                            if space_left > minimum_space:
                                download(mdc_doc_token)
                            else:
                                print("Недостаточно места!")
                        else:
                            print("Данный плейлист уже загружается!")

                    if goal_update:
                        if client_extension == 'exe':
                            download_update(threads_list)
                        else:
                            print(f"{divider()}\nОбновите Kitsune клиент вручную!\n{divider()}")
                        while True:
                            time.sleep(1)

                    seconds = 60 * minutes
                    countdown('Следующее обращение через: ', seconds)
                    break

            except IOError as err:
                if err.errno != errno.EAGAIN and err.errno != errno.EWOULDBLOCK:
                    print('1 Reading error: {}'.format(str(e)))
                    mediaKitsune = Server(IP, PORT, reconnect_seconds)
                continue

            except Exception as err:
                print('2 Reading error: {}'.format(str(err)))
                countdown("Произошла ошибка, следующее обращение через:", reconnect_seconds)
                mediaKitsune = Server(IP, PORT, reconnect_seconds)
                continue


if __name__ == '__main__':

    print('MediaKitsune приветствует!')
    print('Новостной канал: t.me/MediaKitsune\nНаша группа: t.me/MediaKitsune_group')

    global HEADER_LENGTH, IP, PORT, client_token, version, client_extension
    global platform, my_username, reconnect_seconds
    global github_url, debug_url
    global pause_pattern

    if getattr(sys, 'frozen', False):
        client_extension = os.path.abspath(sys.executable).split(".")[-1:][0]
    elif __file__:
        client_extension = os.path.abspath(__file__).split(".")[-1:][0]

    version = "1.0.5"
    HEADER_LENGTH = 10
    reconnect_seconds = 30
    IP, PORT = ("140.238.170.213", 37777)
    # IP, PORT = ("127.0.0.1", 37777)
    github_url = "https://github.com/hibryid/kitsune/releases/download/"
    debug_url = "http://127.0.0.1:8102/-/info?type=debug"
    playlists_url = "http://127.0.0.1:8102/-/media-files"
    pause_pattern = "http://127.0.0.1:8102/-/media-download-pause?doc_id={}"

    client_token = get_token()
    print(f"Версия kitsune: {version}")
    if os.name == "nt":
        colorama.init()
    else:
        print("Системы кроме семейства windows - не поддерживаются")

    while True:
        try:
            main()
        except KeyboardInterrupt:
            print("\nMediaKitsune ждет вашего возвращения!")
            time.sleep(3)
            sys.exit()
        except Exception as e:
            print(e)
            print("Произошла непредвиденная ошибка клиента, перезапуск через 5 секунд")
            time.sleep(5)
            continue
