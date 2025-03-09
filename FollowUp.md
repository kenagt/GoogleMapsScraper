# AI-Powered Software Architect Test Project

## 1. Google Hotels Web Scraping

**Task:** Please scrape as many contacts as possible within a 5 km radius of this hotel location: [https://maps.app.goo.gl/JdqecKy3kz45QSJ26](https://maps.app.goo.gl/JdqecKy3kz45QSJ26)

### 1.a Expected Data (**DONE**)

*   Includes:
    *   Name of property (**DONE**)
    *   Address (**DONE**)
    *   Phone number (**DONE**)
    *   Link to the hotel's website (**DONE**)
    *   Handle missing or incomplete data gracefully (e.g., replace missing fields with "N/A"). (**DONE**)

### 1.b BONUS Items

*   **Email address:** **COMMENT:** Response from Google: No. Google Maps is an ever-expanding database of free business data: marketers can find place names, addresses, phone numbers, and official websites. However, Google Maps does not provide information on business email addresses or social media accounts to reach out through.
*   **Number of reviews:** (**DONE**)
*   **Date range of reviews** (earliest review available to most recent published review): **COMMENT:** There is only a filter for the most recent review. Google search response: Since January 2024, it appears this is no longer possible. Link: [https://support.google.com/maps/thread/224565577/how-do-i-sort-the-reviews-on-places-shown-on-google-maps-by-date?hl=en](https://support.google.com/maps/thread/224565577/how-do-i-sort-the-reviews-on-places-shown-on-google-maps-by-date?hl=en)
*   **Average review score:** (**DONE**)
*   **Name of other OTA** (listing sites where listed, like Booking.com) links to those OTAs: (**DONE**)
*   **Check-in and check-out times:** (**DONE**)
*   **Number of OTAs listed:** (**DONE**)

### 1.c EXTRA BONUS Items

*   **Is there 24-hour reception?:** (**DONE**)
*   **Indicated price on calendar for July 4th:** **COMMENT:** This includes a calendar/date picker to choose check-in/check-out dates. This needs more time to play with the calendar. The rest is the same as scraping OTAs, as compliant OTA prices are shown after the date picker is closed.
*   **Comma-delimited amenities in a single cell:** (**DONE**)
*   **Segmented TripAdvisor reviews from Google:** **COMMENT:** For this task, the Google Places Maps API would be more suitable, but that does not come free. The reason for this is that fetching hundreds of reviews might be resource-hungry.
*   **Social media links from the direct booking website:** (**DONE**) (Comma-delimited!)

### 1.d BONUS CHATGPT Analysis

*   Identify all the review scores and identify the top three negative mentions in the review (ie. cleanliness, communication, location, etc.): **COMMENT:** Could not do this as I needed a paid ChatGPT API key for sentiment analysis, which I do not have currently. For this task, the Google Places Maps API would be more suitable, but that does not come free. The reason for this is that fetching hundreds of reviews might be resource-hungry.

## 2. Data Organization

*   Store the scraped data in a structured format in CSV format. (**DONE**)
*   Ensure the CSV includes separate columns for each data point (ie. hotel_name, review count, email message, etc.). (**DONE**)

## 3. Personalized Email Generation (ChatGPT)

**COMMENT:** I do not have access to the ChatGPT API, which is paid.

Create a script to generate customized email content using the scraped data. The goal for the personalized message is to use it as sales outreach. The formatting for the email:

*   Include an email subject.
*   100 words max.
*   Personalized as much as possible based on scraped data (identifying opportunities for improvement with the hotel).
*   Uploaded as an entry in a cell to the CSV file.
*   Explain how this might be integrated automatically with a CRM system.  **COMMENT:** Integration depends on the existing dashboard, if you have one. Otherwise, create a dashboard in any stack, then integrate the scraping script with the dashboard. Also, the scraping script can include API calls like this, or somewhere else in the Dashboard app. The stack can be either Flask/FastAPI (Python-based) or NodeJS/ReactJS (JS-based backend and frontend), .NET, etc. Also, we might consider using a data warehouse when data grows. That is a common case for marketing companies, that either get campaign results in big files/streams or web scraping results. PostgreSQL is one option for temp data, then using any tool like Snowflake to digest that data in a meaningful way. Note: I have used this API two or three times, but I was not paying for it, so it is not hard to implement this :)

## Deliverables

*   A deployed App from Replit that scrapes as many hotel data contacts as possible within a 5 km radius of this hotel location: [https://maps.app.goo.gl/JdqecKy3kz45QSJ26](https://maps.app.goo.gl/JdqecKy3kz45QSJ26)
*   CSV file with cleanly organized scraped results and personalized emails (in its own column) ready for potential upload to a CRM system.
*   Video explanation of the app, how it functions, the results you were able to achieve, and how you think you could improve the app if you had 20 hours? (Please keep the video to a max of 5 minutes).
    *   Feel free to include a written explanation of anything as well if you feel necessary.

---

## Google Maps API vs Selenium & ChromeDriver - mix of solutions
It is much easier to use Google maps API, parameterized search like lat, lng, radius of search etc.
Also JSON is much easier to handle in app instead of plain scraping with Selenium and ChromeDriver :)
Also, this was intended to use search_query, but for ease of use, url that is used is url for nearby hotels provided by your url.
Could have used Google Places API, but that does not come for free. Check pricing here: https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
Probably with this small amount of API calls it is free, but from 100.000 calls/maps and above, it becomes costly.
So I did not choose Google Maps API solution, and I have moved with plain scraping using Selenium and ChromeDriver.
It is harder to scrape data, then to fetch through API, but this depends on company policies, budget, requirements etc.
Most of scraping I have done this way, just like most of AI companies did :)
Also, there might be mix of those two approaches, for best results. Fetching data from Google Maps API and then fetching website data using Selenium and Webscraping for thata that is not
present in API.

## Summary of Tasks and Code Explanation

Here is the summary of tasks that are finished. Tasks that are finished are marked as "**DONE**". I had an idea to host this app/Python script somewhere, BUT, the script is using multitasking/multiprocessing, and it spawns a number of threads depending on your CPU core count. This is used to increase the speed of scraping for this task.

### ZERO: `perform_scraping()`

This function is the main scraping function. It is setting up Selenium with ChromeDriver and using `headless` and `--disable-gpu` options to set up the scraping tool.

### FIRST: `scrape_google_maps_urls(search_query, driver)`

This function is fetching all URLs for nearby hotels for a fixed URL on Google Maps. It is using ChromeDriver with Selenium to scrape initial data and to scroll down until the end is reached. Those URLs are put into an array that is later used to scrape individual hotel data.

So, by searching the ID for the Google Maps search box, `"searchboxinput"`, I am sending keys to the search box depending on the query that you want. In our example, that is fixed, and `search_query = None`. The reason for that is that you have already sent the URL for the search, so I am not making this dynamically, but it can be made that way.

The next part is scraping URLs for each result. This means that we need to use Selenium to scroll when the end is reached and to check if new records exist (infinite scroll). This is done with this line:

```python
driver.execute_script("arguments[0].scrollIntoView();", businesses[-1])