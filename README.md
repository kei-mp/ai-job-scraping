# ai-job-scraping

Using python, selenium, and AI to scrape saved jobs on LinkedIn and pull out the most sought-after technical skills.

## Project Description

This project automates the process of extracting job descriptions from your saved jobs list on LinkedIn. It navigates through multiple pages of your saved jobs, visits each job posting, extracts the HTML content of the description, and then uses the OpenAI API to identify and list technical skills mentioned in the description. The results (Job URL, Title, and Extracted Skills) are saved to a local file.

## Prerequisites

Before you run the script, ensure you have the following:

1.  **Python 3.7+:** Install Python from [python.org](https://www.python.org/).
2.  **pip:** Python's package installer (usually comes with Python).
3.  **Chrome Browser:** The script uses Selenium with ChromeDriver.
4.  **ChromeDriver:** Download the appropriate version for your Chrome browser from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromedriver.org/downloads). Make sure `chromedriver` is in your system's PATH.
5.  **A LinkedIn Account:** With saved jobs.
6.  **An OpenAI Account and API Key:** You can get one from the [OpenAI website](https://platform.openai.com/). **Note: Using the OpenAI API incurs costs.**

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd ai-job-scraping
    ```
    (Replace `<repository_url>` with the actual URL if you're using Git)

2.  **Install Python Packages:**
    ```bash
    pip install selenium openai
    ```

3.  **Set the OpenAI API Key Environment Variable:**
    The script reads your OpenAI API key from the environment variable `OPENAI_API_KEY`. This is the most secure way to use API keys without embedding them directly in your code.

    * **Windows:**
        * Search for "Environment Variables" in the Windows search bar.
        * Click "Edit the system environment variables".
        * Click the "Environment Variables..." button.
        * Under "User variables", click "New...".
        * Variable name: `OPENAI_API_KEY`
        * Variable value: Your actual OpenAI API key (`sk-...`)
        * Click OK on all windows. **You must restart your Command Prompt or PowerShell** for the changes to take effect.

    * **macOS / Linux:**
        * Open your terminal.
        * Edit your shell configuration file (`~/.bashrc`, `~/.zshrc`, `~/.profile`, etc.) using a text editor like `nano` or `vim`. For example:
            ```bash
            nano ~/.zshrc
            ```
        * Add the following line to the *end* of the file:
            ```bash
            export OPENAI_API_KEY='your_key_here'
            ```
            Replace `'your_key_here'` with your actual OpenAI API key.
        * Save the file and exit the editor.
        * Apply the changes by either closing and reopening your terminal, or running:
            ```bash
            source ~/.zshrc  # Or ~/.bashrc, ~/.profile, etc.
            ```

    * **Verification:** To check if the variable is set correctly, open a **new** terminal and run:
        * Windows (Command Prompt): `echo %OPENAI_API_KEY%`
        * Windows (PowerShell): `$env:OPENAI_API_KEY`
        * macOS / Linux: `echo $OPENAI_API_KEY`
        Your API key should be printed to the console.

4.  **Configure Script Settings:**
    Open the script file (`<your_script_file.py>`) in a text editor. Locate the `NUM_PAGES_TO_SCRAPE` constant near the top and change its value to the number of saved job pages you want to scrape. Each page typically contains 10 jobs.

## How to Run

1.  Ensure you have completed all steps in the Setup section.
2.  Open your terminal or command prompt where the `OPENAI_API_KEY` is set.
3.  Navigate to the project directory if you are not already there.
4.  Run the script:
    ```bash
    python <your_script_file.py>
    ```
    (Replace `<your_script_file.py>` with the actual name of your main Python script file).

5.  The script will open a Chrome browser window.
6.  **Manual Login Required (First Run or Expired Cookies):** The first time you run the script, or if your LinkedIn cookies expire, the script will navigate to the LinkedIn login page and pause, prompting you to log in manually in the browser window it opened. After you have logged in successfully, return to the terminal and press `Enter`. The script will then save your cookies for future runs.
7.  The script will proceed to navigate your saved jobs pages, visit individual job URLs (skipping those already processed), send descriptions to OpenAI, and save the results. Progress will be printed to the console.

## Output

The script will create or append to a file named `job_skills.txt` in the same directory. Each entry in the file will follow this format:
---
URL: https://www.linkedin.com/jobs/view/4140384354/
Title: Principal Air Defense Systems Engineer - Mission Systems Integration
Response:
<skills>
System Engineering
Engineering principles
Multi-disciplinary design
Requirements management
Systems design
Systems integration
Risk identification
Verification and Validation (V&V)
DOORS
Rhapsody
NoMagic
MATLAB
Model Based System Engineering (MBSE)
INCOSE standards
</skills>
---

The OpenAI response block will contain the list of technical skills extracted, wrapped in `<skills>...</skills>` tags as per the prompt.

## Files

* `<your_script_file.py>`: The main script containing the scraping and AI logic.
* `linkedin_cookies.pkl`: (Created after first successful manual login) Stores session cookies to attempt automatic login on subsequent runs.
* `job_skills.txt`: (Created/Appended) Contains the scraped job data and extracted skills.

## Disclaimer

Use this script responsibly and be aware of LinkedIn's Terms of Service regarding scraping. Excessive or rapid requests may lead to temporary or permanent account restrictions. The `human_wait()` function and the check for already processed URLs are included to help mitigate this risk, but responsible usage is up to the user. Also, remember that using the OpenAI API costs money based on usage.