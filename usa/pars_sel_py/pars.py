# ---------------------------------------------------------------------
# Парсинг вакансий https://www.google.ru/maps
# ---------------------------------------------------------------------

import sys
import locale
import mysql.connector

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep

def main():

    config = {
        'user': 'usa',
        'password': 'usa',
        'host': '192.168.2.201',
        'database': 'usa',
        'raise_on_warnings': True
    }

    cnx = mysql.connector.connect(**config)

    curA = cnx.cursor(buffered=True)

    path_to_gechodriver = 'driver/geckodriver' 
    firefox_binary = 'firefox/firefox'
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(executable_path=path_to_gechodriver,
        options=options, firefox_binary=firefox_binary) 

    url = 'https://www.google.ru/maps/'
    driver.get(url)
    sleep(2)
    element = driver.find_element_by_id("searchboxinput").send_keys("Замок Гарибальди, Речной переулок, Хрящевка, Самарская область")
    sleep(2)
    element = driver.find_element_by_id("searchbox-searchbutton").click()
    sleep(2)
    element = driver.find_element_by_class_name("widget-pane-link").click()
    sleep(2)

    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//div[@role='menu']"))).click()
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//li[@data-index='2']"))).click()

    sleep(5)
    i = 0
    while True:
        reviews = driver.find_elements_by_class_name("section-review")
        star = reviews[i].find_elements_by_class_name("section-review-star-active")
        if (len(star) < 4 ): break
        men = reviews[i].find_element_by_class_name("section-review-title")
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
        if (i > 10): break
        target = reviews[i+5]
        target.location_once_scrolled_into_view
        sleep(5)
        i=i+1
    cnx.close()
    driver.quit()
    sys.exit()

if __name__ == '__main__':                                                      # ОСНОВНОЙ ЦИКЛ
    main()
