import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo


client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]


browser = webdriver.Chrome()
# browser = webdriver.PhantomJS(r'D:\phantomjs-2.1.1-windows\bin\phantomjs.exe')
# browser.set_window_size(1400,900)
wait = WebDriverWait(browser, 10)

def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#J_TSearchForm > div.search-button > button")))
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total"))
        )
        get_products()
        return total.text
    except TimeoutException:
        return search()

def next_page(page_number):
    print('正在翻页',page_number)
    try:
        input = wait.until (
            EC.presence_of_element_located ( (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input") )
        )
        submit = wait.until (
            EC.element_to_be_clickable ( (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit") ) )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)

def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image':item.find('.pic .img').attr('data-src'),
            'price':re.sub('\\n','',item.find('.g_price').text()),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':re.sub(r'\n',' ',item.find('.title').text()),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert_one(result):
            print('存储到MongoDB成功',result)
    except:
        print('存储到MongoDB失败',result)


def main():
    try:
        total = search()
        total = int(re.compile(r'(\d+)').search(total).group(1))
        for i in range(2,total + 1):
            next_page(i)
    except:
        print('出错啦')
    finally:
        browser.close()


if __name__ == '__main__':
    main()