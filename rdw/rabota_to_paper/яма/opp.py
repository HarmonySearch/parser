from bs4 import BeautifulSoup
import re

f = open('html.txt', encoding="utf-8")
html = f.read()
soup = BeautifulSoup(html, 'html5lib') # грузим дерево

#Последовательно ищет только в группа так что в цикле придется точняк
tab = soup.find("tr", attrs={"bgcolor": "#F6F6F6","bgcolor": "#FFFFFF"})
print(tab)
# id вакансии и работодателя
qq = tab.find(string=re.compile('id_предложения'))
print (qq)

# профессия и зарплата
qqq = tab.find('h2')
print ()
print (qqq)

# регион размещения
#qqqq = tab.find('table').tr.next_sibling.next_sibling.next_sibling.next_sibling


qqqq = tab.find('td', string=re.compile('Регионы размещения')).next_sibling.next_sibling
print (qqqq)


# фейс телефон емаил
qqqq = tab.find('td', string=re.compile('Работодатель'))
print (qqqq)















# h2 = soup.find_all("span") 

# Ищем все записи
# list = soup.find_all(string = re.compile("id_предложения"))
#for rec in list:
#     print(rec)
# print(len(list))

# делаем цикл по поиску записи (номер есть) нет нужно найти
# Ищем нежную запись печатаем
# id_предложения 41858223, id_пользователя 34751658,
# id = re.compile('id_предложения ([0-9]+), id_пользователя ([0-9]+),')
# for vacant in list:
    # m = id.search(str(vacant.string))
    # id_vacant = m.group(1)
    # id_user = m.group(2)
    # print(id_vacant,id_user)
    
    # х = soup.find(string = re.compile(id_vacant))
    # print (х)
    # break


# html = urlopen('http://www.pythonscraping.com/pages/warandpeace.html')
# bs = BeautifulSoup(html.read(), 'html.parser')
# nameList = bs.find_all('span', {'class':'green'})
# for name in nameList:
    # print(name.get_text())
