# ---------------------------------------------------------------------
# Парсинг вакансий https://www.google.ru/maps
# ---------------------------------------------------------------------

# import os
import sys
import locale
# import datetime
# import sqlite3
# import re
# from lxml import etree
# MySQL
import mysql.connector

# selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
# from selenium.common.exceptions import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from time import sleep

# from openpyxl import Workbook


# release = '(1.01)'


# # import pickle


def main():

    # чистим базу данных
    # Запускаем карты
    # ищем поле поиска
    # вводим в поле название компаеии
    # запускаем поиск
    # проверяем что найдено
    # проверяем что есть отзыви
    # сортируем по самым лучшим
    # до тех пор пока не кончатся или не будет 20 штук
    # ищем очередной если не найден то конец
    # читаем. пишем в базу MySQL
    # всё

    # чистим базу данных
    # база данных на соседнем сервере MySQL
    # пока ни одной таблицы нет
    config = {
        'user': 'usa',
        'password': 'usa',
        'host': '192.168.2.201',
        'database': 'usa',
        'raise_on_warnings': True
    }

    cnx = mysql.connector.connect(**config)

    curA = cnx.cursor(buffered=True)

    # query = ("DROP TABLE IF EXISTS reviews;")
    # curA.execute(query)
    # cnx.commit()
    # query = ("CREATE TABLE IF NOT EXISTS reviews ("
    #             "rec_id INT UNSIGNED NOT NULL AUTO_INCREMENT,"
    #             "ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
    #             "star INT DEFAULT 0,"
    #             "men VARCHAR(256) DEFAULT '',"
    #             "content VARCHAR(256) DEFAULT '',"
    #             "PRIMARY KEY (rec_id))"
    #         )
    # curA.execute(query)
    # cnx.commit()

    # cnx.close()
    # sys.exit()




        

    # --- настраиваем драйвер selenium ----------
    path_to_chromedriver = 'driver/chromedriver' 

    # для запуска без окна хрома
    chrome_options = Options()
#     # chrome_options.add_argument('--headless')
#     # chrome_options.add_argument('--no-sandbox')
#     # chrome_options.add_argument('--window-size=1920,1080')
#     # chrome_options.add_argument('--proxy-server="direct://"')
#     # chrome_options.add_argument('--proxy-bypass-list=*')
    driver = webdriver.Chrome(executable_path=path_to_chromedriver, options=chrome_options) 

    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
#     now = datetime.datetime.now()
#     date_now = now.strftime("%d %b")


    url = 'https://www.google.ru/maps/'
    driver.get(url)
    sleep(3)
    
    # ищем find_element_by_id ()<input id="searchboxinput"> 
    # находим и вводим название
    element = driver.find_element_by_id("searchboxinput").send_keys("Замок Гарибальди, Речной переулок, Хрящевка, Самарская область")
    sleep(5)

    # это кнопка поиска
    element = driver.find_element_by_id("searchbox-searchbutton").click()
    sleep(5)
    
    # здесь бы нужно проверить название организации и адрес и если они не найдены или не совопадают 
    # то заканчиваем и пишем сообщение куда пишем?

    # это уже рейтинг кнопка звездочки
    element = driver.find_element_by_class_name("widget-pane-link").click()
    sleep(5)

    # сортируем по самым лучшим
    # Ожидать не более 10 секунд, пока элемент не станет кликабельным. После этого кликнуть на него
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//div[@role='menu']"))).click()
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//li[@data-index='2']"))).click()

    # считаем что отзывы всегда есть. в крайняк можно хлолший отзыв записать

    # до тех пор пока не кончатся или не будет 20 штук
    # ищем очередной если не найден то конец
    # читаем. пишем в базу MySQL
    # всё
    sleep(5)
    # ищем очередной отзыв целиком если не найден то конец # class="section-review
    # секция с отзывами
    i = 0
    while True:

        # блоки отзывов
        reviews = driver.find_elements_by_class_name("section-review")

        # берем очередной отзыв
        star = reviews[i].find_elements_by_class_name("section-review-star-active")

        # проверяем звезды если меньше 4 звезд - на выход
        if (len(star) < 4 ): break

        # Имя чела
        men = reviews[i].find_element_by_class_name("section-review-title")

        # отзыв чела
        content = reviews[i].find_element_by_class_name("section-review-review-content")

        print (men.text)
        print (content.text)
        print(len(star))
        new = (
            "INSERT INTO reviews (star, men, content) "
            "VALUES (%s, %s, %s)")
        curA.execute(new,
                    (len(star), men.text, content.text))
        cnx.commit()
        # больше 10 отзывов не нужно
        if (i > 10): break

        # засвечиваем последнюю запись
        target = reviews[i+5]
        target.location_once_scrolled_into_view
        sleep(5)
        i=i+1
    cnx.close()
    driver.quit()
    sys.exit()
#             try:
#                 element = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'Дальше'))
#                 )
#             except:
#                 print("Кнопка не зпгрузилась")
#                 sys.exit()
#             finally:
#                 print("загрузка прошла")

        # class="section-expand-review
        # рейтинг если мень it 4-[ то конец]











#     new_window_url = driver.find_element_by_link_text(
#         "Вход").get_attribute("href")
#     driver.get(new_window_url)
#     sleep(3)
#     element = driver.find_element_by_class_name("input")
#     element.send_keys("rabotarutlt@gmail.com")
#     element = driver.find_element_by_class_name("input_1Um_6")
#     element.send_keys("m3X8P49T9f92DMWkJf5#")
#     element.submit()
#     sleep(3)


#     con.close()
    # driver.quit()


















#     def find_link():

#         # Функция чтения ссылок на описание вакансий с сата zarplata.ru
        
#         url = "https://tolyatti.zarplata.ru/vacancy"
#         driver.get(url)
#         while True:
#             # пока не появится кнопка 'Дальше'
#             try:
#                 element = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'Дальше'))
#                 )
#             except:
#                 print("Кнопка не зпгрузилась")
#                 sys.exit()
#             finally:
#                 print("загрузка прошла")

#             print(len(driver.find_elements_by_class_name('vacancy-title_1sIep')))

#             # читаем все ссылки на описание вакансий на странице и грузим в базу данных

#             for vacant in driver.find_elements_by_class_name('vacancy-title_1sIep'):
#                     link = vacant.get_attribute('href')
#                     # print(link)

#                     # записать в базу данных ссылки
#                     try:
#                         query.execute("INSERT INTO vacant (link) VALUES (?);", (link,))

#                     except sqlite3.Error as e:
#                         print(e.args[0])
#                         # logging.critical('btn_collect_ref_click: {} {}'.format( e.args[0],sql))

#                     con.commit()


#             # если link (кнопка с текстом "Дальше..." имеет класс disabled то выход

#             btn_next = driver.find_element_by_partial_link_text('Дальше')
#             vclass = btn_next.get_attribute("class")
#             print('+')
#             if vclass.find('disabled') == -1:
#             # нажимаем кнопку Дальше
#                 btn_next.click()
#             else:
#                 break




#         # driver.quit()
#         # sys.exit()


#     def find_info():

#         # Функция считывет информацию по каждой вакансии с сайта

#         # читаем линки из БД

#         query.execute("SELECT rec_id, link FROM vacant;")
#         rec_all = query.fetchall()
#         for rec in rec_all:

#             # загрузка страницы
#             url = rec['link']
#             driver.get(url)         

#             try:
#                 element = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'Пожаловаться'))
#                 )
#             except:
#                 print("Страница  не загрузилась")
#                 sys.exit()
#             finally:
#                 print("загрузка прошла")


#             # sleep(3)

#             # название вакансии единственный тег h1. Есть обязательно
#             element = driver.find_element_by_tag_name('h1') 
#             vacancy = element.text

#             print ('вакансия-'+vacancy)

#             # нужно поднятся на два ула вверх и упасть до второго линка. первый линк звезда.
#             parent = element.find_element_by_xpath("../..")
#             element = parent.find_element_by_tag_name('div h2 a')
#             company = element.text

#             # группа Контактная информация имеет внятное имя.
#             # Узел необязательный - если нет, то следующая вакансия
#             try:
#                 contact_info = driver.find_element_by_name('vacancy-contacts')
#             except NoSuchElementException:
#                 continue

#             # контактное лицо
#             try:
#                 element = contact_info.find_element_by_xpath("./div/div/div")
#                 face = element.text
#             except NoSuchElementException:
#                 face = 'нет данных'

#             # контактный телефон с кнопкой развертывания
#             try:
#                 btn = contact_info.find_element_by_css_selector("button")
#                 element_phone = btn.find_element_by_xpath('..')
#                 btn.click()
#                 phone = element_phone.text
#             except NoSuchElementException:
#                 phone = 'нет данных'
            
#             date = 'второй заход'

#             print(vacancy) # название вакансии
#             print(company) #  компания
#             print(phone) #  телефон
#             print(face) # контактное лицо
#             print(date) # дата возникновения?

#             sql = ("UPDATE vacant SET "
#                 "vacancy = '{}',"
#                 "company = '{}',"
#                 "phone = '{}',"
#                 "face = '{}',"
#                 "date = '{}' "
#                 "WHERE rec_id = {}"
#                 .format(vacancy, company, phone, face, date, rec['rec_id']))
#             query.execute(sql)
#             con.commit()


#     def write_excel():

#         # Записываем базу в екселевскую таблицу

#         query.execute("SELECT * FROM vacant;")
#         rec_all = query.fetchall()

#         # ◾◾◾ запись в файл excel

#         wb = Workbook()
#         ws = wb.active
#         ws.title = date_now

#         ws.cell(row=1, column=1).value = 'Ссылка на вакансию'
#         ws.cell(row=1, column=2).value = 'Вакансия'
#         ws.cell(row=1, column=3).value = 'Комания'
#         ws.cell(row=1, column=4).value = 'Телефон'
#         ws.cell(row=1, column=5).value = 'Когтактное лицо'
#         ws.cell(row=1, column=6).value = 'Дата вакансии'
#         i = 2
#         for rec in rec_all:
        
#             ws.cell(row=i, column=1).value = rec['link']
#             ws.cell(row=i, column=2).value = rec['vacancy']
#             ws.cell(row=i, column=3).value = rec['company']
#             ws.cell(row=i, column=4).value = rec['phone']
#             ws.cell(row=i, column=5).value = rec['face']
#             ws.cell(row=i, column=6).value = rec['date']
#             i += 1
        
#         file_xlsx = 'zarplata.xlsx'
#         wb.save(file_xlsx)



if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ
    main()
