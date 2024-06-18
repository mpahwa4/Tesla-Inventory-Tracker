from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.firefox.options import Options
import time
from datetime import datetime
from twilio.rest import Client

LINK_RWD = "https://www.tesla.com/en_CA/inventory/new/my"
LINK_AWD = "https://www.tesla.com/en_CA/inventory/new/my?TRIM=LRAWD"

RWD_THRESHOLD = 54990
AWD_THRESHOLD = 60000
RWD_REG_PRICE = 54990
AWD_REG_PRICE = 63990
TWILIO_ID = ""
TWILIO_TOKEN = ""
TWILIO_PHONE_NUM = ""
CONTACT_PHONE_NUM = ""
POSTAL_CODE = ""

RWD_known_deals = {}
AWD_known_deals = {}
error_count = 0
count = 0

account_sid = TWILIO_ID
auth_token = TWILIO_TOKEN
client = Client(account_sid, auth_token)

for i in range(3):
    try:
        driver = webdriver.Firefox()
        break
    except:
        if (i == 2):
            print("Driver startup failed")
            quit()
        else:
            pass

driver.get(LINK_RWD)
time.sleep(3)
elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/header/div/div/dialog/div[1]/div[6]/div/div/div[1]/div[1]/div/div[2]/a[1]")))
elem.click()

print("-------------------")
while(True):
    if count % 2 == 0:
        link = LINK_AWD
        threshold = AWD_THRESHOLD
        reg_price = AWD_REG_PRICE
        model = "AWD"
    else:
        link = LINK_RWD
        threshold = RWD_THRESHOLD
        reg_price = RWD_REG_PRICE
        model = "RWD"

    try:
        print(f"Getting price for {model}")
        driver.get(link)
        time.sleep(3)

        # sort by price low to high
        select = Select(driver.find_element(By.XPATH, value='//*[@id="filter_lbl"]'))
        select.select_by_value("plh")

        time.sleep(5)

        # update postal code
        elem = WebDriverWait(driver,10).until(EC.visibility_of_element_located((By.NAME, "zip")))
        elem.clear()
        elem.send_keys(POSTAL_CODE)

        time.sleep(15)

        # get lowest available price
        elem = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/main/div/article[1]/section[1]/div[2]/div[1]/div/span")))
        price = elem.text
        price = int(price[1:].replace(",", ""))

        # price is lower than threshold
        if price < threshold:
            if (model == 'AWD' and price not in AWD_known_deals.keys()) or (model == 'RWD' and price not in RWD_known_deals.keys()):
                print(f"[{model}] Tesla Model Y Price: ${price}. Sending Text")
                message = client.messages.create(
                from_=TWILIO_PHONE_NUM,
                to=CONTACT_PHONE_NUM,
                body=f'[{model}] Tesla Model Y Price: ${price}. Link: {link}'
                )
                if model == 'AWD':
                    AWD_known_deals[price] = datetime.now()
                    print("Deal added to known deals")
                else:
                    RWD_known_deals[price] = datetime.now()
                    print("Deal added to known deals")
                print("Text Sent")
            else:
               print(f"Price low but known (${price})")
        

        else:
            print(f"Price not low enough (${price})")
            if (model == 'AWD' and price == reg_price and len(AWD_known_deals) != 0):                    
                print("Price back to regular, clearing all previous deals")
                for (deal_price, beg_time) in AWD_known_deals.items():
                    print(f"Clearing Deal: {deal_price}, Duration: {datetime.now() - beg_time}")
                AWD_known_deals.clear()
            elif (model == 'RWD' and price == reg_price and len(RWD_known_deals) != 0):
                print("Price back to regular, clearing all previous deals")
                for (deal_price, beg_time) in RWD_known_deals.items():
                    print(f"Clearing Deal: {deal_price}, Duration: {datetime.now() - beg_time}")
                RWD_known_deals.clear()
        error_count = 0


    except Exception as e:
        if error_count < 10:
            print(f"Error: {str(e)}, trying again")
            error_count += 1
        else:
            print("Too many errors, quitting program")
            driver.quit()
            quit()
    
    # wait 2.5 mins before checking again
    print("Waiting 2.5 mins")
    count += 1
    if count == 368:
        driver.quit()
        quit()
    print("\n-------------------")
    time.sleep(150)
