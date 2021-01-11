# ------------------------------------------------------------------------
# Выкладка вакансий из админки rabota.ru в строчные объявления в газету
# На новом движке QWebEngine. Установка 
# pip install PyQt5
# pip install PyQtWebEngine
# ------------------------------------------------------------------------

import sys, logging, configparser, re, sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from bs4 import BeautifulSoup

# from datetime import date

# ШАБЛОНЫ

pattern_teg = re.compile(r'<.*?>')                                              # 'r' (в любом регистре) механизм экранирования отключается.

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


def main():

    global rubrics
    global mobil_moscau




    app = QApplication(sys.argv)
    app.setStyleSheet(open('pack/style.qss', 'r').read())

    logging.basicConfig(filename='log.txt',level=logging.DEBUG, # стандартный лог
        format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s %(message)s')
    
    window = MainWindow()                                                       
    sys.exit(app.exec())                                                       # exec_() для строго python


class MainWindow(QDialog):

    # ГЛАВНОЕ ОКНО -------------------------------------------------------------
    
    toHtmlFinished = pyqtSignal()
   
    def __init__(self, parent=None):      # self - указатель на себя. Все что нужно сохранить пишем в self

        super().__init__()                                                      # запускаем init родительского класса

        self.create_env() # создание рабочего окружения
        self.create_ui() # ui - user interface


    def create_env(self):

        
        # ищем путь к рабочему столу в реестре. Если на стол нужно файлы писать.
        import winreg
        
        REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, "Desktop")
        self.desktop = value


        # self.file_out = 'spider.csv'
        # self.file_log = 'modules/file.log'


        # в файле конфигурации держим оперативные настройки ?????????????????
        # self.file_ini = 'tuning/system.ini'
        # config = configparser.ConfigParser()
        # config.read(self.file_ini)
        # basic = config['BASIC']
        # print(basic.get('request')) # строка запроса

        import json

        with open('tuning/config.json', 'r') as f:
            config = json.load(f)
            print(config['request'])

        #edit the data
        # config['key3'] = 'value3'



        # config = {'key1': 'value1', 'key2': 'value2'}

        # with open('config.json', 'w') as f:
            # json.dump(config, f)




        # создание БД
        self.file_db = 'pack/file.db'
        self.conn = sqlite3.connect(self.file_db)
        self.conn.row_factory = sqlite3.Row                                     # для доступа по имени и индексу столбца
        query = self.conn.cursor()
        query.execute("CREATE TABLE IF NOT EXISTS vacant "
                "(rec_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,"
                "id_vacant TEXT DEFAULT '',"
                "id_user TEXT DEFAULT '', "
                "id_org TEXT DEFAULT '',"
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

        # -- Создаём словарь функций программы. Создаём модель для поля <функции>.

        self.phase_dict = {
            ' ВЫБРАТЬ ОПЕРАЦИЮ' : '',
            ' Загрузить вакансии' : 'self.load()',
            ' Удаление старых ссылок del_old_ref()' : 'self.del_old_ref()',
            ' Добавить ссылки в архив add_ref()' : 'self.add_ref()',
            ' Поиск организаций find_org()' : 'self.find_org()',
            ' Удаляем дубли и баним clean_org()' : 'self.clean_org()',
            ' Поиск www find_www()' : 'self.find_www()',
            ' Проверка по CRM find_CRM()' : 'self.find_CRM()',
            ' Вывод out()' : 'self.out()',
            }
        self.phase_model = QStringListModel(list(self.phase_dict.keys()))


    def create_ui(self):

        # создание пользовательского интерфейса
        # Два окна. слева будет мелькать загузка. справа будет бежать протокол работы
        # снизу будет протокол ошибок
        # кнопки будут по-верху. авторизации не будет. при необходимости можно кликнуть в окно.
        # одна кнопка старт, вторая выполнение по операциям (для отладки) 
        # после каждого нажатия окна логов очищаются

        start = QPushButton('СТАРТ')
        start.clicked.connect(self.start)
        
        debug = QPushButton('ОТЛАДКА')
        debug.clicked.connect(self.debug)
        
        self.phase = QComboBox()
        self.phase.setModel(self.phase_model)

        hbox_button = QHBoxLayout() # горизонтальный бокс с кнопками
        hbox_button.addWidget(start)
        hbox_button.addWidget(debug)
        hbox_button.addWidget(self.phase)
        hbox_button.addStretch()

        self.web_view = QWebEngineView()
        
        #self.web_view.load(QUrl("https://mail.ru")) # логин: samara пароль: Xahth8io
        self.web_view.load(QUrl("https://www.rabota.ru/admin")) # логин: samara пароль: Xahth8io
        #self.web_view.load(QUrl("https://rabota.ru/admin/")) # логин: samara пароль: Xahth8io
        self.message = QTextEdit()
        self.error = QTextEdit()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_button)
        vbox.addWidget(self.web_view, 3) # 3 - коэффициент растяжения
        vbox.addWidget(self.message,2)
        vbox.addWidget(self.error,1)

        self.setLayout(vbox)
        self.setWindowTitle('ГРАБИМ админку RABOTA.RU')
        self.setWindowIcon(QIcon('pack/spider.svg'))
        self.resize(1000, 600)
        self.show()


    def start(self):
    
        # ПОЛНЫЙ ЦИКЛ РАБОТЫ -------------------------------------------------------------------
        # -- Выполняем все команды из массива full_cycle."""
        
        # открыть страницу с вакансиями
        # прочитать всю информацию (она в ней)
        # записать в базу данных

        # self.web_view.load(QUrl("https://mail.ru")) # логин: samara пароль: Xahth8io
        # self.find_ref()     # собрать все ссылки
        # self.del_old_ref()  # удалить старые ссылки
        # self.add_ref()      # добавить новые в архив ссылок
        # self.find_org()     # загрузить описание вакансий по ссылкам
        # self.clean_org()    # очистить от "грязи"
        # self.clean_org()    # очистить от "грязи"
        # self.find_www()     # поиск названия сайта
        # self.out()          # вывод результатов
        # quit()              # закончить работу
        return


    def debug(self):
    
        # Выполняем выбранную операцию


        exec(self.phase_dict[self.phase.currentText()])
        self.phase.setCurrentIndex(0)


    def load(self):
    
        # проверка работы
        # self.web_view.load(QUrl()) # логин: samara пароль: Xahth8io
        # print('011')

        # self.web_view.load(QUrl("https://www.rabota.ru/admin")) # логин: samara пароль: Xahth8io
        # #self.web_view.load(QUrl("https://www.rabota.ru/admin/index.php?area=v3_base&action=search&start%5Bday%5D=25&start%5Bmonth%5D=1&start%5Byear%5D=2019&end%5Bday%5D=8&end%5Bmonth%5D=2&end%5Byear%5D=2019&sort=salary_asc&per_page=50&sourceAll=on&type=1&filter=nospam&so=f&ch=t&pub=t&se=t&wa=f&is_all_rubric=on&is_all_city=on&offset=0"))
        print('012')
        self.get_html("https://www.rabota.ru/admin/index.php?area=v3_base&action=search&start%5Bday%5D=25&start%5Bmonth%5D=1&start%5Byear%5D=2019&end%5Bday%5D=8&end%5Bmonth%5D=2&end%5Byear%5D=2019&sort=salary_asc&per_page=50&sourceAll=on&type=1&filter=nospam&so=f&ch=t&pub=t&se=t&wa=f&is_all_rubric=on&is_all_city=on&offset=0")
        print('013')
        # ждать
        loop = QEventLoop()
        self.toHtmlFinished.connect(loop.quit)
        loop.exec_()
        print('все загрузилось')
        soup = BeautifulSoup(self.html, 'html.parser') # грузим дерево
        h2 = soup.find_all('id_предложения')
        print (h2)
        # print('014')
        # собираем всю информацию по вакансиям
        # читаем в цикле страницы
        # while 1:
            # # загружаем
            # self.web_view.load(QUrl("https://rabota.ru/admin/")) # логин: samara пароль: Xahth8io
            # self.get_html()
            # print (self.html)
            # # html пишем в файл, чтобы при вылете остался код для анализа
            
            # # ff = open('modules/html.txt', 'w',encoding='utf-8')
            # # ff.write(html)
            # # ff.close()


            # # парсим
            # # проверяем наличие вакансий
            # if 
            # # если пустое множество
            # else:                                                               # Вакансий больше нет,
                # break                                                           # поэтому выходим из бесконечного цикла.


    def store_html(self, html):
        self.html = html # сохраняем html код
        # print(self.html)
        self.toHtmlFinished.emit() # посылаем сигнал, чтобы завершить loop цикл



    def _on_load_finished(self):
        
        print('_on_load_finished')
        self.current_page.toHtml(self.store_html)
        print('_on_load_finished')
        

    def get_html(self,url):
        
        self.current_page = self.web_view.page()
        print('---')
        self.current_page.loadFinished.connect(self._on_load_finished)
        print('--')
        self.current_page.load(QUrl(url))
        print('-')

        # toHtml выполняется асинхронно. После успешного завершения вызывается
        # функция. В эту функцию передается html код.
        # current_page.toHtml(self.store_html) 

        # QEventLoop класс для входа и выхода из цикла событий.
        # Вызвается exec() для запуска локального цикл обработки событий.
        # quit() срубает цикл и продолжает выполнение кода.
        # Циклим пока не появится сигнал от toHtmlFinished.
        #print('loop')
        #loop = QEventLoop()
        #self.toHtmlFinished.connect(loop.quit)
        #loop.exec()
        

        #print(len(self.html))
        # bs = BeautifulSoup(self.html, 'html.parser')
        # #nameList = bs.find_all('span')
        # print('тест')
        # nameList = bs.find_all('a', {'href':re.compile('/vacancy/card*')})
# #        nameList = bs.find_all('a')
        # print('прошли')
        # for name in nameList:
            # print(name['href'])
        

    def _load(self):

        # --------- Собирает ссылки с сайта
        # Собирает ссылки на вакансии с сайта и вставляет в таблицу vacant.

        stat_moscau = ['495', '499', '496', '498']                              # номера московских телефонов

        def phone_moscau(phones):

            # --------- ????????????????????????????

            phones = ''.join(filter(lambda x: x.isalnum() or x == ',', phones)) # оставляем буквы, цыфры, запятые
            phones = phones.strip(',').split(',')                               # убрать последнюю запятую и создать список

            for i, phone in enumerate(phones):                                  # пошли по списку телефонов
                p = phone.find('до')                                            # если есть слова "доп.", "доб." и т.д.
                if p != -1:                                                     # убираем
                    phone = phone[:p]
                if len(phone)>=11:                                              # убрать код страны (урезать до 10 цифр)
                    phone = phone[1:]
                if phone[:3] in stat_moscau:                                    # стационарный московский ?
                    return(1)                                                   # да
                for mobil in mobil_moscau:
                    if  mobil[0] <= phone <= mobil[1]:                          # мобильный московский ?
                        return(1)                                               # да
            return(0)                                                           # не московский телефон


        def separation_needs(descript):

            # --------- Выделение требований из описания вакансии.

            if not descript:                                                    # Нет исходных данных.
                return ''

            match = pattern_needs.search(descript)                              # Ищем раздел "Требования" в описании вакансии
            if match:
                needs = match.group(2)
            else:
                return ''

            needs = needs.replace("\n"," ")                                     # Удалем из html кода переносы строк.
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


        query = self.conn.cursor()

        # Читаем словарь рубрик. Формат строки: регулярное выражение$номер рубрики.
        # (М|м)едицин$211
        # (М|м)енеджер$261
        # (П|п)екар$231

        # Читаем словарь и сортируем по длинне регулярного выражения в обратном порядке

        with open("tuning/rubric_dict.txt",'r') as file:
            line = file.readlines()                                             # file.readlines()  -> list
        sort_list = sorted(line, key=len, reverse=True)                         # key=len функция сортировки

        # Создаём список: [[патерн, рубрика], ...]  """

        pattern_dict = re.compile(r'(.*)\$(.*)')
        rubrics = []
        for line in sort_list:
            me = pattern_dict.search(line)
            if me:
                try:
                    rubrics.append([re.compile(me.group(1)),me.group(2)])
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
        # print(rubrics[2])

        # ЧИТАЕМ МАССИВ МОСКОВСКИХ ТЕЛЕФОНОВ
        """ Формат строки: от номера$до номера."""
        pattern_dict = re.compile(r'(.*)\$(.*)')
        mobil_moscau = []
        with open("tuning/mobil_moscau.txt",'r') as f_in:
            for sline in f_in:
                me = pattern_dict.search(sline)
                if me:
                    mobil_moscau.append([me.group(1),me.group(2)])
                else:
                    logging.error('Ошибка списка телефонов: {}'.format(sline))
                    btn_quit_click()

        
        # РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ -------------------------------------------------
        
        pattern_page = re.compile(
            'Результаты поиска вакансий \(([\d]+?)-([\d]+?) ')                  # Интервал номеров вакансий
        pattern_id_vacant = re.compile('id_предложения ([\d]+?),')              # id вакансии
        pattern_id_user = re.compile('id_пользователя ([\d]+?),')               # id работодателя
        pattern_id_region = re.compile(
            'Регионы размещения:.+\n.+\n[\t]+([^\t]+)')          # регион размещения
        pattern_prof = re.compile('\n\t+?([ \S]+?)\t+?([ \S]+?)\t+?')           # профессия
        pattern_face = re.compile(
            '<b>Работодатель:</b></td><td width="80%">([ \S]+?)\t')             # контактное лицо
        pattern_org = re.compile(
            '<div class="VacancyView_location">'
            '(.+?)<span class="h_color_gray VacancyView_town">',re.S)           # название компании
        pattern_org2 = re.compile('>(.+?)<')                                    # организация внутри html ссылки
        pattern_phone = re.compile(
        'class="phoneItem">(.+?)E-mail:</b></td>',re.S)                         # телефон
        pattern_email = re.compile('E-mail:</b></td>.+?>(.+?)<',re.S)           # E-mail
        pattern_descript = re.compile(
            '<b>Образование:</b>(.+?)<b>Платная модель:</b>',re.S)              # требования
        # pattern_needs = re.compile('(ребования:|ребование:)(.+?)</ul>',re.S)                          # требования
        pattern_needs = re.compile(
            '(ребования:|ребование:)(.+?)(</ul>|</tr>)',re.S)                   # требования
        pattern_watch = re.compile('(вахт|Вахт)(.+?)(</ul>|</tr>)',re.S)        # вахта
        pattern_punct_end = re.compile('^\W*?(\w.+?)\W*?$')                     # пунтуация в конце предложения.


        # РАБОЧИЙ ЦИКЛ ---------------------------------------------------------

        query.executescript("DELETE FROM vacant; VACUUM;") # очистка таблицы вакансий

        # ЧТЕНИЕ ВАКАНСИЙ (цикл по всем страницам)
        # В "админке" позиционирование происходит по смещению от начала списка.
        # В отладочном начально смещение делаем близко к посленей вакании.
        # Делаем бесконечный цикл. Выдем по break.

        web = WebManager()
        cookies = QNetworkCookieJar()
        self.cookie_load(cookies, 'modules/cookies.txt')
        web.manager.setCookieJar(cookies)

        offset = 0
        while 1:

            # ЗАГРУЗКА СТРАНИЦЫ
            # Формируем URL. Показываем в текстовом поле для контроля. Грузим.

            self.message.setText('Вакансий: {}'.format(offset))
            url = self.request.toPlainText().format(offset)

            web.get(url) # загрузка html страницы
            html = web.html

            # html пишем в файл, чтобы при вылете остался код для анализа
            
            ff = open('modules/html.txt', 'w',encoding='utf-8')
            ff.write(html)
            ff.close()


            if pattern_id_vacant.search(html): # tckb 'id_предложения' найдено? то ещё есть вакансии

                # ПОИСК ГРАНИЦ ВАКАНСИЙ --------------------------------------------------

                # Генераторы списков записываются в квадратных скобках, потому что это,
                # в конечном счете, способ создания нового списка.
                # метод finditer находит все объекты совпадения (Match) для оператора for
                # каждый объект иметт метод start индекс начала подстроки
                # Результат - список позиций начал вакансий (pos).
                
                pos = [m.start() for m in re.finditer("id_предложения", html)] 
                pos.append(len(html) - 1) # добавить нижнюю границу последней вакансии

                
                for i in range(len(pos)-1): # теперь можно работать в пределах описания одной вакансии

                    # id вакансии
                    match = pattern_id_vacant.search(html, pos[i], pos[i+1])
                    if not match:
                        logging.critical('Не найден id вакансии')
                        QMessageBox.critical(None, "ОШИБКА ПАРСИНГА", "Невозможно продолжить работу. Нужен программист.")
                        sys.exit()
                    id_vacant = match.group(1).strip()
                    print('id вакансии {}'.format(id_vacant))


                    # id работодателя
                    match = pattern_id_user.search(html, pos[i], pos[i+1])
                    if not match:
                        logging.critical('Не найден id работодателя')
                        QMessageBox.critical(None, "ОШИБКА ПАРСИНГА", "Невозможно продолжить работу. Нужен программист.")
                        sys.exit()
                    id_user = match.group(1).strip()
                    print('id работодателя {}'.format(id_user))


					# !!!!!!!!по id клиента ищем id организации (!!!!откуда взялась таблица)!!!!!!!!!!!!
                    query.execute("SELECT id_org FROM user_org "
                            "WHERE id_user = '{}';".format(id_user))
                    rec = query.fetchone()
                    id_org = ''
                    if rec:
                        id_org = rec[0]


                    # Регион размещения
                    match = pattern_id_region.search(html, pos[i], pos[i+1])
                    if not match:
                        logging.error('Не найден Регион размещения')
                        continue
                    region = match.group(1).strip()
                    print('Регион размещения {}'.format(region))


                    # профессия
                    # модифицируем для правильного поиска рубрик
                    match = pattern_prof.search(html, pos[i], pos[i+1])
                    if not match:
                        logging.error('не найдена профессия')
                        continue
                    prof = match.group(1).strip() # удаляем пробелы вокруг
                    for code in codes_spec: # Заменяем спецсимволы html
                        prof = prof.replace(code,codes_spec[code]) 
                    prof = prof.replace("\\", "/") # Заменяем обраный слешь на прямой
                    prof = prof.replace("\'", "")
                    prof = prof[0:1].upper() + prof[1:] # Делаем профессию с заглавной буквы
                    print('профессия {}'.format(prof))

                    # зарплата
                    salary = match.group(2).strip()

                    # ПРИСВАИВАЕМ РУБРИКУ (по названию професии)
                    # Итерация списка рубрик. Каждый элемент списка - массив двух элементов:
                    # ссылка на откомпилированное регулярное выражение и номер рубрики.
                    # Ищем регулярное выражение в названии профессии. Если найдено, то
                    # присваиваем рубрику и заканчиваем поиск.

                    rubr = 0
                    for index, rubric in enumerate(rubrics):
                        if rubric[0].search(prof):
                            rubr = rubric[1]
                            debug = index + 1
                            break

                    # КОНТАКТНОЕ ЛИЦО.
                    # Звездочки, пропущеные имя, фамилия или отчество обрезаем.

                    face = ''
                    match = pattern_face.search(html, pos[i], pos[i+1])
                    if match:
                        face = match.group(1).strip('*')

                    # ТЕЛЕФОН.
                    # Если номеров несколько, то внутри строки попадаются html теги
                    # и непечатные символы. Теги убираем с помощью регулярнных выражений.
                    # Непечатные символы удаляем по коду. Пробелы оставляем.
                    # Если встречаются московские телефоны, изменяем рубрику на
                    # "РАБОТА В МОСКВЕ"

                    phone = ''
                    match = pattern_phone.search(html, pos[i], pos[i+1])
                    if match:
                        phone = pattern_teg.sub('', match.group(1))
                        phone = ''.join(c for c in phone if ord(c) > 31)
                        if phone_moscau(phone):
                            rubr = 900

                    # ЭЛЕКТРОННАЯ ПОЧТА.

                    email = ''
                    match = pattern_email.search(html, pos[i], pos[i+1])
                    if match:
                        email = match.group(1)

                    # ОПИСАНИЕ ВАКАНСИИ
                    # Вытаскиваем полное описание вакансии. Если встречается слово
                    # 'вахта', то изменяем рубрику на "РАБОТА ВАХТОВЫМ МЕТОДОМ"

                    descript = ''
                    match = pattern_descript.search(html, pos[i], pos[i+1])
                    descript = match.group(1)
                    descript = ''.join(c for c in descript if ord(c) >= 32)     # удаляем непечатные символы
                    descript = descript.replace("\'", "")
                    if (prof.lower().find('вахт') != -1) or \
                        (descript.lower().find('вахт') != -1):
                        rubr = 500

                    # ТРЕБОВАНИЯ (см. функцию)

                    needs = separation_needs(descript)

                    # ЗАПИСЬ ВБД
                    # Ошибка в процесс записи считаем фатальной.

                    sql = ("INSERT INTO vacant (id_vacant, id_user, id_org, region, "
                        "rubr, prof, salary, face, phone, email, descript, needs)"
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?);")
                    param = (id_vacant, id_user, id_org, region, rubr, prof, salary, face,
                        phone, email, descript, needs)
                    try:
                        query.execute(sql, param)
                    except sqlite3.Error as e:
                        logging.critical('Ошибка записи в базу данных: {} {}'.
                            format( e.args[0],sql))
                        QMessageBox.critical(None, "ОШИБКА БАЗЫ ДАННЫХ", "Невозможно продолжить работу. Нужен программист.")
                        sys.exit()
                        # btn_quit_click()
            else:                                                               # Вакансий больше нет,
                break                                                           # поэтому выходим из бесконечного цикла.
            offset += 50                                                        # Смещаемся на следующие 50 вакансий.

        query.close()
        self.org_id()
        self.message.setText('ОКОНЧАНИЕ ПАРСИНГА')


    def org_id(self):

        # ---------- ПОИСК ID КОМПАНИИ
        # Шаблон для поиска. Курсоры для чтения и записи.
        # Только для организаций без ID. В каждой записи читаем id пользователя.
        # Загружаем страницу [Информация о пользователе]
        # Ищем id компании и пишем в таблицу. """

        web = WebManager()
        cookies = QNetworkCookieJar()
        self.cookie_load(cookies, 'modules/cookies.txt')
        web.manager.setCookieJar(cookies)

        pattern_id_org = re.compile('company_id=([\d]+?)</a>')
        select = self.conn.cursor()
        update = self.conn.cursor()

        select.execute("SELECT ROWID, id_user FROM vacant WHERE id_org = '';")
        for ROWID, id_user in select:

            self.message.setText('Юзер: {}'.format(id_user))
            url = ('https://www.rabota.ru/admin/?area=v3_editPerson&id={}'.format(id_user))
            web.get(url)
            html = web.html

            m = pattern_id_org.search(html)
            if not m:
                logging.error('Не найден ID [{}]'.format(html))
                QMessageBox.critical(None, "ОШИБКА ПОИСКА ID КОМПАНИИ", "Повторить поиск.")
                return
            id_org = m.group(1)
            sql = ("UPDATE vacant SET id_org = '{}' WHERE ROWID = {}".
                format(id_org, ROWID))
            try:
                update.execute(sql)
            except sqlite3.Error as e:
                logging.error('btn_load_vacant_click: {} {}'.format( e.args[0],sql))
                QMessageBox.critical(None, "КРИТИЧЕСКАЯ ОШИБКА", "Подробности в файле log.txt.")
                quit()

            sql = ("INSERT INTO user_org (id_user, id_org)"
                    "VALUES ('{}','{}')".format(id_user, id_org))
            try:
                update.execute(sql)
            except sqlite3.Error as e:
                logging.error('btn_load_vacant_click: {} {}'.format( e.args[0],sql))
                QMessageBox.critical(None, "КРИТИЧЕСКАЯ ОШИБКА", "Подробности в файле log.txt.")
                quit()

        update.execute("DELETE FROM user_org WHERE ROWID NOT IN ("
            "SELECT MIN(ROWID) FROM user_org GROUP BY id_user, id_org);")
        select.close()
        update.close()
        self.message.setText('ОРГАНИЗАЦИИ ОК')


    def unload(self):

        # необходимо выводить в два файла в тольяттински и самарский


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

        f_locality = open('locality.txt', 'r',encoding='utf-8')
        loc_samara = f_locality.readline().split(',')
        loc_tlt = f_locality.readline().split(',')
        print(loc_samara, loc_tlt)

        #dir_out = self.dir_out + '\\' + self.sity.currentText()
        dir_out = 'c:\СТРОЧКИ'
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)

        query = self.conn.cursor()

        # Удаляем дубли по: профессии, контактному лицу, телефону.
        query.execute("DELETE FROM vacant WHERE ROWID NOT IN ("
            "SELECT MIN(ROWID) FROM vacant GROUP BY prof, face, phone);")

        # Удаляем без контактных данных.
        query.execute("DELETE FROM vacant WHERE (phone = '') AND (email = '');")

        # Бан по id организации
        sql = ("DELETE FROM vacant WHERE ROWID IN "
                "(SELECT v.ROWID FROM vacant as v, org_ban as o "
                "WHERE v.id_org=o.id_org);")
        query.execute(sql)

        # ВЫГРУЗКА ПО НОМЕРАМ РУБРИКАМ
        for key in rub_dict:

            # Если в рубрике нет вакансий, то переходим к следующей.
            query.execute("SELECT count(*) FROM vacant WHERE rubr LIKE '{}%';"
                .format(key))
            rec = query.fetchone()
            count = rec[0]
            if count == 0:
                continue



            # filname = '{}\\{} {}.txt'.format(dir_out,
                # self.sity.currentText(), rub_dict[key])
            # f_out = open(filname,'w', encoding='utf16')
            file_samara = '{}\\Самара {}.txt'.format(dir_out, rub_dict[key])    # название файла содержит: город и название рубрики
            f_samara = open(file_samara,'w', encoding='utf16')                  #  вывод в кодировке UTF-16 (для InDesign)
            file_tlt = '{}\\Тольятти {}.txt'.format(dir_out, rub_dict[key])
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

            query.execute("SELECT prof, needs, salary, phone, email, face, region "
                "FROM vacant WHERE rubr LIKE '{}%' ORDER BY prof;".format(key))

            for val in query:                                                   # по всем записям


                # ДИНАМИЧЕСКОЕ ИЗМЕНЕНИЕ ИНФОРМАЦИИ
                # """ Договорную зарплату сокращаем до "дог.". """
                salary = val[2].replace("договорная", "дог.")
                # """Если нет телефона, то выводим электронную почту.  """
                contact = ''
                if val[3] != '':
                    contact = 'Тел. ' +  val[3]
                else:
                    contact = 'E-mail: ' +  val[4]
                # """ Контактное лицо выводим в скобках."""
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
                    sam = list(set(loc_samara) & set(region_vacant))
                    if sam:
                        f_samara.write(rec)
                    tlt = list(set(loc_tlt) & set(region_vacant))
                    if tlt:
                        f_tlt.write(rec)
            f_samara.close
            f_tlt.close

        # БЕЗ РУБРИКИ
        filname = '{}\\{} ПРОФЕССИИ БЕЗ РУБРИКИ.txt'.format(dir_out, self.sity.currentText())
        f_out = open(filname,'w')
        query.execute("SELECT prof FROM vacant WHERE rubr = 0 ORDER BY prof;")
        for val in query:
            #print(val['prof'])
            f_out.write('{}\n'.format(val['prof']))
        f_out.close

        query.close
        self.message.setText('ВЫГРУЗКА ОК')


    def end(self):
        """
        Закрыть программу.
        """

        self.conn.close()
        quit()


class FormLogin(QDialog):

    # форма чтобы залогонится.
    # web компонент в переменной web

    def __init__(self, parent):
        super().__init__()                                                      # вызвать одноименный метод из базового класса QDialog

        self.web = QWebView()                                                   # виджет окна браузера
        vbox = QVBoxLayout()                                                    # вертикальный контейнер
        vbox.addWidget(self.web)                                                # добавляем в контейнер виджет окна браузера
        # vbox.addStretch()

        self.setLayout(vbox)                                                    # размещаем контейнер в окне
        self.setWindowModality(1)                                               # окно должно быть модальным
        self.setWindowTitle('АВТОРИЗАЦИЯ')                                      # заголовок
        self.show()                                                             # отображаем окно

    # def get(self):

        # self.web.page().networkAccessManager().setCookieJar(self.cookies)
        # self.web.load(QUrl(self.url))


    def closeEvent(self,e):

        """ НАЖАТА СИСТЕМНАЯ КНОПКА <ЗАКРЫТЬ ФОРМУ>  ."""

        self.accept()

class WebManager():

    # Класс для загрузки старниц без отображения окна браузера

    def __init__(self):

        self.manager = QNetworkAccessManager()


    def get(self, url):

        """ ЗАПРОС
        --- Создаем QNAM. Создаем хранилище куков. Подсоединяем к QNAM."""

        request = QNetworkRequest()
        request.setUrl(QUrl(url))
        request.setRawHeader(b"User-Agent", b"MyOwnBrowser 1.0")
        loop = QEventLoop()
        self.manager.finished.connect(loop.quit)
        reply = self.manager.get(request);
        loop.exec_()
        f =  bytes(reply.readAll())
        self.html = f.decode(encoding="utf-8", errors="strict")



if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ
    main()
