import pickle
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_FILE = "linkedin_cookies.pkl"

def save_cookies(driver, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("Cookies saved successfully.")

def load_cookies(driver, file_path):
    try:
        with open(file_path, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                if 'domain' not in cookie:
                     cookie['domain'] = '.linkedin.com'
                driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

# --- Main Script Logic ---

driver = webdriver.Chrome()

if os.path.exists(COOKIES_FILE):
    driver.get("https://www.linkedin.com/") 
    load_cookies(driver, COOKIES_FILE)
    driver.refresh()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav__content"))
        )
        print("Logged in using cookies.")
    except:
        print("Cookies did not result in login. Please log in manually.")
        driver.get("https://www.linkedin.com/login")
        input("Press Enter here after you have successfully logged in...")
        save_cookies(driver, COOKIES_FILE)
else:
    driver.get("https://www.linkedin.com/login")
    input("Press Enter here after you have successfully logged in...")
    save_cookies(driver, COOKIES_FILE)

driver.get("https://www.linkedin.com/my-items/saved-jobs/?start=160")

time.sleep(10)
driver.quit()