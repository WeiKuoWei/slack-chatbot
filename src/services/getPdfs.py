import requests, os, asyncio, logging, csv
from aspose.slides import Presentation
from aspose.slides.export import SaveFormat
from pyppeteer import launch
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# WEBPAGE_FOLDER = 'webpage_files'
PDF_FOLDER = 'pdf_files'
PPTX_FOLDER = 'pptx_files'

def get_all_hyperlinks(url, base_link):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        anchor_tags = soup.find_all('a')
        hyperlinks = [a.get('href') for a in anchor_tags if a.get('href')]

        hyperlinks = [link if link.startswith('http') else base_link + link for link in hyperlinks]

        with open('hyperlinks.csv', 'w') as f:
            for link in hyperlinks:
                f.write(f"{link}\n")

        return hyperlinks

    except requests.RequestException as e:
        logging.error(f"Failed to retrieve the page: {e}")
        return []

def filter_links(hyperlinks, base_link):
    filtered_links = [
        link for link in hyperlinks if '#' not in link and 
        base_link in link and 
        'php?' not in link
    ]
    return filtered_links

def download_file(url, folder):
    try:
        local_filename = url.split('/')[-1]
        local_filepath = os.path.join(folder, local_filename)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Downloaded {url} to {local_filepath}")
        return local_filename

    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return None

def convert_pptx_to_pdf(pptx_path, pdf_path):
    try:
        if not os.path.exists(pptx_path):
            logging.error(f"File not found: {pptx_path}")
            return

        # Load the presentation
        with Presentation(pptx_path) as presentation:
            # Save as PDF
            presentation.save(pdf_path, SaveFormat.PDF)
            logging.info(f"Converted {pptx_path} to {pdf_path}")

    except Exception as e:
        logging.error(f"Failed to convert {pptx_path} to PDF: {e}")

def convert_all_pptx_in_folder(PPTX_FOLDER, PDF_FOLDER):
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)

    for filename in os.listdir(PPTX_FOLDER):
        if filename.endswith('.pptx'):
            pptx_path = os.path.join(PPTX_FOLDER, filename)
            pdf_filename = filename.replace('.pptx', '.pdf')
            pdf_path = os.path.join(PDF_FOLDER, pdf_filename)
            convert_pptx_to_pdf(pptx_path, pdf_path)

async def convert_webpage_as_pdf(url, pdf_path):
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        await page.goto(url)
        await page.pdf({'path': pdf_path, 'format': 'A4'})
        await browser.close()
        logging.info(f"Converted {url} to {pdf_path}")

    except Exception as e:
        logging.error(f"Failed to convert {url} to PDF: {e}")

def create_folders(*folders):
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

# ---------------------------- Other helper functions ----------------------------

def read_hyperlinks(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        urls = [row[0] for row in reader]
    return urls

def match_filenames_to_urls(filenames, urls):
    matched_urls = {}
    for filename in filenames:
        for url in urls:
            if filename in url:
                matched_urls[filename] = url
                break
        else:
            matched_urls[filename] = None
    return matched_urls

# ---------------------------- Main function ----------------------------
def main():
    url = 'https://manual.eg.poly.edu/index.php/Main_Page'
    base_link = 'https://manual.eg.poly.edu'

    hyperlinks = get_all_hyperlinks(url, base_link)
    hyperlinks = filter_links(hyperlinks, base_link)

    create_folders(PPTX_FOLDER, PDF_FOLDER, PDF_FOLDER)

    # get the hyperlinks that are pptx and download them
    pptx_links = [link for link in hyperlinks if link.endswith('.pptx')]
    for link in pptx_links:
        download_file(link, PPTX_FOLDER)

    convert_all_pptx_in_folder(PPTX_FOLDER, PDF_FOLDER)

    # get the hyperlinks that are pdf and download them
    pdf_links = [link for link in hyperlinks if link.endswith('.pdf')]
    for link in pdf_links:
        download_file(link, PDF_FOLDER)

    # get the hyperlinks that are webpages and convert them to pdf
    webpage_links = [link for link in hyperlinks if not link.endswith('.pdf') and not link.endswith('.pptx')]
    loop = asyncio.get_event_loop()
    for link in webpage_links:
        local_filename = link.split('/')[-1] + '.pdf'
        pdf_path = os.path.join(PDF_FOLDER, local_filename)
        loop.run_until_complete(convert_webpage_as_pdf(link, pdf_path))

if __name__ == "__main__":
    main()

