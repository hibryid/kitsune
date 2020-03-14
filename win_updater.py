import os, sys, time
import argparse

def rename():
    try:
        print('Обновление через 3 секунды')
        time.sleep(3)
        parser = argparse.ArgumentParser(description = 'Kitsune updater for windows')
        parser.add_argument('-l','--list', nargs='+', required=True, action='store', dest='list', help='-l list')
        args = parser.parse_args()
        old_new_versions = vars(args)['list']
        path_of_old_one = old_new_versions[0]
        path_of_new_one = old_new_versions[1]

        os.remove(path_of_old_one)
        os.rename(path_of_new_one, path_of_old_one)
        path_of_new_one = path_of_old_one
        os.system("start {}".format(path_of_new_one))
        print('Апдейт успешно выполнен')
        time.sleep(3)

    except(Exception) as e:
        print(e)
        print('Обвновление провалено. Отпишите t.me/hibryid')
        time.sleep(2000)

if __name__ == '__main__':
    rename()
