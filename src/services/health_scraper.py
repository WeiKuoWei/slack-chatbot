import requests, os, asyncio, logging, csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urlunparse
from pyppeteer import launch
import time
import re

BASE_URL = "https://www.nyu.edu/life/safety-health-wellness/health-resources.html"
PDF_FOLDER = "saved_pdfs"

MENTAL_HEALTH_KEYWORDS = [
    "mental health", "counseling", "therapy", "psychological", 
    "psychiatry", "depression", "anxiety", "stress",
    "support group", "crisis", "emotional support", "mindfulness", "illness"
]

# Selenium Options
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--headless")  # Uncomment for headless mode

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.set_page_load_timeout(5)

visited = set()

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def normalize_url(url): #removes fragment identifiers
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))

def load_page_delay():
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        print("Page load timed out but continuing...")

def clickable_elements():
    elements = []
    try:
        main_content = driver.find_element(By.TAG_NAME, "main")
        potential_elements = main_content.find_elements(By.TAG_NAME, "a")
    except:
        potential_elements = driver.find_elements(By.TAG_NAME, "a")

    for element in potential_elements:
        try:
            href = element.get_attribute("href")
            if href and not href.startswith("mailto:"):  # Skip email links
                href = normalize_url(href)
                if "nyu.edu" in href and href not in visited:
                    elements.append(href)
        except:
            continue

    return elements

def page_contains_keywords():
    """Check if the page contains mental health-related keywords."""
    try:
        main_content = driver.find_element(By.TAG_NAME, "main").text.lower().strip()
    except:
        main_content = driver.page_source.lower().strip()

    matched_keywords = [kw for kw in MENTAL_HEALTH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", main_content)]

    return bool(matched_keywords), matched_keywords

async def save_pdf(url, pdf_filename):
    """Save the relevant page as a PDF using Pyppeteer."""
    pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        await page.goto(url)
        await page.pdf({'path': pdf_path, 'format': 'A4'})
        await browser.close()
        print(f"\n✅ Relevant page saved as {pdf_path}")
    except Exception as e:
        print(f"Failed to save {url} as PDF: {e}")

def dfs_scrape(url, max_depth=3):
    stack = [(normalize_url(url), 0)]  # (URL, depth)
    
    while stack:
        current_url, depth = stack.pop()

        if current_url in visited or depth > max_depth:
            continue

        print(f"\nVisiting (Depth {depth}): {current_url}")
        visited.add(current_url)

        try:
            driver.get(current_url)
            load_page_delay()
        except:
            print(f"Skipping {current_url} due to timeout.")
            continue

        contains_keywords, matched_keywords = page_contains_keywords()

        if contains_keywords:
            print(f"✅ Relevant page found! Keywords: {', '.join(matched_keywords)}")
            pdf_filename = f"relevant_page_{len(visited)}.pdf"
            asyncio.run(save_pdf(current_url, pdf_filename))
        else:
            print(f"❌ Skipping {current_url} (no relevant keywords)")
            continue

        new_links = clickable_elements()
        for href in reversed(new_links):
            if href not in visited:
                stack.append((href, depth + 1))  # Increase depth

    return visited

if __name__ == "__main__":
    all_links = dfs_scrape(BASE_URL)

    print("\nAll Scraped Links:")
    for link in sorted(all_links):
        print(link)

    driver.quit()