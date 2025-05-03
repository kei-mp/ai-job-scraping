import pickle
import os
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI

COOKIES_FILE = "linkedin_cookies.pkl"
SKILLS_OUTPUT_FILE = "job_skills.txt"
NUM_PAGES_TO_SCRAPE = 3
JOBS_PER_PAGE = 10

OPENAI_SKILLS_PROMPT = """Pull out the technical skills from this job description. List only the name of the skill without any unnecessary words. Wrap the list of skills in a <skills></skills> block so it can be parsed:

{job_description_html}"""

def is_url_processed(url, file_path):
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() == f"URL: {url}":
                    return True
        return False
    except Exception as e:
        print(f"Error checking file {file_path} for URL {url}: {e}")
        return False

def append_processed_data(url, job_title, openai_response, file_path):
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Title: {job_title}\n")
            f.write(f"Response:\n{openai_response}\n")
            f.write("---\n")
        print(f"Successfully appended data for {url} ('{job_title}') to {file_path}")
    except Exception as e:
        print(f"Error appending data for {url} ('{job_title}') to {file_path}: {e}")

def get_skills_from_description(description_html):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return None

    client = OpenAI(api_key=openai_api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts technical skills from job descriptions."},
                {"role": "user", "content": OPENAI_SKILLS_PROMPT.format(job_description_html=description_html)}
            ]
        )
        openai_response_text = response.choices[0].message.content
        return openai_response_text

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def save_cookies(driver, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    print("Cookies saved successfully.")

def load_cookies(driver, file_path):
    try:
        with open(file_path, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                if 'domain' not in cookie or cookie['domain'] is None:
                     cookie['domain'] = '.linkedin.com'
                try:
                     driver.add_cookie(cookie)
                except Exception as cookie_err:
                     pass
            driver.refresh()
        print("Cookies loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

def human_wait():
    wait_time = random.uniform(3, 8)
    print(f"Waiting for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

driver = webdriver.Chrome()

if os.path.exists(COOKIES_FILE):
    driver.get("https://www.linkedin.com/")
    if load_cookies(driver, COOKIES_FILE):
        try:
             WebDriverWait(driver, 10).until(
                 EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav__content"))
             )
             print("Logged in using cookies.")
        except:
             print("Cookies did not result in login or session expired. Please log in manually.")
             driver.get("https://www.linkedin.com/login")
             input("Press Enter here after you have successfully logged in...")
             save_cookies(driver, COOKIES_FILE)
    else:
         print("Could not load cookies. Please log in manually.")
         driver.get("https://www.linkedin.com/login")
         input("Press Enter here after you have successfully logged in...")
         save_cookies(driver, COOKIES_FILE)
else:
    print("No cookies found. Please log in manually.")
    driver.get("https://www.linkedin.com/login")
    input("Press Enter here after you have successfully logged in...")
    save_cookies(driver, COOKIES_FILE)

all_unique_job_urls = set()
base_url = "https://www.linkedin.com/my-items/saved-jobs/"

print(f"\n--- Navigating and extracting URLs from {NUM_PAGES_TO_SCRAPE} pages ---")

if NUM_PAGES_TO_SCRAPE < 1:
    print("Warning: NUM_PAGES_TO_SCRAPE is less than 1. No pages will be scraped.")

for page_num in range(NUM_PAGES_TO_SCRAPE):
    start_index = page_num * JOBS_PER_PAGE
    page_url = f"{base_url}?start={start_index}"
    if page_num == 0:
        page_url = base_url

    print(f"Navigating to page {page_num + 1}/{NUM_PAGES_TO_SCRAPE} (URL: {page_url})...")

    try:
        driver.get(page_url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.my-items-page__list-container"))
        )
        print(f"Page {page_num + 1} loaded.")

        html_content = driver.page_source
        pattern = re.compile(r'<a.*?href\s*=\s*["\'](https://www.linkedin.com/jobs/view/\d+/?).*?["\'].*?>')
        page_job_urls = pattern.findall(html_content)

        num_urls_on_page = len(page_job_urls)
        before_add_count = len(all_unique_job_urls)
        all_unique_job_urls.update(page_job_urls)
        after_add_count = len(all_unique_job_urls)

        print(f"Found {num_urls_on_page} URLs on page {page_num + 1}. Total unique URLs collected so far: {after_add_count}")
    except Exception as e:
        print(f"An unexpected error occurred on page {page_num + 1} ({page_url}): {e}")
        print("Attempting to continue with the next page.")

    if page_num < NUM_PAGES_TO_SCRAPE - 1:
        human_wait()

print("\n--- Finished collecting URLs from pages ---")
print(f"Total unique job URLs collected from {NUM_PAGES_TO_SCRAPE} pages: {len(all_unique_job_urls)}")
print("------------------------------------------")

print("\n--- Processing unique Job Descriptions ---")
if all_unique_job_urls:
    processed_count = 0
    skipped_count = 0
    errored_count = 0

    urls_to_process = sorted(list(all_unique_job_urls))

    for i, url in enumerate(urls_to_process):
        print(f"\nProcessing URL {i+1}/{len(urls_to_process)}: {url}")

        if is_url_processed(url, SKILLS_OUTPUT_FILE):
            skipped_count += 1
            continue

        job_title = "[Title Not Found]"
        description_html = None

        try:
            driver.get(url)

            try:
                title_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.t-24.t-bold.inline"))
                )
                job_title = title_element.text.strip()
                print(f"Extracted Title: {job_title}")
            except Exception as e:
                print(f"Could not find job title element for {url}. Using placeholder. Error: {e}")

            try:
                description_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article.jobs-description__container"))
                )
                description_html = description_element.get_attribute('outerHTML')
            except Exception as e:
                 print(f"Could not find job description element for {url}. Cannot extract skills. Error: {e}")

            if description_html:
                openai_response = get_skills_from_description(description_html)

                if openai_response is not None:
                    append_processed_data(url, job_title, openai_response, SKILLS_OUTPUT_FILE)
                    processed_count += 1
                else:
                    print(f"Skipping appending data for {url} due to OpenAI error.")
                    errored_count += 1
            else:
                 print(f"Skipping OpenAI processing and file append for {url} because description HTML was not found.")
                 errored_count += 1

        except Exception as e:
            print(f"An unexpected error occurred while processing {url}: {e}")
            errored_count += 1

        human_wait()

    print(f"\n--- Processing Summary ---")
    print(f"Total unique URLs collected from pages: {len(all_unique_job_urls)}")
    print(f"URLs skipped (already processed): {skipped_count}")
    print(f"URLs processed with OpenAI and saved: {processed_count}")
    print(f"URLs encountered errors during processing: {errored_count}")
    print(f"Results saved to {SKILLS_OUTPUT_FILE}")
    print("--------------------------")

else:
    print("No unique URLs collected from the specified pages.")

time.sleep(5)
driver.quit()
print("Browser closed.")