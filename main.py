from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
import pandas
import time
from datetime import datetime
import numpy
import smtplib
import os

OWN_EMAIL = os.environ['SENDER_EMAIL']
OWN_PASSWORD = os.environ['SENDER_EMAIL_PASSWORD']


def price_str_to_float(price_euro:str) -> float:
    '''Convert string price to float'''
    return float(price_euro.replace("€", "").replace(",", "."))


def send_email(product: str, email: str, message: str, price: float):
    '''Send email message alerting of price below target'''
    header = f"From: {OWN_EMAIL}\nTo: {email}\nMIME-Version: 1.0\nContent-type: text/html\nSubject: {product} price is below target -> {price}!\n\n"
    email_message = header + message
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(OWN_EMAIL, email.split(";"), email_message)


data = pandas.read_csv("products.csv")
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument('--disable-dev-shm-usage')
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=options)
except SessionNotCreatedException:
    driver = webdriver.Chrome(executable_path="chromedriver", options=options)
except WebDriverException:
    driver = webdriver.Chrome(options=options)
today = datetime.now().date().strftime("%d-%m-%Y")
for index, product in data.iterrows():
    price = 0
    driver.get(product.link)
    time.sleep(1)
    if product.type == "id":
        price = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.ID, product.location)))
        price = price_str_to_float(price.text)
    elif product.type == "class":
        price = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CLASS_NAME, product.location)))
        price = price_str_to_float(price.text)
    elif product.type == "lionofporches":
        WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.XPATH, '//*[@id="popup-campaign"]/div[2]'))).click()
        time.sleep(2)
        items = WebDriverWait(driver, 10).until(
            ec.presence_of_all_elements_located((By.CLASS_NAME, "current")))
        if len(items) > 0:
            i = 0
            for item in items:
                item_price = price_str_to_float(item.text)
                if item_price < price and i > 0 or i == 0:
                    price = item_price
    if price > 0:
        last_price = 0
        try:
            with open(f"items/{product['item']}.csv", "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            with open(f"items/{product['item']}.csv", "w") as file:
                file.write(f"Date,Price\n{today},{price}\n")
        else:
            if len(lines) > 0:
                item_data = pandas.read_csv(f"items/{product['item']}.csv")
                item_data.loc[len(item_data)] = [today,price]
                item_data.to_csv(f"items/{product['item']}.csv", index=False)
            else:
                with open(f"items/{product['item']}.csv", "w") as file:
                    file.write(f"Date,Price\n{today},{price}\n")
        if float(product.target) >= price != last_price:
            send_email(product['item'].title(), product.email, f"{product.link}", price)
