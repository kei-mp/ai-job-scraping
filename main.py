import pickle
import os
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI # Import OpenAI library
# Import specific exceptions for more robust handling if needed
from selenium.common.exceptions import NoSuchElementException, TimeoutException


# --- Constants ---
COOKIES_FILE = "linkedin_cookies.pkl"
SKILLS_OUTPUT_FILE = "job_skills.txt"
# Define the OpenAI prompt
OPENAI_SKILLS_PROMPT = """Pull out the technical skills from this job description. List only the name of the skill without any unnecessary words. Wrap the list of skills in a <skills></skills> block so it can be parsed:

{job_description_html}""" # Placeholder for job description HTML

# --- File Handling for Processed URLs ---

def is_url_processed(url, file_path):
    """Checks if a URL has already been processed by looking in the output file."""
    # We only check for the URL, not the title or response, as URL is the unique key
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read line by line to avoid loading huge files into memory
            for line in f:
                if line.strip() == f"URL: {url}":
                    print(f"URL {url} found in {file_path}, skipping.")
                    return True
        return False
    except Exception as e:
        print(f"Error checking file {file_path} for URL {url}: {e}")
        # Assume not processed if there's an error reading the file
        return False

# --- MODIFIED FUNCTION ---
def append_processed_data(url, job_title, openai_response, file_path):
    """Appends the URL, Job Title, and OpenAI response to the output file."""
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Title: {job_title}\n") # Add the job title line
            f.write(f"Response:\n{openai_response}\n")
            f.write("---\n") # Separator
        print(f"Successfully appended data for {url} ('{job_title}') to {file_path}")
    except Exception as e:
        print(f"Error appending data for {url} ('{job_title}') to {file_path}: {e}")

# --- OpenAI Integration (No changes needed here) ---

def get_skills_from_description(description_html):
    """Sends job description HTML to OpenAI and returns the response."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return None

    client = OpenAI(api_key=openai_api_key)

    try:
        print("Sending job description to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Or other models like gpt-4o
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

# --- Selenium Helper Functions (No significant changes needed) ---

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
                     print(f"Could not add cookie {cookie.get('name')}: {cookie_err}")
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

# --- Main Script Logic ---

driver = webdriver.Chrome()

# --- Login/Cookie Handling (remains the same) ---
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

# --- Navigate to Saved Jobs (remains the same) ---
print("Navigating to saved jobs page...")
driver.get("https://www.linkedin.com/my-items/saved-jobs/")

try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.my-items-page__list-container"))
    )
    print("Saved jobs list loaded.")
except:
    print("Timed out waiting for saved jobs list to load. Proceeding with available HTML.")


# --- Extract Job URLs from the Page Source (remains the same) ---
html_content = driver.page_source
pattern = re.compile(r'<a.*?href\s*=\s*["\'](https://www.linkedin.com/jobs/view/\d+/?).*?["\'].*?>')
job_urls = pattern.findall(html_content)
unique_job_urls = set(job_urls)
print("\n--- Extracted LinkedIn Job URLs ---")
if unique_job_urls:
    for url in sorted(list(unique_job_urls)):
        print(url)
else:
    print("No job view URLs found matching the pattern in the initial source.")
print(f"Found {len(unique_job_urls)} unique job URLs.")
print("---------------------------------")


# --- Visit Each Unique URL, Extract Title & Description, Process with OpenAI ---

print("\n--- Processing Job Descriptions ---")
if unique_job_urls:
    processed_count = 0
    skipped_count = 0
    errored_count = 0

    urls_to_process = sorted(list(unique_job_urls))

    for i, url in enumerate(urls_to_process):
        print(f"\nProcessing URL {i+1}/{len(urls_to_process)}: {url}")

        # --- Check if URL is already processed ---
        if is_url_processed(url, SKILLS_OUTPUT_FILE):
            skipped_count += 1
            continue # Skip to the next URL if already processed

        job_title = "[Title Not Found]" # Default placeholder
        description_html = None # Initialize description variable

        try:
            driver.get(url)

            # --- Extract Job Title ---
            try:
                # Wait for the job title element to be present
                title_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.t-24.t-bold.inline"))
                )
                job_title = title_element.text.strip()
                print(f"Extracted Title: {job_title}")
            except (NoSuchElementException, TimeoutException) as e:
                print(f"Could not find job title element for {url}: {e}")
                # Continue processing, using the placeholder title

            # --- Extract Job Description HTML ---
            try:
                # Wait for the job description element to be present
                description_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article.jobs-description__container"))
                )
                # Get the outer HTML of the description element
                description_html = description_element.get_attribute('outerHTML')
                # print(f"--- Description HTML extracted for {url} ---") # Optional: uncomment to see HTML
            except (NoSuchElementException, TimeoutException) as e:
                 print(f"Could not find job description element for {url}: {e}")
                 # If description isn't found, we can't send it to OpenAI, so description_html remains None

            # --- Process HTML with OpenAI IF description was found ---
            if description_html:
                openai_response = get_skills_from_description(description_html)

                if openai_response is not None:
                    # --- Append results to file ---
                    # Now passing the job_title variable
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
            # Note: If an error occurs *before* getting the title/description,
            # it will fall into this outer catch.

        # --- Human-like wait before the next action ---
        human_wait()

    print(f"\n--- Processing Summary ---")
    print(f"Total unique URLs found: {len(unique_job_urls)}")
    print(f"URLs skipped (already processed): {skipped_count}")
    print(f"URLs processed with OpenAI and saved: {processed_count}")
    print(f"URLs encountered errors during processing: {errored_count}")
    print(f"Results saved to {SKILLS_OUTPUT_FILE}")
    print("--------------------------")

else:
    print("No unique URLs to visit.")

# --- Cleanup ---
time.sleep(5) # Give a few seconds before closing
driver.quit()
print("Browser closed.")