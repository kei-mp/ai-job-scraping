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
OPENAI_SKILLS_PROMPT = """Pull out the technical skills from this job description. List only the name of the skill without any unnecessary words. Wrap the list of skills in a <skills></skills> block so it can be parsed:
{job_description_html}"""

def is_url_processed(url, file_path):
    """Checks if a URL has already been processed by looking in the output file."""
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() == f"URL: {url}":
                    print(f"URL {url} found in {file_path}, skipping.")
                    return True
        return False
    except Exception as e:
        print(f"Error checking file {file_path} for URL {url}: {e}")
        return False
    
def append_processed_data(url, openai_response, file_path):
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Response:\n{openai_response}\n")
            f.write("---\n") # Separator
        print(f"Successfully appended data for {url} to {file_path}")
    except Exception as e:
        print(f"Error appending data for {url} to {file_path}: {e}")

def get_skills_from_description(description_html):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return None

    client = OpenAI(api_key=openai_api_key)

    try:
        print("Sending job description to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # You can use gpt-4o or other models if preferred
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts technical skills from job descriptions."},
                {"role": "user", "content": OPENAI_SKILLS_PROMPT.format(job_description_html=description_html)}
            ]
        )
        # Extract the text content from the response
        openai_response_text = response.choices[0].message.content
        print("Received response from OpenAI.")
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

print("\n--- Processing Job Descriptions ---")
if unique_job_urls:
    processed_count = 0
    skipped_count = 0
    errored_count = 0

    # Convert set to list and sort for consistent processing order
    urls_to_process = sorted(list(unique_job_urls))

    for i, url in enumerate(urls_to_process):
        print(f"\nProcessing URL {i+1}/{len(urls_to_process)}: {url}")

        # --- Check if URL is already processed ---
        if is_url_processed(url, SKILLS_OUTPUT_FILE):
            skipped_count += 1
            continue # Skip to the next URL if already processed

        try:
            driver.get(url)

            # Wait for the job description element to be present and potentially interactive (visible)
            # LinkedIn often uses an article tag with class jobs-description__container
            description_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.jobs-description__container"))
                # Or check for visibility: EC.visibility_of_element_located((By.CSS_SELECTOR, "article.jobs-description__container"))
            )

            # Get the outer HTML of the description element
            description_html = description_element.get_attribute('outerHTML')

            # --- Process HTML with OpenAI ---
            openai_response = get_skills_from_description(description_html)

            if openai_response is not None:
                # --- Append results to file ---
                append_processed_data(url, openai_response, SKILLS_OUTPUT_FILE)
                processed_count += 1
            else:
                print(f"Skipping appending data for {url} due to OpenAI error.")
                errored_count += 1

        except Exception as e:
            print(f"An error occurred while processing {url}: {e}")
            errored_count += 1

        human_wait()

    print(f"\n--- Processing Summary ---")
    print(f"Total unique URLs found: {len(unique_job_urls)}")
    print(f"URLs skipped (already processed): {skipped_count}")
    print(f"URLs processed with OpenAI: {processed_count}")
    print(f"URLs encountered errors during processing: {errored_count}")
    print(f"Results saved to {SKILLS_OUTPUT_FILE}")
    print("--------------------------")

else:
    print("No unique URLs to visit.")

time.sleep(10)
driver.quit()