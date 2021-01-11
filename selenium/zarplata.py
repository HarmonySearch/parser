# ◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾
# Парсинг вакансий https://zarplata.ru/
# ◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾◾

release = '(1.01)'

import re, sqlite3, datetime, locale

from time import sleep
# import pickle
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import *

from lxml import etree

def main():

    now = datetime.datetime.now()
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    date_now = now.strftime("%d %b")
    
    # БД SQLite
    file_db = 'pack/file.db'
    con = sqlite3.connect(file_db)
    con.row_factory = sqlite3.Row                                      # для доступа к полям по имени
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


    path_to_chromedriver = 'chromedriver' # адрес WebDriver
    driver = webdriver.Chrome(executable_path = path_to_chromedriver) # запуск WebDriver
    url = 'https://tolyatti.zarplata.ru/'
    driver.get(url) # загрузка страницы
    sleep(3)

    # найти кнопку "Вход"

    new_window_url = driver.find_element_by_link_text("Вход").get_attribute("href")
    driver.get(new_window_url)
    sleep(3)
    element = driver.find_element_by_class_name("input")
    element.send_keys("rabotarutlt@gmail.com")
    element = driver.find_element_by_class_name("input_1Um_6")
    element.send_keys("m3X8P49T9f92DMWkJf5#")
    element.submit()
    sleep(3)

    for i in range(0, 201,25): # 0, 201,25
        url = "https://tolyatti.zarplata.ru/vacancy?offset={0}".format(i)
        print(url)
        driver.get(url)
        sleep(3)
        # находим ссылки на вакансии
        for link in driver.find_elements_by_xpath('//a[@class ="vacancy-title_1sIep"]'):
            print (link.get_attribute('href'))

            # записать в базу данных ссылки
            try:
                query.execute("INSERT INTO vacant (link)"
                " VALUES (?);",(link.get_attribute('href'),))

            except sqlite3.Error as e:
                print (e.args[0])
                # logging.critical('btn_collect_ref_click: {} {}'.format( e.args[0],sql))

            con.commit()
        
    # читаем линки из БД. только не заполненные
    
    query.execute("SELECT rec_id, link FROM vacant WHERE date= '';")
    rec_all = query.fetchall()
    for rec in rec_all:

        url = rec['link']
        driver.get(url) # загрузка страницы
        sleep(3)

        try:
            button = driver.find_element_by_class_name("button_2DvrK")
            button.click()
            sleep(3)
        except NoSuchElementException:
            continue

        element = driver.find_element_by_class_name("header_20r3Q")
        vacancy = element.text
        element = driver.find_element_by_class_name("company_2yzPu")
        company = element.text
        try:
            element = driver.find_element_by_class_name("link_3cMNA")
            phone = element.text
        except NoSuchElementException:
            phone = ''
        try:
            element = driver.find_element_by_class_name("hr_3mYeJ")
            face = element.text
        except NoSuchElementException:
            face = ''

        element = driver.find_element_by_class_name("vacancy-info_mVlOu")
        date = element.text
        date = date.replace('сегодня', date_now)

        print (vacancy)
        print (company)
        print (phone)
        print (face)
        print (date)
        

        sql = ( "UPDATE vacant SET "
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

