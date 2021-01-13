# ---------------------------------------------------------------------
# Парсинг вакансий https://zarplata.ru/
# ---------------------------------------------------------------------

import os
import sys
import locale
import datetime
import sqlite3
import re
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
release = '(1.01)'


# import pickle


def main():

    now = datetime.datetime.now()

    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    date_now = now.strftime("%d %b")

    # создание папки
    db_dir = 'dbase'
    if not os.path.exists(db_dir):
        os.mkdir(db_dir)

    # создание базы данных SQLite
    db_sqlite3 = db_dir + '/db_sqlite3.db'
    con = sqlite3.connect(db_sqlite3)
    con.row_factory = sqlite3.Row                                               # для доступа к полям по имени
    query = con.cursor()
    query.execute("CREATE TABLE IF NOT EXISTS vacant "
                  "(rec_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,"
                  "link TEXT DEFAULT '',"
                  "vacancy TEXT DEFAULT '',"
                  "company TEXT DEFAULT '',"
                  "phone TEXT DEFAULT '',"
                  "face TEXT DEFAULT '', "
                  "date TEXT DEFAULT '');")
    # query.close()

    path_to_chromedriver = 'driver/chromedriver'                                # адрес WebDriver
    driver = webdriver.Chrome(executable_path=path_to_chromedriver)             # запуск WebDriver

    # загрузка страницы
    url = 'https://tolyatti.zarplata.ru/'
    driver.get(url)
    sleep(3)

    # Залогонимся на сайте, а то не видно будет ничего полезного
    # Находим кнопку Вход. У кнопки есть атрибут  href, по которому происходит переход на форму регистрации.
    # Грузим страницу входа (get) и ищем на странице поле логина (find_element_by_class_name).
    # Вводим текст (send_keys() в поле логина. Ищем поле ввода пароля (input_1Um_6).
    # Вводим туда пароль (send_keys(). Нажимаем кнопку отправить (submit).
    # Ждем секунды 3, пока куки не прогрузятся гарантированно.

    new_window_url = driver.find_element_by_link_text(
        "Вход").get_attribute("href")
    driver.get(new_window_url)
    sleep(3)
    element = driver.find_element_by_class_name("input")
    element.send_keys("rabotarutlt@gmail.com")
    element = driver.find_element_by_class_name("input_1Um_6")
    element.send_keys("m3X8P49T9f92DMWkJf5#")
    element.submit()
    sleep(3)


    # читаем линки из БД. только не заполненные

    query.execute("SELECT rec_id, link FROM vacant WHERE date= '';")
    rec_all = query.fetchall()
    for rec in rec_all:

        # загрузка страницы
        url = rec['link']
        driver.get(url)                                                         
        sleep(3)

        # название вакансии единственный тег h1. Есть обязательно
        element = driver.find_element_by_tag_name('h1') 
        vacancy = element.text
        # print ('-------------------')
        # print (element.get_attribute('outerHTML'))
        # print ('-------------------')


        # нужно поднятся на два ула вверх и упасть до ссылки
        parent = element.find_element_by_xpath("../..")
        # print ('-------------------')
        # print (parent.get_attribute('outerHTML'))
        # print ('-------------------')

        a = parent.find_element_by_tag_name('div h2 a')
        print ('-------------------')
        print (a.get_attribute('outerHTML'))
        print ('-------------------')



        driver.quit()
        sys.exit()




        link = parent.find_element_by_xpath("./div[2]/div/h2/a")
        company = link.text
        print('===========')

        # группа Контактная информация имеет внятное имя.
        # Узел необязательный - если нет, то следующая вакансия
        try:
            contact_info = driver.find_element_by_name('vacancy-contacts')
        except NoSuchElementException:
            continue

        # а дальше от этого узла собираем данные
        # название компании
        #try:
        #    element = contact_info.find_element_by_xpath("./div/div/a")
        #    company = element.text
        #except NoSuchElementException:
        #    company = 'нет данных'
        
        # контактное лицо
        try:
            element = contact_info.find_element_by_xpath("./div/div/div")
            face = element.text
        except NoSuchElementException:
            face = 'нет данных'

        # контактный телефон с кнопкой развертывания
        try:
            btn = contact_info.find_element_by_css_selector("button")
            element_phone = btn.find_element_by_xpath('..')
            btn.click()
            phone = element_phone.text
        except NoSuchElementException:
            phone = 'нет данных'
        
        driver.quit()
        sys.exit()

        #try:
         #   element = driver.find_element_by_class_name("link_3cMNA")
          #  phone = element.text
        #except NoSuchElementException:
        #    phone = ''
        #try:
        #    element = driver.find_element_by_class_name("hr_3mYeJ")
        #    face = element.text
        #except NoSuchElementException:
        #    face = ''

        #element = driver.find_element_by_class_name("vacancy-info_mVlOu")
        #date = element.text
        #date = date.replace('сегодня', date_now)
        date = ''

        print(vacancy) # название вакансии
        print(company) #  компания
        print(phone) #  телефон
        print(face) # контактное лицо
        print(date) # дата возникновения?

        sql = ("UPDATE vacant SET "
               "vacancy = '{}',"
               "company = '{}',"
               "phone = '{}',"
               "face = '{}',"
               "date = '{}' "
               "WHERE rec_id = {}"
               .format(vacancy, company, phone, face, date, rec['rec_id']))
        query.execute(sql)
        con.commit()

    # Нажать на кнопку <button class="ui basic button button_2DvrK" role="button">Показать контакты</button>

    # <a target="_blank" class="vacancy-title_1sIep" href="/vacancy/card/204548072/voditel-legkovogo-avtomobilya?position=1&amp;track=search&amp;search_query="><span>Водитель легкового автомобиля</span></a>
    con.close()
    driver.quit()

    # ◾◾◾ Парсинг
    # parser = etree.HTMLParser()
    # tree = etree.parse("page.html", parser)
    # root = tree.getroot()
    # vacancy = root.xpath('//*[@bgcolor="#FFFFFF"]') # ищем таблицу вакансии по цвету

#


if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ
    main()


# <input autocomplete="off" class="ui input" type="text" placeholder="Телефон или e-mail" value="">
# print (new_window_url)
# element.send_keys("va-klimov@mail.ru")
# <input type="password" class="input_1Um_6 " placeholder="Введите пароль" value="">
# element = driver.find_element_by_class_name("input_1Um_6")
# element.send_keys("пароль")
# <button type="submit" class="ui orange button submit_1aqae" role="button">Войти</button>
# element.submit()

# <a match="[object Object]" location="[object Object]" history="[object Object]" href="/login">Вход</a>
# url = 'https://mail.ru'
# driver.get(url) # загрузка страницы
# sleep(3)
# # content = driver.page_source
# # f = open('page.html', 'w',encoding='utf-8')
# # f.write(content)
# # f.close()
# # pickle.dump(driver.get_cookies(), open("cookies.pkl","wb"))
# # driver.quit()

# # <input id="mailbox:login" class="input i-no-right-radius i-width-100% mailbox__rwd-control" type="text" name="login" value="" tabindex="21" placeholder="Имя ящика">
# elem = driver.find_element_by_id('mailbox:login')
# elem.clear()
# elem.send_keys("va-klimov@mail.ru")

# elem = driver.find_element_by_id('mailbox:password')
# elem.clear()
# elem.send_keys("wA{q5%$n<H8)")
# elem.submit()

# response = requests.get('https://zarplata.ru')

# f = open('x.html', 'w',encoding='utf-8')
# f.write(response.content.decode("utf-8"))
# f.close()
# print(response.content.decode("utf-8"))

    # f = open('page.html', 'w',encoding='utf-8')
    # f.write(driver.page_source)
    # f.close()
