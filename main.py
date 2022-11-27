from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import pandas
import time
from datetime import datetime

data = pandas.read_csv("products.csv")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
today = datetime.now().date().strftime("%d-%m-%Y")
for index, line in data.iterrows():
    price = 0
    driver.get(line.link)
    time.sleep(2)
    if line.type == "id":
        price = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.ID, line.location)))
        price = float(price.text.split("€")[0].replace(",", "."))
    elif line.type == "lionofporches":
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="popup-campaign"]/div[2]'))).click()
        time.sleep(2)
        items = WebDriverWait(driver, 10).until(ec.presence_of_all_elements_located((By.CLASS_NAME, "current")))
        price = 1000
        for item in items:
            item_price = float(item.text.split("€")[0].replace(",", "."))
            if item_price < price:
                price = item_price
    try:
        with open(f"items/{line['item']}.csv", "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        with open(f"items/{line['item']}.csv", "w") as file:
            file.write(f"{today},{price}\n")
    else:
        with open(f"items/{line['item']}.csv", "a") as file:
            if len(lines) > 0:
                last_price = float(lines[-1].split(",")[1])
                if last_price != price:
                    file.write(f"{today},{price}\n")
            else:
                file.write(f"{today},{price}\n")
    if price < int(line.target):
        print(f"Buy {line.link}")


