"""
Сортировка словаря рубрик.
"""

import logging                                                                  # запись логов

if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ

    logging.basicConfig(filename='log.txt',level=logging.DEBUG)                 # инициализация лог файла
                                                                                            
    package = input('Choose file for sort: ')
    try:
        file = open(package, 'r+')
        pos = 0
        line = file.readlines()
        file.seek(pos)
        sort_text = sorted(line, key=len, reverse=True) # СТРОКА СОРТИРОВКИ
        for new_line in sort_text:
            file.write(new_line)
            pos = file.tell()
        file.close()
    except IOError:
        print("No such file or directory. Repeat, please!")