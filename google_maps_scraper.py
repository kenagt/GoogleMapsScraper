import json
import time
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options  # Import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_number(text):
    """
  Extracts a floating-point number from a string, handling different decimal separators.

  Args:
    text: The input string containing the number.

  Returns:
    A float representing the extracted number, or None if no number is found.
  """
    if not isinstance(text, str):
        return None  # or raise TypeError("Input must be a string")

    # Replace commas with periods (European decimal style)
    text = text.replace(",", ".")

    # Use a regular expression to find a floating-point number
    match = re.search(r"[-+]?\d*\.?\d+", text)  # Matches integers or floats

    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None  # Handle cases where the matched string isn't a valid float
    else:
        return None


def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '',
                  text).strip()  # Keep only ASCII characters


def is_open_24_hours(hours_text):
    # Define a pattern to match opening hours like "9 AM–10 PM" or "9AM-10PM"
    time_pattern = r"(\d{1,2}[:\.]?\d{0,2}\s?(AM|PM)?\s?[-–]\s?(\d{1,2}[:\.]?\d{0,2}\s?(AM|PM)?))"

    # Split the schedule into lines and loop over them
    lines = hours_text.splitlines()

    # Check for each line
    for line in lines:
        # If there is a specific time range for the day, check if it indicates non-24 hour operation
        if re.search(time_pattern, line):
            times = line.split("–")
            if len(times) == 2:
                start_time = times[0].strip()
                end_time = times[1].strip()

                # If start time and end time don't indicate a 24-hour period, return False
                if start_time != "12 AM" or end_time != "12 AM":
                    return False
    return True


def scrape_google_maps_urls(search_query, driver):
    if search_query is not None:
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'searchboxinput')))

            # Type the search query and press Enter
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)

            # Wait for the search results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'hfpxzc')))
        except:
            # If an exception occurs, retry the code block after a short delay
            time.sleep(5)
            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'searchboxinput')))
                search_box.send_keys(search_query)
                search_box.send_keys(Keys.RETURN)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'hfpxzc')))
            except:
                # If the problem persists, print an error message and exit the script
                print("Error: Failed to load search results")
                logger.error(f"Failed to load search results")
                driver.quit()
                exit()

    # Google maps and results are successfully loaded
    # Initialize the output list
    urls = []

    while True:
        try:
            # Find all the businesses in the search results
            businesses = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'hfpxzc')))
        except:
            # If no businesses are found, break the loop
            break

        time.sleep(5)

        # Store the URLs of the businesses
        for business in businesses:
            url = business.get_attribute('href')
            if url not in urls:
                urls.append(url)

        logger.info(f"Loaded URL number: {str(len(urls))}")

        ###COMMENT
        #break

        ###UNCOMMENT
        # Scroll down to load more businesses
        driver.execute_script("arguments[0].scrollIntoView();", businesses[-1])
        time.sleep(5)
        try:
            # Check if new businesses are loaded
            new_businesses = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'hfpxzc')))
            if len(new_businesses) == len(businesses):
                # If no new businesses are loaded, break the loop
                break
        except:
            # If an exception occurs, break the loop
            break

    return urls


def scrape_url_data(google_url, chrome_options):
    """Scrapes data from a single business URL."""
    try:
        driver = webdriver.Chrome(
            options=chrome_options)  #Pass the chrome_options
        logger.info(f"Scraping URL: {google_url}")
        driver.get(google_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")))

        # name of property
        try:
            name = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'lfPIob'))).text)

            if not name:
                name = "N/A"
        except Exception as e:
            name = "N/A"
            logger.error(f"name: {e}")

        # link to the hotels website
        try:
            url = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         "[data-item-id*='authority']"))).text)

            if not url:
                url = "N/A"
        except Exception as e:
            url = "N/A"
            logger.error(f"url: {e}")

        # address
        try:
            address = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-item-id*='address']"))).text)

            if not address:
                address = "N/A"
        except Exception as e:
            address = "N/A"
            logger.error(f"address: {e}")

        # phone number
        try:
            phone = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-item-id*='phone']"))).text)

            if not phone:
                phone = "N/A"
        except Exception as e:
            phone = "N/A"
            logger.error(f"phone: {e}")

        # working hours
        try:
            workingHoursHtml = driver.page_source
            soup = BeautifulSoup(workingHoursHtml, 'html.parser')
            table = soup.find("table", class_="eK4R0e fontBodyMedium")

            # Check if table is found
            if table:
                # Find all <ul> tags with class "G8aQO"
                ul_elements = table.find_all("ul", class_="G8aQO")

                # Iterate through the ul elements and check for "closed"
                for ul in ul_elements:
                    if is_open_24_hours(ul.get_text().lower()):
                        workingHours = "Open 24 hours"
                    else:
                        workingHours = "Not open 24 hours"
            else:
                workingHours = "Open 24 hours"

            if not workingHours:
                workingHours = "Open 24 hours"
        except Exception as e:
            workingHours = "N/A"
            logger.error(f"workingHours: {e}")

        # Number of reviews
        try:
            numberOfReviewsElement = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'rqjGif')))

            # Using Selenium's get_attribute('outerHTML')
            numberOfReviewsHtml = numberOfReviewsElement.get_attribute(
                'outerHTML')
            soup = BeautifulSoup(numberOfReviewsHtml, 'html.parser')

            # Find all span elements
            spans = soup.find_all('span')

            # Extract the text content from each span and create a comma-separated string
            numberOfReviews = [span.text for span in spans]
            numberOfReviews = ", ".join(numberOfReviews)
            numberOfReviews = str(extract_number(numberOfReviews)).replace(
                ".", "")

            if not numberOfReviews:
                numberOfReviews = "N/A"
        except Exception as e:
            numberOfReviews = "N/A"
            logger.error(f"numberOfReviews: {e}")

        # average review score
        try:
            averageReviewScoreHtml = driver.page_source
            soup = BeautifulSoup(averageReviewScoreHtml, 'html.parser')
            div = soup.find("div", "fontDisplayLarge")

            averageReviewScore = div.text

            if not averageReviewScore:
                averageReviewScore = "N/A"
                print("averageReviewScore: " + averageReviewScore)
        except Exception as e:
            averageReviewScore = "N/A"
            logger.error(f"averageReviewScoreHtml: {e}")

        # checkInOutTimes
        try:
            checkInOutTimesElement = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-item-id*='place-info-links:']")))
            checkInOutTimesHtml = checkInOutTimesElement.get_attribute(
                'outerHTML')

            soup = BeautifulSoup(checkInOutTimesHtml, 'html.parser')

            # Extract the text content from each span and create a comma-separated string
            spans = soup.find_all('span')
            checkInOutTimes = [span.text for span in spans]
            checkInOutTimes = [
                clean_text(string) for string in checkInOutTimes
            ]
            checkInOutTimes = [s for s in checkInOutTimes if s.strip()]
            checkInOutTimes = " - ".join(checkInOutTimes)

            if not checkInOutTimes:
                checkInOutTimes = "N/A"
        except Exception as e:
            checkInOutTimes = "N/A"
            logger.error(f"checkInOutTimes: {e}")

        # amenities
        try:
            amenities_element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'WKLD0c')))

            # Using Selenium's get_attribute('outerHTML')
            amenities_html = amenities_element.get_attribute('outerHTML')

            soup = BeautifulSoup(amenities_html, 'html.parser')
            spans = soup.find_all('span')

            # Extract the text content from each span and create a comma-separated string
            amenities = [clean_text(span.text) for span in spans]
            amenities = [s for s in amenities if s.strip()]
            amenities = ", ".join(amenities)

            if not amenities:
                amenities = "N/A"
        except Exception as e:
            amenities = "N/A"
            logger.error(f"amenities: {e}")

        # Number of OTAs
        try:
            # Wait for the "Prices" tab and click it
            price_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@class='hh2c6 ']")))
            price_tab.click()
            # Allow time for prices to load
            time.sleep(3)

            numberOfOTAsHtml = driver.page_source
            soup = BeautifulSoup(numberOfOTAsHtml, 'html.parser')

            # Find all span elements
            spans = soup.find_all('span', class_='QVR4f fontTitleSmall')

            # Extract the text content from each span and create a comma-separated string
            numberOfOTAs = [span.text for span in spans]
            numberOfOTAs = str(len(numberOfOTAs))

            if not numberOfOTAs:
                numberOfOTAs = "N/A"
        except Exception as e:
            numberOfOTAs = "N/A"
            logger.error(f"numberOfOTAs: {e}")

        # OTA links
        try:
            numberOfOTAsLinksHtml = driver.page_source
            soup = BeautifulSoup(numberOfOTAsLinksHtml, 'html.parser')

            # Find all a elements
            atags = soup.find_all('a', class_='SlvSdc co54Ed')
            hrefs = [a['href'] for a in atags if 'href' in a.attrs]

            # Extract the text content from each span and create a comma-separated string
            otaLinks = ", ".join(hrefs)

            if not otaLinks:
                otaLinks = "N/A"
        except Exception as e:
            otaLinks = "N/A"
            logger.error(f"otaLinks: {e}")

        # Calculate average OTA price
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find all div elements
            divs = soup.find_all('div', class_='fontLabelMedium pUBf3e oiQUX')

            # Extract the text content from each span and create a comma-separated string
            averageOtaPrice = [extract_number(div.text) for div in divs]
            if len(averageOtaPrice) > 0:
                averageOtaPrice = str(
                    round(sum(averageOtaPrice) / len(averageOtaPrice), 2))
            else:
                averageOtaPrice = "N/A"

        except Exception as e:
            averageOtaPrice = "N/A"
            logger.error(f"averageOtaPrice: {e}")
            logger.error(f"averageOtaPrice: {e.__traceback__.tb_lineno}")

        # Social media links
        if url != "N/A":
            try:
                driver.get("https://" + url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body")))

                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                # Define regex pattern for social media domains
                social_media_pattern = re.compile(
                    r"(facebook\.com|linkedin\.com|instagram\.com|youtube\.com|twitter\.com)"
                )

                # Find all <a> tags with social media links
                links = soup.find_all("a", href=social_media_pattern)

                # Extracted links
                socialMediaLinks = [link["href"] for link in links]
                socialMediaLinks = ", ".join(socialMediaLinks)

                if not socialMediaLinks:
                    socialMediaLinks = "N/A"
            except Exception as e:
                socialMediaLinks = "N/A"
                logger.error(f"socialMediaLinks: {e}")
                logger.error(f"socialMediaLinks: {__file__}")
                logger.error(f"socialMediaLinks: {e.__traceback__.tb_lineno}")
        else:
            socialMediaLinks = "N/A"

        # emails - It is connected to email and Google Places API.
        # I have included into scraping now, but it is not used (commented out).
        # Scraping emails is not an issue, but guessing contact page is, so results may vary.
        #if url != "N/A":
        #    possible_contact_page_urls = ["/about", "/contact", "/contact-us"]
        #    for possible_path in possible_contact_page_urls:
        #        contact_page_url = url.rstrip("/") + possible_path

        #        try:
        #            driver.get("https://" + contact_page_url)
        #            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        #            html = driver.page_source
        #            soup = BeautifulSoup(html, 'html.parser')
        #            text = soup.get_text()
        #            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?", text)

        #            if emails:
        #                email = emails[0]
        #            else:
        #                email = "N/A"

        #        except Exception as e:
        #            emails = "N/A"
        #            logger.error(f"emails: {e}")
        #            logger.error(f"emails: {e.__traceback__.tb_lineno}")
        #else:
        #    email = "N/A"

        driver.quit()  #Quit driver after usage

        logger.info(f"Finished scraping URL: {google_url}")

        return {
            "name": name,
            "phone": phone,
            "url": url,
            "googleMapsUrl": google_url,
            "address": address,
            "numberOfReviews": numberOfReviews,
            "averageReviewScore": averageReviewScore,
            "checkInOutTimes": checkInOutTimes,
            "amenities": amenities,
            "numberOfOTAs": numberOfOTAs,
            "otaLinks": otaLinks,
            "averageOtaPrice": averageOtaPrice,
            "socialMediaLinks": socialMediaLinks,
            "workingHours": workingHours
            #"email": email
        }

    except Exception as e:
        logger.error(f"Error scraping : {e}")
        logger.error(f"Error scraping : {__file__}")
        logger.error(f"Error scraping : {e.__traceback__.tb_lineno}")
        return None


def write_to_csv():
    # Load JSON file
    json_file = "google_maps_results.json"  # Change to your JSON file path
    df = pd.read_json(json_file)

    # Convert to CSV
    csv_file = "google_maps_results.csv"
    df.to_csv(csv_file, index=False)

    logger.info(f"CSV file saved as {csv_file}")


def write_to_json(data, filename):
    """Writes the scraped data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:  # Specify encoding
            json.dump(data, f, indent=4, ensure_ascii=False
                      )  # Pretty print and handle non-ASCII characters
        logger.info(f"Data written to {filename}")
    except Exception as e:
        logger.error(f"Error writing to JSON file: {e}")


def perform_scraping():
    """Main scraping function."""
    global progress, scraped_data
    progress = 0  # Reset progress
    scraped_data = []  # Reset scraped data

    # Set up Chrome options for headless mode# Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    # Optionally, disable GPU if you encounter issues in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=1")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option(
        'prefs', {'intl.accept_languages': 'en,en_US'})
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(
            options=chrome_options)  #Pass the chrome_options
    except Exception as e:
        logger.error(f"Error setting chrome: {e}")
        exit()

    # It is much easier to use Google maps API, parameterized search like lat, lng, radius of search etc.
    # Also JSON is much easier to handle in app instead of plain scraping with Selenium and ChromeDriver :)
    # Also, this was intended to use search_query, but for ease of use, url that is used is url for nearby hotels provided by your url.
    # Could have used Google Places API, but that does not come for free. Check pricing here: https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
    # Probably with this small amount of API calls it is free, but from 10K calls/maps and above, it becomes costly.
    # So I did not opted for Google Maps API solution, and I have moved with plain scraping using Selenium and ChromeDriver.
    # It is harder to scrape data, then to fetch through API, but this depends on company policies, budget, requirements etc.
    # Most of scraping I have done this way, just like most of AI companies did :)
    driver.get(
        "https://www.google.com/maps/search/Hotels/@30.3736662,-86.5128752,12z/data=!4m5!2m4!5m3!5m2!1s2025-03-01!2i3?authuser=0&entry=ttu&g_ep=EgoyMDI1MDIyNi4xIKXMDSoASAFQAw%3D%3D"
    )

    try:
        search_query = None
        urls = scrape_google_maps_urls(search_query, driver)
        num_processes = multiprocessing.cpu_count(
        )  # Use all available cores or adjust as needed

        logger.info(f"Final scrolled URL number: {str(len(urls))}")
        write_to_json(urls, "google_maps_results_urls.json")

        with multiprocessing.Pool(processes=num_processes) as pool:
            # Map the scraping function to the URLs
            results = pool.starmap(
                scrape_url_data,
                [(google_url, chrome_options)
                 for google_url in urls])  #Pass chrome_install one time

        # Filter out None results and format the output
        scraped_data = [result for result in results if result is not None]

        # Write the data to the JSON file
        write_to_json(scraped_data, "google_maps_results.json")

        # Write the data to the CSV file
        write_to_csv()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"An error occurred: {__file__}")
        logger.error(f"An error occurred: {e.__traceback__.tb_lineno}")
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    perform_scraping()
