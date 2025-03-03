AI-Powered Software Architect Test Project 

1. **Google Hotels Web Scraping:**
Please scrape as many contacts as possible within a 5 km radius of this hotel location [https://maps.app.goo.gl/JdqecKy3kz45QSJ26] 
    1. **Expected data**  - DONE
		includes: name of property,  - DONE
		address,  - DONE
		phone number,  - DONE
		and a link to the hotels website.  - DONE
		(Handle missing or incomplete data gracefully (e.g., replace missing fields with "N/A"). - DONE
    2. **BONUS items**: 
			**email address**, - COMMENT: Response from Google: No. Google Maps is an ever-expanding database of free business data: marketers can find place names, addresses, phone numbers, and official websites. However, Google Maps does not provide information on business email addresses or social media accounts to reach out through.
			# of reviews, - DONE
			date range of reviews (earlies review available to most recent published review), - COMMENT: There is only filter for most recent review. Google search response: Since January 2024, it appears this is no longer possible. Link: https://support.google.com/maps/thread/224565577/how-do-i-sort-the-reviews-on-places-shown-on-google-maps-by-date?hl=en
			average review score, - DONE
			name of other OTA (listings sites wehre listed, like Booking.com) links to those OTAs, - DONE
			check in and check out times, - DONE
			# of OTAs listed - DONE
    3. **EXTRA BONUS** items would include:  
			is there 24 hour reception? - DONE
			indicated price on calendar for July 4th, - COMMENT: This includes calendar/date picker, to choose check in/check out dates. 
																 This need more time to play with calendar. 
																 Rest is the same as scraping OTAs, as compliant OTA prices are showing after date picker is closed.
			comma deliminated ammenities in a single cell, - DONE
			segmented Tripadvisor reviews from Google, - COMMENT: For this task maybe google places maps api would be more suitable, but that does not come free. Reason for this is that fetching hunderds of reviews might be resource hungry 
			social media links from direct booking website, - DONE (Comma delimited!)

    4. **BONUS CHATGPT Analysis**: 
		identify all the review scores and identify the top three negative mentions in the review (ie. cleanliness, communication, location etc) - 
		COMMENT: Could not do this as I needed paid ChatGPT API key for sentiment analysis which I do not have currently.
		For this task maybe google places maps api would be more suitable, but that does not come free. Reason for this is that fetching hunderds of reviews might be resource hungry 
		
2. **Data Organization:**
    1. Store the scraped data in a structured format in CSV format. - DONE
    2. Ensure the CSV includes separate columns for each data point (ie. hotel_name, review count, email message ect) - DONE
    
3. **Personalized Email Generation (Chat GPT):** - COMMENT: I do not have access to chat gpt API which is paid. 
Create a script to generate customized email content using the scraped data. The goal for the personalized message is to use it as sales outreach. The formatting for the email: 
    1. Include an email subject 
    2. 100 words max
    3. personalized as much as possible based on scrape data (identifying opportunities for improvement with the hotel)
    4. Uploaded as an entry in a cell to CSV file 
    5. Explain how this might be integrated automatically with a CRM system - COMMENT: Integration depends on existing dashnoard, if you have one. 
																					 Otherwise, crating dashboard in any stack than integrating scraping script with dashborad. Also scraping script can include API calls like this, or somwhere else in Dashobard app.
																					 Stack can be either Flask/Fast API (python based) or NodeJS/ReactJS (JS based backend and frontend), .NET etc. 
																					 Also, we might consider using some data warehouse when data grows. That is commong case for marketing comapnies, that either get campaign results in big files/streams or web scraping results.
																					 PosgreSQL is one option for temp data then using any tool like snowflake to digest that data in meaningful way.
																					 Note, I have used this API two or three times, but I was not paying for it, so it is not hard to implement this :)
	
**Deliverables:**
- A deployed App from Replit that scrapes as many hotel data contacts as possible within a 5 km radius of this hotel location https://maps.app.goo.gl/JdqecKy3kz45QSJ26
- CSV file with cleanly organized scraped results and personalized emails (in it’s own column) ready for potential upload to a CRM system
- Video explanation of the app, how it functions, results you were able to achieve, and how you think you could improve the app if you had 20 hours? (please keep the video to a max of 5 minutes)
    - Feel free to include a written explanation of anything as well if you feel necessary
	
	
	
	
*********************************************************************************************************************************************************************************************************************************************************************************
Here is the summary of tasks that are finished. Taks that are finished are marked as "DONE". I had an idea, to host this app/python script somwhere, BUT, script is using multitasking/multiprocessing, 
and it spawns number of threads depending on your CPU core count. This is used to increase speed of scraping for this task. 

ZERO:
function perform_scraping()

This functiopn is main scraping function. It is setting up Selenimu with ChromeDriver and using headless and disable gpu options, to setup scraping tool.  

FIRST:
function scrape_google_maps_urls(search_query, driver)

This function is fetching all urls for nearby hotels for fixed URL on Google Maps. It is using ChromeDriver with Selenium to scrape initial data and to scroll down until end is reached. Those URLs are put into an array that is later used to scrape inidivdual hotel data.
So, by searching ID for Google Maps searchbox, "searchboxinput", I am sending keys to searchbox depending on query that you want. In our example that is fixed, and search_query = None. Reason for that is that you have already sent URL for search, so I am not making this dynamically, but it cam be made that way.
Next part is scraping URLs for each result. This means that we need to use Selenium to scroll when end is reached and to check if new records exist (infinite scroll). This id done with this line:
driver.execute_script("arguments[0].scrollIntoView();", businesses[-1])

We are scrolling to last record and setting sleep time to wait for records to load. Then we append new records by class name and repeat process again, until there are no more records to be added.

SECOND:
function scrape_url_data(google_url, chrome_install, chrome_options)

This function is scraping individual hotel data and include scraping for fields that are in task marked as DONE. Scraping is done in 4 ways: by ID, by CLASS_NAME, by CSS_SELECTOR and by XPATH.

Here are details:
	"name": scraped text by class name "lfPIob"
	"phone": scraped text by css selector  "[data-item-id*='phone']"
	"url": scraped text by css selector  "[data-item-id*='authority']"
	"address":  scraped text by css selector  "[data-item-id*='address']"
	"numberOfReviews": scraped text by class name "rqjGif", then outer HTML is taken and with beautifulsoup parser, all SPAN tags are found that contains field numberOfReviews and are converted to comma separated string. Here we have only one record, that we needed.
	"averageReviewScore": scraped text by class name  "fontDisplayLarge"
	"checkInOutTimes":  scraped text by css selector  "data-item-id*='place-info-links:']"
	"amenities": scraped text by class name "rqjGif", then outer HTML is taken and with beautifulsoup parser, all SPAN tags are found that contains field numberOfReviews and are converted to comma separated string
	"numberOfOTAs": this was a little bit tricky as we needed to fetch all OTAs(Online Travel Agencies) not on first tab, where they are shown in reduced number, but on second tab called "Prices", where all OTAs are present. 
					This includes first finding appropriate tab button to click. It is found by next XPATH "//button[@class='hh2c6 ']". 
					Then we wait for 3 seconds to switch to that tab, and then start scraping. Scraping is done by scracping with beautifulsoup for class "QVR4f fontTitleSmall".
					All records are show as final count for OTAs as numberOfield.
	"otaLinks": this was a little bit tricky as we needed to fetch all OTAs(Online Travel Agencies) not on first tab, where they are shown in reduced number, but on second tab called "Prices", where all OTAs are present. 
				This includes first finding appropriate tab button to click. It is found by next XPATH "//button[@class='hh2c6 ']". 
				Then we wait for 3 seconds to switch to that tab, and then start scraping. Scraping is done by scracping with beautifulsoup for class "SlvSdc co54Ed".
				All links are show as comma delimited string.
	"socialMediaLinks": this was done by loading browser for all records that have URL or webpage and using reqular expression to find all A tags where href contains url for major social networks like facebook, twitter, linedkin, instagram, youtube.
					If pattern is found, we scrape that A tag and take its href into comma separated array as result of scraping.
	"workingHours": this was done with finding TABLE tag by class "eK4R0e fontBodyMedium". Then if table is found, search for UL tag with class "G8aQO". If found, and if it contains specific time range, with/without closed then it is not open 24h. 
					Other than that it is open 24h.

Here is the output JSON object for scraped data:
{
	"name": "The Island Resort at Fort Walton Beach",
	"phone": "+1 800-874-8962",
	"url": "theislandfl.com",
	"address": "1500 Miracle Strip Pkwy SE, Fort Walton Beach, FL 32548, Sjedinjene Drave",
	"numberOfReviews": 4.378,
	"averageReviewScore": "4,0",
	"checkInOutTimes": "Vrijeme prijave: 15:00\nVrijeme odjave: 11:00",
	"amenities": "Besplatan WiFi, Doruak uz plaanje, Parking uz plaanje, Pristupano za invalide, Otvoreni bazen, Klimatizirano, Praonica rublja, Poslovni centar, Pogodno za ljubimce, Pristup plai, Pogodno za djecu, Restoran, Prijevoz sa/do aerodroma, Vrela kupka, Fitnes centar, Bar, Nepuaki",
	"numberOfOTAs": "27",
	"otaLinks": "https://www.google.com/aclk?sa=l&ai=DChcSEwjN5MWauemLAxWVXEgAHX3-DRkYABABGgJjZQ&co=1&ase=2&gclid=EAIaIQobChMIzeTFmrnpiwMVlVxIAB19_g0ZEAoYASABEgLIKfD_BwE&sig=AOD64_1iTJyEcmpmxx0qfLQodUpQUYvT5Q&nis=4&adurlhttps://www.google.com/aclk?sa=l&ai=DChcSEwjN5MWauemLAxWVXEgAHX3-DRkYABADGgJjZQ&co=1&ase=2&gclid=EAIaIQobChMIzeTFmrnpiwMVlVxIAB19_g0ZEAoYAiABEgIAEvD_BwE&sig=AOD64_2QURhOFjx-o9paR9uJQuPDKNp3dA&nis=4&adurl, https://www.google.com/aclk?sa=l&ai=DChcSEwjN5MWauemLAxWVXEgAHX3-DRkYABAFGgJjZQ&co=1&ase=2&gclid=EAIaIQobChMIzeTFmrnpiwMVlVxIAB19_g0ZEAoYAyABEgL4O_D_BwE&sig=AOD64_3Wwl2KgmpxgwWHSodSEUQrrgbcSw&nis=4&adurl, https://www.google.com/aclk?sa=l&ai=DChcSEwjN5MWauemLAxWVXEgAHX3-DRkYABAHGgJjZQ&co=1&ase=2&gclid=EAIaIQobChMIzeTFmrnpiwMVlVxIAB19_g0ZEAoYBCABEgJ22_D_BwE&sig=AOD64_01Q66LXH4xgEU9JhIju19zekkWOA&nis=4&adurl, http://www.google.com/travel/clk?pc=AA80OszasVL8MCQAr-7hW9mo8-WLzJnJgpCrRnrBmhoHW5931xE96OaXh7d5QkIVMrrVL30jBJWPijUwunJUicKSF04LYd8qrRwOMpYKEMN_DhNnii8C1t1qFwP0FA3ATbTrCWRJqB5jN3kaB5w_5k6p30QvdQ3pm2uJDA&pcurl=https://m.hktuyitrip.com/hotel-detail?hotelId%3Dh1329704887109292032%26roomId%3Dr1329704887495168000%26planId%3Dr1329704887495168000_2%5C_2%5C_3%5C_2%5C_3%5C_w%5C_p%5C_m%5C_385242675%26checkIn%3D2025-03-01%26checkOut%3D2025-03-04%26adult%3D2%26children%3D0%26age%3D%26userDevice%3Ddesktop%26googleSite%3Dmapresults%26userCurrency%3DBAM%26userCountry%3DBA%26userLanguage%3Dbs%26userTotal%3D618.48, http://www.google.com/travel/clk?pc=AA80OsyiNf_FZdCiGx00X8qRk3Eh0l_4kbldvpQAb2w5WQg5VN4PxKVn4ztO-XWsbdZh2EF9LQeGO8o_ddILmIma9Z9otPQJpO0R5fHypsMikRdYh9RYf1geQiysBDg&pcurl=https://linkcenter.derbysoftca.com/dplatform-linkcenter/booking.htm?hotelCode%3DSABRE-37398%26providerHotelCode%3DSABRE-37398%26checkInDate%3D2025-03-01%26checkOutDate%3D2025-03-04%26identifier%3Dsabre-google%26currency%3DUSD%26userCurrency%3DBAM%26language%3Dbs%26userCountry%3DBA%26testClick%3Dfalse%26sitetype%3Dmapresults%26deviceType%3Ddesktop%26priceDisplayedTax%3D330.19%26priceDisplayedTotal%3D1268.20%26partnerId%3Dderbysoft%26campaignid%3D%26userlistid%3D%26ifDefaultDate%3Dselected%26isPromoted%3Dfalse%26s_is_ad%3Dfalse%26adults%3D2%26children%3D0%26hotel_campaign%3Dtrue%26clk_src%3D",
	"socialMediaLinks": "https://www.instagram.com/theislandfl/https://www.facebook.com/TheIslandFL/, https://www.linkedin.com/company/the-island-resort-at-fort-walton-beach, https://www.instagram.com/p/DGN-m2kJhdI, https://www.instagram.com/p/DGLZ7wbptca, https://www.instagram.com/p/DGGQNp9BZPv, https://www.instagram.com/p/DF-h2DzpOdY",
	"workingHours": "Open 24 hours"
}

Everything is saved to CSV file too. Also for me it is in Bosnian language :)
I have set urls[:5] to scrape first 5 URLs, as scraping all 120+ records for this example might take some time, especially if script is not using multitasking/multiprocessing. ALso important note for computer resources, as multitasking/multiprocessingć is taking a lot of RAM and
CPU depending on number of records.

THIRD:

One important note, This solution is not definite solution, as Google changes data class names and ids frquently, so any solution needs to be changed accordingly. Also this solution may vary for type of data scraping. 
Those are only hotels and differnt/missing/addidional data may appear/disappear on different types of scracping. Also important note is that css selector changes according to language that is used for google maps.



