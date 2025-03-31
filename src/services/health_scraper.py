from openai import OpenAI
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
import matplotlib.pyplot as plt

import time
import re

client = OpenAI(api_key = "API_KEY")
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
        WebDriverWait(driver, 1.5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except:
        print("Page load timed out or still loading... continuing anyway.")


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

def check_relevance_with_openai(page_content):
    """
    Use OpenAI API to determine if the page is relevant to mental health resources.
    
    Args:
        page_content (str): The text content of the webpage
        
    Returns:
        tuple: (is_relevant, explanation)
    """

    max_content_length = 4000
    if len(page_content) > max_content_length:
        page_content = page_content[:max_content_length] + "..."
    
    try:
        prompt = f"""
        Task: Determine if the following webpage content is relevant to mental health resources.
        
        Context: I'm looking for mental health resources at NYU, including counseling services, 
        psychological support, therapy options, crisis intervention, wellness programs, 
        or any resources related to anxiety, depression, stress management, or emotional wellbeing.
        
        Webpage content: 
        {page_content}
        
        Is this webpage relevant to mental health resources? 
        Answer YES if it contains information about mental health services, resources, support, 
        or wellbeing that would be useful for someone seeking mental health assistance.
        Answer NO if it doesn't contain relevant mental health information.
        
        Format your response as:
        RELEVANT: YES/NO
        REASON: Brief explanation
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates webpage content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        
        is_relevant = "RELEVANT: YES" in result
        reason = result.split("REASON:")[1].strip() if "REASON:" in result else "No reason provided"
        
        return is_relevant, reason
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        matched_keywords = [kw for kw in [
            "mental health", "counseling", "therapy", "psychological", 
            "psychiatry", "depression", "anxiety", "stress",
            "support group", "crisis", "emotional support", "mindfulness", "illness"
        ] if re.search(rf"\b{re.escape(kw)}\b", page_content.lower())]
        
        return bool(matched_keywords), f"Fallback keyword match: {', '.join(matched_keywords) if matched_keywords else 'none'}"

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
    relevant_count = 0  # Track number of relevant links found
    
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
        
        try:
            main_content = driver.find_element(By.TAG_NAME, "main").text.strip()
        except:
            main_content = driver.find_element(By.TAG_NAME, "body").text.strip()

        is_relevant, reason = check_relevance_with_openai(main_content)

        if is_relevant:
            print(f"✅ Relevant page found! Reason: {reason}")
            pdf_filename = f"relevant_page_{len(visited)}.pdf"
            asyncio.run(save_pdf(current_url, pdf_filename))
            
            with open('relevant_pages.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if os.path.getsize('relevant_pages.csv') == 0:
                    writer.writerow(['URL', 'Reason', 'Depth'])
                writer.writerow([current_url, reason, depth])
            
        else:
            print(f"❌ Skipping {current_url} (not relevant: {reason})")
            continue

        new_links = clickable_elements()
        for href in reversed(new_links):
            if href not in visited:
                stack.append((href, depth + 1))  

    return relevant_count  


if __name__ == "__main__":
    # depths = list(range(0, 11))
    # relevant_links_found = []

    # for depth in depths:
    #     visited.clear()  
    #     driver = webdriver.Chrome(service=service, options=chrome_options)  
    #     count = dfs_scrape(BASE_URL, max_depth=depth)
    #     relevant_links_found.append(count)
    #     driver.quit()
    with open('relevant_pages.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'Reason', 'Depth'])
        
    visited.clear()  
    driver = webdriver.Chrome(service=service, options=chrome_options)  
    count = dfs_scrape(BASE_URL, max_depth=7)
    driver.quit()

    # Plot the results
    # plt.figure(figsize=(8, 6))
    # plt.plot(depths, relevant_links_found, marker='o', linestyle='-', color='b')
    # plt.xlabel("Max Depth")
    # plt.ylabel("Number of Relevant Links Found")
    # plt.title("Max Depth vs. Number of Relevant Links Found")
    # plt.grid()
    # plt.show()