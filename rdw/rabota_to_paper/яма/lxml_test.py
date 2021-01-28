# pip install lxml

from lxml import etree
from io import StringIO
import re
# Из строки
# broken_html = "<html><head><title>test<body><h1>page title</h3>"
# parser = etree.HTMLParser()
# tree   = etree.parse(StringIO(broken_html), parser)
# result = etree.tostring(tree.getroot(),pretty_print=True, method="html")

# Из файла
parser = etree.HTMLParser()
tree   = etree.parse("html.txt",parser)
result = etree.tostring(tree.getroot(),pretty_print=True, method="html")
##print(result)

root = tree.getroot()
child = root[0]
print(child.tag)
print(len(root))
child = root[1]
print(child.tag)

children = list(root)
for child in root:
    print(child.tag)

if len(root):   # this no longer works!
    print("The root element has children")

##Ищем у детей
print('Ищем у детей')
print(root.find("b"))
print(root.find("body"))

##print(root.find(".//Система управления сайтом samara.rabota.ru (Самара)"))

print('Ищем элемент')

print(tree.xpath("//*[@cellspacing='2']/tbody/tr[2]/td[2]/span"))
vv = tree.xpath("//*[@cellspacing='2']/tbody/tr[2]/td[2]/span")
print('серилизация')
for child in vv:
    print(etree.tounicode(child, method="text"))

s= etree.tounicode(vv[0], method="text")
pattern_id=re.compile('id_предложения ([0-9]*), id_пользователя ([0-9]*)')
m = pattern_id.search(s)
if not m:
    print('нах')

print(m.group(1), m.group(1))

