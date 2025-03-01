import requests, os, asyncio, logging, csv
import sys
import asyncio 
import traceback
import pdfkit
from aspose.slides import Presentation
# from aspose.slides.export import SaveFormat
from pyppeteer import launch
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


#Alternative getPdf script as we continuously fail at 

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

PDF_FOLDER = 'pdf_files'
PPTX_FOLDER = 'pptx_files'
URL_FILENAME = 'hyperlinks.csv'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(PPTX_FOLDER, exist_ok=True)

def get_all_hyperlinks(url, base_link):
    """Extracts all hyperlinks from a webpage and saves to CSV."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        anchor_tags = soup.find_all('a')

        hyperlinks = []
        hyperlink_pairs = []  # For CSV storage (link, text)

        for a in anchor_tags:
            href = a.get('href')
            text = a.get_text(strip=True)
            if href:
                link = href if href.startswith('http') else base_link + href
                hyperlinks.append(link)  # Store only the URL for later use
                hyperlink_pairs.append((link, text))  # Store both for CSV

        # Save both link + text to CSV
        with open(f'{CURRENT_DIR}/{URL_FILENAME}', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Link', 'Text'])
            writer.writerows(hyperlink_pairs)

        print(f"Extracted {len(hyperlinks)} links.")
        return hyperlinks  # Return only the URLs for further processing

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
    local_filename = os.path.basename(url)
    local_filepath = os.path.join(folder, local_filename)

    if os.path.exists(local_filepath):
        logging.info(f"File already exists: {local_filepath}, skipping download.")
        return local_filepath

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Downloaded {url} to {local_filepath}")
        return local_filepath

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
            presentation.save(pdf_path, SaveFormat.Pdf)
            #presentation.save(pdf_path, 32)
            logging.info(f"Converted {pptx_path} to {pdf_path}")

    except Exception as e:
        traceback.print_exc()
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
    #going to try pdfkit
    try:
        browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.newPage()
        await page.goto(url)
        await page.pdf({'path': pdf_path, 'format': 'A4'})
        await browser.close()
        logging.info(f"Converted {url} to {pdf_path}")

    except Exception as e:
        traceback.print_exc()
        logging.error(f"Failed to convert {url} to PDF: {e}")
def webpage_to_pdf(url, pdf_path):
    """Converts a webpage to PDF and saves it in the pdf_files folder."""
    try: 
        pdf = pdfkit.from_url(url, pdf_path)
        logging.info(f"Converted {url} to {pdf_path}")
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Failed to convert {url} to PDF: {e}")
        return None

    return pdf

def create_folders(*folders):
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

def match_filenames_to_urls(filenames, urls_with_texts):
    matched_urls = {}
    for filename in filenames:
        for url, text in urls_with_texts:
            if filename in url:
                matched_urls[filename] = (url, text)
                break
        else:
            matched_urls[filename] = (None, "Description not found")
    return matched_urls

async def process_all_links(pdf_links, pptx_links, webpage_links):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    #from database.crudChroma import CRUD

    #crud = CRUD()  # Initialize CRUD for saving PDFs

    # print(f"Pdf links stored: {len(pdf_links)} ")

    # # Step 1: Download PDFs (THIS WORKS)
    # if pdf_links:
    #     print("Downloading PDFs...")
    #     for link in pdf_links:
    #         download_file(link, PDF_FOLDER)

    print(f"pptx links stored: {len(pptx_links)} ")

    # Step 2: Download & Convert PPTX to PDFs
    # Issue: No usable version of libssl was found Aborted (core dumped)
    # Need to find a different way to convert pptx to pdf
    # if pptx_links:
    #     print("Downloading and converting PPTX files...")
    #     for link in pptx_links:
    #         download_file(link, PPTX_FOLDER)

    #     # Convert all downloaded PPTX files into PDFs
    #     convert_all_pptx_in_folder(PPTX_FOLDER, PDF_FOLDER)

    # Step 3: Convert Webpages to PDFs
    # WORKS!!!
    if webpage_links:
        print("Converting webpages to PDFs...")
        tasks = []
        for link in webpage_links:            
            filename = link.split("/")[-1] + ".pdf"  # Generate a filename
            pdf_path = os.path.join(PDF_FOLDER, filename)
            #webpage_to_pdf(link, pdf_path)
            tasks.append(asyncio.to_thread(webpage_to_pdf(link, pdf_path)))

            # tasks.append(convert_webpage_as_pdf(link, pdf_path))

    #     # Run all conversions asynchronously
    await asyncio.gather(*tasks)
    

    # # Step 4: Save All PDFs into ChromaDB
    # print("Processing PDFs and saving them to ChromaDB...")
    # await crud.save_pdfs(PDF_FOLDER, "course_materials")

    print("All materials have been processed and stored.")

async def main():

    # crud = CRUD()  # Initialize CRUD for saving PDFs
    # await crud.save_pdfs(PDF_FOLDER, "course_materials")
    url = 'https://manual.eg.poly.edu/index.php/Main_Page'
    base_link = 'https://manual.eg.poly.edu'

    print("Extracting hyperlinks...")
    hyperlinks = get_all_hyperlinks(url, base_link)
    # print(f"Before filtration: {hyperlinks}")
    # Properly seperates links, fits into what we need. One pdf a bunch of webpages and some slides
        # pdf_links = [link for link in hyperlinks if link.endswith('.pdf')]
        # webpage_links = [link for link in hyperlinks if not link.endswith('.pdf') and not link.endswith('.pptx')]
        # pptx_links = [link for link in hyperlinks if link.endswith('.pptx')]
        # print(f"PDFS: {pdf_links} /n Webpages: {webpage_links} /n PPTX: {pptx_links}")

    hyperlinks = filter_links(hyperlinks, base_link)
    # print(f"After filtration: {hyperlinks}")

    # # Separate links
    pdf_links = [link for link in hyperlinks if link.endswith('.pdf')]
    webpage_links = [link for link in hyperlinks if not link.endswith('.pdf') and not link.endswith('.pptx')]
    pptx_links = [link for link in hyperlinks if link.endswith('.pptx')]

    print(f"{len(pdf_links) + len(webpage_links) + len(pptx_links)} links found.") # Should be 60 total links.
    print(f"PDFs: {len(pdf_links)} | Webpages: {len(webpage_links)} | PPTX: {len(pptx_links)}") # Should be 20 each.
    print(f"PDFS: {pdf_links} /n Webpages: {webpage_links} /n PPTX: {pptx_links}")
    
    await process_all_links(pdf_links, pptx_links, webpage_links)

    # create_folders(PPTX_FOLDER, PDF_FOLDER, PDF_FOLDER)

    # # get the hyperlinks that are pptx and download them
    # pptx_links = [link for link in hyperlinks if link.endswith('.pptx')]
    # for link in pptx_links:
    #     download_file(link, PPTX_FOLDER)

    # convert_all_pptx_in_folder(PPTX_FOLDER, PDF_FOLDER)

    # # get the hyperlinks that are pdf and download them
    # pdf_links = [link for link in hyperlinks if link.endswith('.pdf')]
    # for link in pdf_links:
    #     download_file(link, PDF_FOLDER)

    # # get the hyperlinks that are webpages and convert them to pdf
    # webpage_links = [link for link in hyperlinks if not link.endswith('.pdf') and not link.endswith('.pptx')]
    # loop = asyncio.get_event_loop()
    # for link in webpage_links:
    #     local_filename = link.split('/')[-1] + '.pdf'
    #     pdf_path = os.path.join(PDF_FOLDER, local_filename)
    #     loop.run_until_complete(convert_webpage_as_pdf(link, pdf_path))


if __name__ == "__main__":
    asyncio.run(main())
