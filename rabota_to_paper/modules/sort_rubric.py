"""
Сортировка словаря рубрик.
Принцип сортировка: по алфавиту.
"""

import logging                                                                  # запись логов

if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ

    logging.basicConfig(filename='sort.log',level=logging.DEBUG)                 # инициализация лог файла
                                                                                # СОЗДАНИЕ ПАПОК
    try:
        file = open("rubric_dict.txt", 'r+')
        pos = 0
        line = file.readlines()
        file.seek(pos)
        sort_text = sorted(line) 
        for new_line in sort_text:
            file.write(new_line)
            pos = file.tell()
        file.close()
    except IOError:
        logging.error('Что-то пошло не так.')
