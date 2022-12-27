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
import smtplib
import os

OWN_EMAIL = os.environ['SENDER_EMAIL']
OWN_PASSWORD = os.environ['SENDER_EMAIL_PASSWORD']

SLEEP_TIME = 2
TODAY = datetime.now().date().strftime("%d-%m-%Y")

# Selenium Options
OPTIONS = Options()
OPTIONS.add_argument("--no-sandbox")
OPTIONS.add_argument("--headless")
OPTIONS.add_argument("--disable-gpu")
OPTIONS.add_argument('--disable-dev-shm-usage')


def price_str_to_float(price_euro:str) -> float:
    '''Convert string price to float'''
    try:
        price = float(price_euro.replace("€", "").replace(",", "."))
    except ValueError:
        price = 0

    return price


def send_email(product: str, email: str, message: str, price: float):
    '''Send email message alerting of price below target'''
    header = f"From: {OWN_EMAIL}\nTo: {email}\nMIME-Version: 1.0\nContent-type: text/html\nSubject: {product} price is below target -> {price}!\n\n"
    email_message = header + message
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(OWN_EMAIL, email.split(";"), email_message)


def get_price(locator, product) -> float:
    '''Get current price from product'''
    if str(product.popup) != 'nan':
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.XPATH, product.popup))).click()
        time.sleep(2)
    items = WebDriverWait(driver, 10).until(ec.presence_of_all_elements_located((locator, product.location)))
    price = 0
    i = 0
    for item in items:
        if item.text != "":
            item_price = price_str_to_float(item.text)
            if item_price < price and i > 0 or i == 0:
                price = item_price

    return price


if __name__ == "__main__":
    data = pandas.read_csv("products.csv")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=OPTIONS)
    except SessionNotCreatedException:
        driver = webdriver.Chrome(executable_path="chromedriver", options=OPTIONS)
    except WebDriverException:
        driver = webdriver.Chrome(options=OPTIONS)
    for index, product in data.iterrows():
        price = 0
        print(product["item"], product["link"])
        driver.get(product.link)
        time.sleep(SLEEP_TIME)
        if product.type == "id":
            product_locator = By.ID
        elif product.type == "class":
            product_locator = By.CLASS_NAME
        elif product.type == "xpath":
            product_locator = By.XPATH
        elif product.type == "css":
            product_locator = By.CSS_SELECTOR

        price = get_price(product_locator, product)
        if price > 0:
            last_price = 0
            try:
                with open(f"items/{product['item']}.csv", "r") as file:
                    lines = file.readlines()
            except FileNotFoundError:
                with open(f"items/{product['item']}.csv", "w") as file:
                    file.write(f"Date,Price\n{TODAY},{price}\n")
            else:
                if len(lines) > 0:
                    item_data = pandas.read_csv(f"items/{product['item']}.csv")
                    last_price = item_data.iloc[-1]["Price"]
                    if item_data.Date[len(item_data)-1] != TODAY:
                        item_data.loc[len(item_data)] = [TODAY,price]
                    elif item_data.Price[len(item_data)-1] != price:
                        item_data.loc[len(item_data)-1] = [TODAY,price]
                    item_data.to_csv(f"items/{product['item']}.csv", index=False)
                else:
                    with open(f"items/{product['item']}.csv", "w") as file:
                        file.write(f"Date,Price\n{TODAY},{price}\n")
            if float(product.target) >= price != last_price:
                send_email(product['item'].title(), product.email, f"{product.link}", price)
