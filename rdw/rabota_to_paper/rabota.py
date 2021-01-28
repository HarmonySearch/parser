# -----------------------------------------------------------------------------
# Выкладка вакансий с rabota.ru в строчные объявления в газету

# -----------------------------------------------------------------------------

release = '(2.01)'

import os, sys, logging, configparser, re, sqlite3

from lxml import etree

from datetime import date
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

# хлам ---------------------------------------------------------------------------
# from PyQt5.QtWebKitWidgets import *
# from PyQt5.QtNetwork import *
# хлам ---------------------------------------------------------------------------

# ШАБЛОНЫ

pattern_teg = re.compile(r'<.*?>')                                              # теги

codes_html = {"</li>":"$", "<br />":"$", "<br>":"$", "\\":"/"}

def main():

    # стандартная запускалка

    app = QApplication(sys.argv)
    app.setStyleSheet(open('pack/style.qss', 'r').read())

    logging.basicConfig(filename='log.txt',level=logging.DEBUG,
        format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s %(message)s')

    window = MainWindow()                                                       # создаем окно
    sys.exit(app.exec())                                                        # Запускаем цикл обработки событий


class MainWindow(QDialog):

    # В процессе исполнения кода все виджеты формы создаются как локальные переменные.
    # Затем закладываются в контейнеры виждеты. Вся итоговая структура локальных
    # сохраняется оператором self.setLayout(vbox). Чтобы иметь доступ к элементам
    # класса, используем self там, где необходимо.

    toHtmlFinished = pyqtSignal()                                               # сигнал окончания асинхронной загрузки html кода

    def __init__(self, parent=None):
        super().__init__()                                                      # запускаем init родительского класса

        self.create_environment() # создание переменных
        self.create_ui() # создание пользовательского интерфейса


    def create_environment(self):

        # рабочее оркужение ----------------------------------------------------


        # ищем путь к рабочему столу в реестре. Если на стол нужно файлы писать.
        
        import winreg

        REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, "Desktop")
        self.desktop = value

        # названия файлов
        
        # self.file_out = 'spider.csv'
        # self.file_log = 'file.log'
        # self.file_ini = 'file.ini'

        # БД SQLite
        self.file_db = 'pack/file.db'
        self.con = sqlite3.connect(self.file_db)
        self.con.row_factory = sqlite3.Row                                      # для доступа к полям по имени
        query = self.con.cursor()
        query.execute("CREATE TABLE IF NOT EXISTS vacant "
                "(rec_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,"
                "id_vacant TEXT DEFAULT '',"
                "id_user TEXT DEFAULT '', "
                "id_org TEXT DEFAULT '',"
                "conditions TEXT DEFAULT '',"
                "region TEXT DEFAULT '', "
                "rubr TEXT DEFAULT '', "
                "prof TEXT DEFAULT '', "
                "salary TEXT DEFAULT '',"
                "face TEXT DEFAULT '', "
                "phone TEXT DEFAULT '',"
                "email TEXT DEFAULT '', "
                "moscau INTEGER DEFAULT 0,"
                "descript TEXT DEFAULT '', "
                "needs TEXT DEFAULT '', "
                "debug TEXT DEFAULT '');")

        query.execute("CREATE TABLE IF NOT EXISTS user_org ("
                "rec_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,"
                "id_user TEXT DEFAULT '',"
                "id_org TEXT DEFAULT '');")

        query.execute("CREATE TABLE IF NOT EXISTS org_ban ("
                "rec_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,"
                "id_org TEXT DEFAULT '');"
                )
        query.close()
        
        # словарь элементарных операций для отладки
        self.phase_dict = {                                                     
            ' ВЫБРАТЬ ОПЕРАЦИЮ' : '',
            ' Переход на страницу загрузок ' : 'self.load_page()',
            ' Загрузка тестовой страницы ' : 'self.test_page()',
            ' html в файл' : 'self.test_page()',
            ' Парсим' : 'self.pars_page()',
            ' Расстановка рубрик' : 'self.rubric()',
            ' Выгрузка' : 'self.unload()',
            ' всякое' : 'self.xxx()',
            ' всякое' : 'self.xxx()',
            ' Выход' : 'self.finish()'
            }
        self.phase_model = QStringListModel(list(self.phase_dict.keys()))       # модель для поля со списком



    def create_ui(self):

        # создание пользовательского интерфейса -------------------------------

        vacant = QPushButton('ВАКАНСИИ')                                        # переход на страницу вакансий
        vacant.clicked.connect(self.open_page_vacant)                             

        start = QPushButton('ПАРСИМ')                                            # 
        start.clicked.connect(self.start)

        upload = QPushButton('ВЫГРУЖАЕМ')                                            # 
        upload.clicked.connect(self.unload)
        
        self.phase = QComboBox()                                                # поле со списком элементарных операций
        self.phase.setModel(self.phase_model)

        debug = QPushButton('ОТЛАДКА')                                          # вторая кнопка для отладки + отдельные операции элементарные
        debug.clicked.connect(self.debug)

        hbox_button = QHBoxLayout()                                             # горизонтальный бокс с кнопками
        hbox_button.addWidget(vacant)
        hbox_button.addWidget(start)
        hbox_button.addWidget(upload)
        hbox_button.addStretch()
        hbox_button.addWidget(self.phase)
        hbox_button.addWidget(debug)

        self.web_view = QWebEngineView()
        self.current_page = self.web_view.page()

        self.web_view.load(QUrl("https://www.rabota.ru/admin/index.php?area=main")) # логин: samara пароль: Xahth8io

        self.message = QTextEdit()
        self.error = QTextEdit()

        hbox_mess_err = QHBoxLayout()                                             # горизонтальный бокс с кнопками
        hbox_mess_err.addWidget(self.message)                                        # 3 - коэффициент растяжения
        hbox_mess_err.addWidget(self.error)                                        # 3 - коэффициент растяжения


        vbox = QVBoxLayout()
        vbox.addLayout(hbox_button)
        vbox.addWidget(self.web_view, 3)                                        # 3 - коэффициент растяжения
        vbox.addLayout(hbox_mess_err)

        self.setLayout(vbox)
        self.setWindowTitle('ГРАБИМ админку RABOTA.RU '+ release)
        self.setWindowIcon(QIcon('pack/yarn.svg'))
        self.resize(1000, 1000)
        self.show()


    def debug(self):

        # выполнить отдельную операцию ----------------------------------------

        exec(self.phase_dict[self.phase.currentText()])
        self.phase.setCurrentIndex(0)


    def finish(self):

        # закрыть программу ---------------------------------------------------

        print ('АМИНЬ')
        sys.exit()


    def open_page_vacant(self):

        # переходим на страницу вакансий для парсинга. адрес храним в файле.
        # адрес обновляется после старта парсинга.

       
        f = open('pack/page_vacant.txt', 'r',encoding='utf-8')
        url = f.readline()
        f.close()
        self.current_page.load(QUrl(url))


    def start(self):
    
        # рабочий цикл парсинга
        
        # чистим таблицу вакансий
        query = self.con.cursor()
        query.executescript("DELETE FROM vacant; VACUUM;")
        
        self.current_page.loadFinished.connect(self._on_load_finished)

        self.url = self.current_page.url().toString()
        # пишем в файл стартовый адрес страницы вакансий, чтобы с него начать в следующий раз
        f = open('pack/page_vacant.txt', 'w',encoding='utf-8')                             
        f.write(self.url)
        f.close()

        # модифицуируем url (per_page=10 на per_page=50 по 50 вакансий и добавляем &offset=, +50 шаг по 50 вакансий
        self.url = self.url.replace('per_page=10','per_page=50') + '&offset='
        #print('1-',self.url)
        pattern_id_vacant = re.compile('id_предложения ([\d]+?),')              # id вакансии
        offset = 0

        while 1:         # делаем бесконечный цикл с переходом на очередную страницу
            
            url = self.url + str(offset)
            #print('2-',url)
            self.get_html(url)
            #print('3-')
            
            if pattern_id_vacant.search(self.html): # если 'id_предложения' найдено? то ещё есть вакансии
            
                # записываем код страницы в файл. и запускаем парсинг файла
                # замыкаем цикл
                # print('4-')
                self.pars_page() # парсим из файла
                print('отпарсили')
                
                # if offset == 300:
                    # break

            else:                                                               # Вакансий больше нет,
                break                                                           # поэтому выходим из бесконечного цикла.
        
            offset += 50                                                        # Смещаемся на следующие 50 вакансий.

        self.rubric()



        # чтение и запись html кода в файл  ---------------------------------
        # запись ведется на случай вылета программы, чтобы искать ошибку 
        # по коду 
        
        # что происходит: 
        # У QWebEngineView есть метод page() у которого есть метод load() 
        # для загрузки url. Этот метод асинхронный, поэтому необходимо 
        # дождаться загрузки страницы. У него есть сигнал loadFinished,
        # который подключаем к слоту _on_load_finished(). Этот слот функция.
        # запускает метод загрузки html кода, который тоже асинхроный (
        # и нужно дождаться когда скопируется html код. Этот метод тоже 
        # подключается к слоту, который записывает код в переменну. Мы
        # ждем только запись html кода в переменную. 
        
        # loop = QEventLoop()
        # self.toHtmlFinished.connect(loop.quit)
        # loop.exec_()

        # # пишем в файл html код
        # ff = open('txt.html', 'w',encoding='utf-8')                             # пишем в файл для разборки
        # ff.write(self.html)
        # ff.close()
        


    def save_html(self):
    

        self.get_html(self.current_page.url())
        # loop = QEventLoop()
        # self.toHtmlFinished.connect(loop.quit)
        # loop.exec_()


    def get_html(self,url):

        # загружаем страницу --------------------------------------------------

        self.current_page.load(QUrl(url))
        # print(url)
        loop = QEventLoop()
        self.toHtmlFinished.connect(loop.quit)
        loop.exec_()
        # пишем в файл html код
        ff = open('txt.html', 'w',encoding='utf-8')                             # пишем в файл для разборки
        ff.write(self.html)
        ff.close()


    def _on_load_finished(self):

        # читаем html код --------------------------------------------------
        
        self.current_page.toHtml(self.store_html)


    def store_html(self, html):
    
        # сохраняем код --------------------------------------------------

        self.html = html                                                        # сохраняем html код
        self.toHtmlFinished.emit()                                              # посылаем сигнал, чтобы завершить loop цикл

    def xxx(self):


        print(self.current_page.url().toString())

    def pars_page(self):

        # парсим html код из файла --------------------------------------------------

        def need_find(s):

            # выделяет из строки требования и возвращает ввиде строки ---------
            # при появлении в строки "Требование" или "Требования"
            # начинаем сохранять строки пока не появится строк
            # с Заглавной буквы и с окончанием на ":"
            
            print('----------------------',s)

            list = s.splitlines()

            # Со строками не все гладко. В HTML коде встречаются теги <br>. Их нужно обрабатывать до разбивки на строки. Сюда нужно подавать сырую строку.
            # обрабатывать <br>, потом убирать все тэги и после этого работать.


            p1 = re.compile('Требовани[я|е]:')
            p2 = re.compile('[А-Я].+:')
            triger = False
            ss = ''
            for l in list:
                if (p1.search(l)):
                    triger = True
                    continue

                if (p2.search(l) and triger):
                    break

                if triger:
                    ss = ss + l

            return ss


        def separation_needs(descript):


            codes_html = {"</li>":"$", "<br />":"$", "<br>":"$", "\\":"/"}

            codes_spec = {
                "&quot;":'"', "&amp;":"&", "&lt;":"<", "&gt;":">", "&nbsp;":" ",
                "&iexcl;":"¡", "&cent;":"¢", "&euro;":"€", "&pound;":"£", "&curren;":"¤",
                "&yen;":"¥", "&brvbar;":"¦", "&sect;":"§", "&uml;":"¨", "&copy;":"©",
                "&trade;":"™", "&laquo;":"«", "&not;":"¬", "&reg;":"®", "&macr;":"¯",
                "&deg;":"°", "&plusmn;":"±", "&times;":"×", "&divide;":"÷", "&sup2;":"²",
                "&sup3;":"³", "&acute;":"´", "&fnof;":"ƒ", "&micro;":"µ", "&para;":"¶",
                "&middot;":"·", "&cedil;":"¸", "&sup1;":"¹", "&ordm;":"º", "&ordf;":"ª",
                "&raquo;":"»", "&frac14;":"¼", "&frac12;":"½", "&frac34;":"¾", "&iquest;":"¿",
                "&larr;":"←", "&uarr;":"↑", "&rarr;":"→", "&darr;":"↓", "&harr;":"↔",
                "&spades;":"♠", "&clubs;":"♣", "&hearts;":"♥", "&diams;":"♦", "&ne;":"≠",
                "&loz;":"◊", "&circ;":"ˆ", "&tilde;":"˜	", "&bull;":"•", "&hellip;":"…",
                "&prime;":"′", "&Prime;":'″', "&oline;":"‾", "&frasl;":"⁄", "&ndash;":"–",
                "&mdash;":"—", "&lsquo;":"‘", "&rsquo;":"’", "&sbquo;":"‚", "&ldquo;":"“",
                "&rdquo;":"”", "&bdquo;":"„", "&rho;":"р"}

            pattern_needs = re.compile(
                '(ребования:|ребование:)(.+?)(</ul>|</tr>)',re.S)                   # требования


            # --------- Выделение требований из описания вакансии.

            if not descript:                                                    # Нет исходных данных.
                return ''

            match = pattern_needs.search(descript)                              # Ищем раздел "Требования" в описании вакансии
            if match:
                needs = match.group(2)
            else:
                return ''

            needs = needs.replace("\n"," ")                                     # Удалем из html кода переносы строк.
            needs = needs.replace("&#13;","")                                     # Удалем из html кода переносы строк.
            #needs = needs.replace("\'","")                                          # Удалем из html кода символы апострофа (БД его не принимает).
            for code in codes_html:                                             # Заменяем html теги на их символьные эквиваленты.
                needs = needs.replace(code,codes_html[code])
            for code in codes_spec:                                             # Заменяем специальные символы html на их символьные эквиваленты.
                needs = needs.replace(code,codes_spec[code])
            needs = pattern_teg.sub('', needs)                                  # Убираем все остальные теги.
            needs = needs.strip(" $")                                           # Чтобы пустых фраз не было
            phrase = needs.split('$')                                           # Разбиваем на фразы.

            phrase = phrase[0:3]                                                # Урезаем список требования до трёх строк

            for i, item in enumerate(phrase):                                   # чистим фразы
                phrase[i] = phrase[i].strip(" -,‚.;:!•")                        # Удалем знаки препинания в конце и вначале.
                phrase[i] = phrase[i][0:1].lower() + phrase[i][1:]              # первое слово с маленькой буквы
            needs = "; ".join(phrase)                                           # Соединяем фразы в единое предложение через ;
            if len(needs) > 500:                                                # Слишком обширные требования.
                return('')
            return("Требования: {}.".format(needs))



        query = self.con.cursor()

        # парсим из файла

        self.message.insertPlainText('парсим страницу\n')

        parser = etree.HTMLParser()
        tree   = etree.parse("txt.html", parser)


        # ЦИКЛ ПО ВСЕМ ТАБЛИЦАМ ВАКАНСИЙ. ПОКА НЕТ
        # сколько строк в главной таблице? каждая строка вакансия
        tag_vacant = tree.find("//*[@cellspacing='2']/tbody")
        vacants = len(tag_vacant) - 2                                           # минус четыре служебные строки к вакансиям не относятс. одна в начале и три в конце и плюс верхняя граница и х.з
##        print('Вакансий в странице ',vacants)

        # for vacant_row in range(2, vacants + 1): # верхняя граница не включается
        for vacant_row in range(2, vacants):                                    # верхняя граница не включается
            # print(vacant_row)

            # ID вакансии и работодателя
            element_id = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/span".format(vacant_row))
            s = etree.tounicode(element_id[0], method="text")
            pattern_id = re.compile('id_предложения ([0-9]*), id_пользователя ([0-9]*)')
            m = pattern_id.search(s)
            if not m:
                self.error.insertPlainText('не найдены ID')
                # здесь что-то делаем если не нашли. особый случай
            id_vacant = m.group(1)
            id_user = m.group(2)

            # профессия и зарплата
            tag_prof_salary = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/h2".format(vacant_row))
            s = etree.tounicode(tag_prof_salary[0], method="text")
            pattern_prof_salary = re.compile('[\t]+([^\t]+)[\t]+([^\t]+)')
            m = pattern_prof_salary.search(s)
            if not m:
                self.error.insertPlainText('не найдены профессия и зарплата')
            prof = m.group(1)
            salary = m.group(2)

            # описание вакансии
            tag_descript = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[7]/td[2]".format(vacant_row))
            # s = etree.tounicode(tag_needs[0], method="text")                    # method="text" убрать теги
            descript = etree.tounicode(tag_descript[0])                    # с тегами
            # print (descript)
            needs = separation_needs(descript)

            email = ''                                                          # Возможно отсутствие телефона или почты. чтобы не слетела запись в БД
            phone = ''

            # сколько строк в таблице?
            tag = tree.find("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody".format(vacant_row))
            row = len(tag)

            # перебор таблицы. по совпадениям в первой колонке читаем вторую колонку

            for x in range(2, row+1):                                           # верхняя граница не включается

                tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[1]".format(vacant_row, x))
                s = etree.tounicode(tag[0], method="text")
                #if (vacant_row == 21):
                    # print(x,'-',s)


                # Условия труда: это вахта

                if ('Условия труда:' in s):
                    # print('Условия труда:')
                    tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[2]".format(vacant_row, x))
                    s = etree.tounicode(tag[0], method="text")
                    # print(s)
                    pattern_cond = re.compile('[\t]+([^\t]+)[\t]+')
                    m = pattern_cond.search(s)
                    if not m:
                        self.error.insertPlainText('не найден Условия труда:')
                    conditions = m.group(1)
    ##                print(m,m.group(1))

                    continue

                # Регион размещения
                if ('размещения:' in s):
                    tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[2]".format(vacant_row, x))
                    s = etree.tounicode(tag[0], method="text")
                    pattern_region = re.compile('[\t]+([^\t]+)[\t]+')
                    m = pattern_region.search(s)
                    if not m:
                        print('не найден регион')
                    region = m.group(1).rstrip()
                    # print(m,m.group(1))
                    continue

                # Контактное лицо
                if ('Работодатель:' in s):
                    tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[2]".format(vacant_row, x))
                    s = etree.tounicode(tag[0], method="text")
                    pattern_face = re.compile('([^\t]+)[\t]+')
                    m = pattern_face.search(s)
                    if not m:
                        self.error.insertPlainText('не найден работодатель')
                    face = m.group(1)
                    # print(face)

                    continue

                if ('Телефон:' in s):
                    tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[2]".format(vacant_row, x))
                    s = etree.tounicode(tag[0], method="text")
                    # print(s)
                    pattern_phone = re.compile('(.+)')
                    m = pattern_phone.search(s)
                    if not m:
                        print('не найден телефон')
                    phone = m.group(1)
                    phone = phone.strip()
                    # print(phone)

                    continue

                if ('E-mail:' in s):
                    tag = tree.xpath("//*[@cellspacing='2']/tbody/tr[{}]/td[2]/table/tbody/tr[{}]/td[2]".format(vacant_row, x))
                    s = etree.tounicode(tag[0], method="text")
                    pattern_region = re.compile('(.+)')
                    m = pattern_region.search(s)
                    if not m:
                        print('не найден E-mail')
                    email = m.group(1)

                    continue


            # ЗАПИСЬ в БД
            # Ошибка в процесс записи считаем фатальной.



            try:
                query.execute("INSERT INTO vacant (id_vacant, id_user, prof, salary, conditions, region, face, phone, email, descript, needs)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?);",(id_vacant, id_user, prof, salary, conditions, region, face, phone, email, descript, needs))

            except sqlite3.Error as e:
                logging.critical('btn_collect_ref_click: {} {}'.format( e.args[0],sql))

            self.con.commit()

        print('удачно')



    def prep_dict(self):

        # Читаем словарь и сортируем по длинне регулярного выражения в обратном порядке
        # чтобы снчала проверять на более часные совпадения а потом на более общие
        # print('начали')

        with open("tuning/rubric_dict.txt",'r') as file:
            line = file.readlines()                                             # file.readlines()  -> list
            # line = line.lower()
        sort_list = sorted(line, key=len, reverse=True)                         # key=len функция сортировки

        # Создаём список: [[патерн, рубрика], ...]
        pattern_dict = re.compile(r'(.*)\$(.*)')
        self.rubrics = []
        for line in sort_list:
            me = pattern_dict.search(line)
            if me:
                try:
                    self.rubrics.append([re.compile(me.group(1)),me.group(2)])
                except re.error:
                    logging.error('Ошибка регулярного выражения словаря рубрик: [{}]'.format(line))
                    QMessageBox.critical(None, "КРИТИЧЕСКАЯ ОШИБКА",
                        "Подробности в файле log.txt.")
                    quit()
            else:
                logging.error('Ошибка парсинга словаря рубрик: [{}]'.format(line))
                QMessageBox.critical(None, "КРИТИЧЕСКАЯ ОШИБКА",
                    "Подробности в файле log.txt.")
                quit()



    def rubric(self):

        # расставляем рубрики вакансий
        # читаем вакансию и условия
        # если вахта то сразу рубрика 900
        # иначе смотрим по таблице профессий рубрику
        # в таблицу рубрик добавляем столбец с новой рубрикой

        self.prep_dict()                                                        # подготавливаем словарь
        # print(self.rubrics)

        query = self.con.cursor()
        query.execute("SELECT rec_id, conditions, prof FROM vacant;")
        rec_all = query.fetchall()
        for rec in rec_all:
            rubr = 0
            # print (rec['conditions'])
            # print ('вахта' in rec['conditions'])
            if ('вахта' in rec['conditions']):
                rubr = 900
            else:
            # ПРИСВАИВАЕМ РУБРИКУ (по названию професии)
            # Итерация списка рубрик. Каждый элемент списка - массив двух элементов:
            # ссылка на откомпилированное регулярное выражение и номер рубрики.
            # Ищем регулярное выражение в названии профессии. Если найдено, то
            # присваиваем рубрику и заканчиваем поиск.

                prof = rec['prof'].lower()
                for index, rubric in enumerate(self.rubrics):
                    # print(index,rubric)
                    if rubric[0].search(prof):
                        rubr = rubric[1]
                        break

            sql = ("UPDATE vacant SET rubr = '{}' WHERE rec_id = {}".format(rubr, rec['rec_id']))
            query.execute(sql)
            self.con.commit()



    def unload(self):

        # необходимо выводить в два файла в тольяттински и самарский
        # здесь только две первые цифры рублики. третья не имеет значения
    
        rub_dict = {
                '11': 'ФИНАНСЫ. ПРАВО. ОФИС',
                '14': 'КОМПЬЮТЕРЫ и IT',
                '15': 'ПРОИЗВОДСТВО. СТРОИТЕЛЬСТВО',
                '17': 'МАРКЕТИНГ. РЕКЛАМА',
                '18': 'ТОРГОВЛЯ',
                '19': 'ЛОГИСТИКА. СКЛАД',
                '20': 'ТРАНСПОРТ. АВТОБИЗНЕС',
                '21': 'МЕДИЦИНА. ФАРМАЦИЯ',
                '22': 'ОБРАЗОВАНИЕ. КУЛЬТУРА',
                '23': 'РЕСТОРАНЫ. ПИТАНИЕ',
                '24': 'ОХРАНА. ПОЛИЦИЯ',
                '25': 'УСЛУГИ',
                '26': 'РАБОТА ДЛЯ ВСЕХ',
                '27': 'СЕТЕВОЙ МАРКЕТИНГ',
                '30': 'ОБУЧЕНИЕ',
                '40': 'ПЕРСОНАЛ',
                '50': 'РАБОТА ВАХТОВЫМ МЕТОДОМ',
                '90': 'РАБОТА В МОСКВЕ',
                '0': 'БЕЗ РУБРИКИ'
                }

        # читаем список городов
        f_locality = open('tuning/locality.txt', 'r',encoding='utf-8')
        loc_samara = f_locality.readline().rstrip().split(',')                  # самарские города
        for i, city in enumerate(loc_samara):
            loc_samara[i] = city.strip()

        loc_tlt = f_locality.readline().rstrip().split(',')                     # тольяттинские города
        print(loc_samara, loc_tlt)


        # делаем папку для вывода
        dir_out = 'c:\СТРОЧКИ'
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)
        query = self.con.cursor()

        # Удаляем дубли по: профессии, контактному лицу, телефону.
        query.execute("DELETE FROM vacant WHERE ROWID NOT IN ("
            "SELECT MIN(ROWID) FROM vacant GROUP BY prof, face, phone);")

        # Удаляем без контактных данных.
        query.execute("DELETE FROM vacant WHERE (phone = '') AND (email = '');")

        # Бан по id организации
        # sql = ("DELETE FROM vacant WHERE ROWID IN "
                # "(SELECT v.ROWID FROM vacant as v, org_ban as o "
                # "WHERE v.id_org=o.id_org);")
        # query.execute(sql)

        # ВЫГРУЗКА ПО НОМЕРАМ РУБРИКАМ
        for key in rub_dict:

            # Если в рубрике нет вакансий, то переходим к следующей.
            query.execute("SELECT count(*) FROM vacant WHERE rubr LIKE '{}%';"
                .format(key))
            rec = query.fetchone()
            count = rec[0]
            print('Рубрика', key, 'Вакансий', count)
            if count == 0:
                continue

            # return # ЗАТЫЧКА


            # формируем названия файлов для вывода
            file_samara = '{}\\Самара {}{}.txt'.format(dir_out, key, rub_dict[key])# название файла содержит: город и название рубрики
            f_samara = open(file_samara,'w', encoding='utf16')                  #  вывод в кодировке UTF-16 (для InDesign)

            file_tlt = '{}\\Тольятти {}{}.txt'.format(dir_out, key, rub_dict[key])
            f_tlt = open(file_tlt,'w', encoding='utf16')

            # Шапка - общее описание стилей.
            # f_out.write("""<UNICODE-WIN>
            title = """<UNICODE-WIN>
<Version:5><FeatureSet:InDesign-Roman><ColorTable:=<Black:COLOR:CMYK:Process:0,0,0,1>>
<DefineParaStyle:00 RUB\_SUPER=<Nextstyle:00 RUB\_SUPER><cTypeface:Bold><cSize:24.000000><cCase:All Caps><pHyphenationLadderLimit:0><cLeading:22.000000><pHyphenation:0><pHyphenationZone:14.149999><pSpaceAfter:2.849999><pTabRuler:28.350000381469727\,Left\,.\,0\,\;><cFont:Abbat><pDesiredWordSpace:0.900000><pMaxWordSpace:1.000000><pMinWordSpace:0.700000><pDesiredLetterspace:0.050000><pMaxLetterspace:0.300000><pMinLetterspace:-0.050000><pMinGlyphScale:0.500000><pKeepFirstNLines:1><pKeepLastNLines:1><pRuleAboveColor:None><pRuleAboveStroke:0.000000><pRuleAboveTint:100.000000><pRuleAboveOffset:16.700000><pRuleAboveRightIndent:337.299987><pRuleBelowColor:Black><pRuleBelowStroke:0.007812><pRuleBelowTint:100.000000><pRuleBelowOffset:1.142187><pRuleBelowRightIndent:337.299987><pRuleAboveOn:1><pTextAlignment:Center>>
<DefineParaStyle:03 STR VAKANS=<Nextstyle:03 STR VAKANS><cTypeface:Black><cSize:6.500000><cHorizontalScale:0.900000><pHyphenationLadderLimit:0><pAutoLeadPercent:1.800000><cLeading:6.500000><pHyphenation:0><pHyphenationZone:34.000000><pSpaceBefore:1.399999><pSpaceAfter:1.399999><pTabRuler:177.14999389648438\,Right\,.\,0\,\;><cFont:GoodPro><pDesiredWordSpace:0.900000><pMaxWordSpace:1.000000><pDesiredLetterspace:0.050000><pMaxLetterspace:0.150000><pMinGlyphScale:0.500000><pKeepWithNext:1><pKeepFirstNLines:1><pKeepLastNLines:1><pRuleAboveColor:None><pRuleAboveStroke:0.000000><pRuleAboveTint:100.000000><pRuleAboveOffset:5.650000><pRuleBelowColor:Black><pRuleBelowStroke:0.300000><pRuleBelowTint:30.000000><pRuleBelowOffset:1.699999><pRuleBelowOn:1>>
<DefineParaStyle:03 STR\_TEXT bold=<Nextstyle:03 STR\_TEXT bold><cTypeface:Book><cSize:6.300000><cLeading:6.615000><cFont:GoodPro><pMinGlyphScale:0.500000>>
<DefineParaStyle:03 STR\_TEXT=<Nextstyle:03 STR\_TEXT><cTypeface:Book><cSize:6.300000><pHyphenationLadderLimit:0><pAutoLeadPercent:1.800000><cLeading:6.500000><pHyphenationZone:11.350000><pTabRuler:161.5500030517578\,Center\,.\,0\,\;><cFont:GoodPro><pMaxWordSpace:1.200000><pMaxLetterspace:0.150000><pMinLetterspace:-0.150000><pMinGlyphScale:0.500000><pKeepFirstNLines:1><pKeepLastNLines:1><pRuleAboveColor:Black><pRuleAboveStroke:0.300000><pRuleAboveTint:30.000000><pRuleAboveOffset:4.250000><pRuleBelowColor:Black><pRuleBelowStroke:0.250000><pRuleBelowTint:100.000000><pTextAlignment:JustifyLeft>>"""
            f_samara.write(title)
            f_tlt.write(title)

            # взять все вакансии текущей рубрики
            query.execute("SELECT prof, needs, salary, phone, email, face, region "
                "FROM vacant WHERE rubr LIKE '{}%' ORDER BY prof;".format(key))

            for val in query:                                                   # по всем записям

                # ДИНАМИЧЕСКОЕ ИЗМЕНЕНИЕ ИНФОРМАЦИИ
                """ Договорную зарплату сокращаем до "дог.". """
                salary = val[2].replace("договорная", "дог.")
                """Если нет телефона, то выводим электронную почту.  """
                contact = ''
                if val[3] != '':
                    contact = 'Тел. ' +  val[3]
                else:
                    contact = 'E-mail: ' +  val[4]
                """ Контактное лицо выводим в скобках."""
                face = ''
                if val[5] != '':
                    face = '({})'.format(val[5])

                    rec = ('<ParaStyle:03 STR VAKANS><cTracking:1><cCase:All Caps>{} '
                        '<cTracking:><cCase:><cTypeface:Regular><cTracking:1><cCase:All Caps><cPosition:Superscript>	<cTypeface:><cTracking:><cCase:><cPosition:><cTracking:1>{}\n'
                        '<cTracking:><ParaStyle:03 STR\_TEXT><cTypeface:Regular>{} {} {}<cTypeface:><cTypeface:Regular><cSize:12.300000><cBaselineShift:-5.000000> *\n'
                        '<cTypeface:><cSize:><cBaselineShift:><ParaStyle:03 STR\_TEXT><cTypeface:Regular><cSize:12.300000><cBaselineShift:-5.000000>\n<cTypeface:><cSize:><cBaselineShift:>'
                        .format(val[0], salary, val[1], contact, face))

                    # проверяем регион к которому относится вакансия
                    region_vacant = val[6].split(',')
                    print('Регионы',region_vacant)
                    sam = list(set(loc_samara) & set(region_vacant))
                    print('Совпало',sam)
                    if sam:
                        f_samara.write(rec)
                    tlt = list(set(loc_tlt) & set(region_vacant))
                    print('Совпало',tlt)
                    if tlt:
                        f_tlt.write(rec)
            # f_samara.write(str(i))                        # записываю счетчик чтобы не считать вакансии
            f_samara.close
            # f_tlt.write(str(i))                        # записываю счетчик чтобы не считать вакансии
            f_tlt.close
            print('записали')

        # БЕЗ РУБРИКИ
        filname = '{}\\ПРОФЕССИИ БЕЗ РУБРИКИ.txt'.format(dir_out)
        f_out = open(filname,'w')
        query.execute("SELECT prof FROM vacant WHERE rubr = 0 ORDER BY prof;")
        for val in query:
            f_out.write('{}\n'.format(val['prof']))

        f_out.close

        query.close
        self.message.setText('ВЫГРУЗКА ОК')


    def end(self):
        """
        Закрыть программу.
        """

        self.con.close()
        quit()


    def closeEvent(self,e):

        """ НАЖАТА СИСТЕМНАЯ КНОПКА <ЗАКРЫТЬ ФОРМУ>  ."""

        self.accept()


if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ
    main()
