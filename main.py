import pickle
import os
import time
import re
import random
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

def human_wait():
    wait_time = random.uniform(3, 8)
    print(f"Waiting for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

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

print("Navigating to saved jobs page...")
driver.get("https://www.linkedin.com/my-items/saved-jobs/")

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav__content"))
    )
    print("Saved jobs page loaded.")
except:
    print("Timed out waiting for saved jobs list to load. Proceeding with available HTML.")

html_content = driver.page_source
pattern = re.compile(r'<a.*?href\s*=\s*["\'](https://www.linkedin.com/jobs/view/\d+/).*?["\'].*?>')
job_urls = pattern.findall(html_content)
unique_job_urls = set(job_urls)
print("\n--- Extracted LinkedIn Job URLs ---")
if job_urls:
    for url in job_urls:
        print(url)
else:
    print("No job view URLs found matching the pattern.")
print("---------------------------------")

# --- Visit Each Unique URL and Extract Description ---

print("\n--- Extracting Job Descriptions ---")
if unique_job_urls:
    for i, url in enumerate(unique_job_urls):
        print(f"Visiting URL {i+1}/{len(unique_job_urls)}: {url}")
        try:
            driver.get(url)

            # Wait for the job description element to be present
            description_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.jobs-description__container"))
            )

            # Get the outer HTML of the description element
            description_html = description_element.get_attribute('outerHTML')

            print(f"--- Description for {url} ---")
            print(description_html)
            print("---------------------------")

        except Exception as e:
            print(f"An error occurred while processing {url}: {e}")

        human_wait()
else:
    print("No unique URLs to visit.")

time.sleep(10)
driver.quit()