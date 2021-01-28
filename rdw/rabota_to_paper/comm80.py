# --------------------------------------------------------------------------------
# Сдвигает комментарий на 80-ю позицию. 
# Не трогает строки начинающиеся с комментария.
# Использование: comm80 name.py
# --------------------------------------------------------------------------------

import sys
import os
import logging                                                                  # запись логов

def pos_comm(line):

    # Находим в строке позицию начала комментарий символа '#'

    mem = ""                                                                    # переменная для хранения открытого апострофа
    for i, sim in enumerate(line):                                              # итератор - позиция, символ
        if sim in ("'",'"'):                                                    # если встретился любой апостроф
            if not mem:                                                         # и буфер апострофа пуст
                mem = sim                                                       # значит апостроф отрывающийся. запомнить в буфере. началась символная строка
            elif mem == sim:                                                    # иначе проверяем, если он совпадает с буфером
                mem = ""                                                        # значит апостроф закрывающий. очистить буфер. кончилась символная строка
        if sim == '#' and mem == "":                                            # если это символ комментарий и не внутри строки
            return i                                                            # возвращаем позицию символа

if __name__ == '__main__':

    logging.basicConfig(filename='log.txt',level=logging.DEBUG)                 # log file

    if len(sys.argv) < 2:                                                       # обязательный аргумент имя файла
        logging.error('Консольная команда: comm72 name.py')
        quit()

    # ИМЕНА ФАЙЛОВ
    # Работаем только с файлами питона. К имени выходного файла добавляем
    # подчеркивание. Проверяем наличие входного файла.

    file_name, file_ext = os.path.splitext(sys.argv[1])
    file_ext = '.py'
    in_file = file_name + file_ext
    out_file = file_name + '_' + file_ext
    if not os.path.exists(in_file):
        logging.error('Файл: {} не найден'.format(in_file))
        quit()

    f_out = open(out_file,'w',encoding='utf-8')                                 # файл вывода
    with open(in_file,'r',encoding='utf-8') as f_in:                            # файл входной (сам закроется)
        for line in f_in:                                                       # читаем строку
            line = line.rstrip()                                                # удаляем пробелы в конце строки
            i = pos_comm(line)                                                  # ищем позицию комментария
            if i and line[:i].strip():                                          # есть и комментарий не одинок
              line = ("{0:80}{1}{2}"                                            # комментарий за 80 позицией
                     .format(line[:i].rstrip(),line[i:i],line[i:]))             #
            f_out.write(line + '\n')                                            # вывод в формате UTF-8
    f_out.close()                                                               # закрываем выходной файл
