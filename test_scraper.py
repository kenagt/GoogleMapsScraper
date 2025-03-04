import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import multiprocessing

# Lock for thread-safe writing
lock = threading.Lock()
results = []  # Shared list to store results

# Function to initialize a Selenium driver
def get_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Random User-Agent
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f"user-agent={user_agent}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Function to scrape details from a Google Maps URL
def scrape_google_maps(url):
    driver = get_driver()
    
    try:
        # Open the provided Google Maps URL
        driver.get(url)
        time.sleep(random.uniform(3, 6))  # Random delay to mimic human interaction
        
        # Extract business name
        try:
            name = driver.find_element(By.CLASS_NAME, "DUwDvf").text
        except:
            name = "N/A"

        # Extract address
        try:
            address = driver.find_element(By.CSS_SELECTOR, "[data-item-id*='address']").text
        except:
            address = "N/A"

        # Extract rating
        try:
            rating = driver.find_element(By.CLASS_NAME, "fontDisplayLarge").text
        except:
            rating = "N/A"

        # Extract number of reviews
        try:
            num_reviews = driver.find_element(By.CSS_SELECTOR, "[data-item-id*='phone']").text
        except:
            num_reviews = "N/A"

        # Extract phone number
        try:
            phone = driver.find_element(By.XPATH, "//button[contains(@data-tooltip, 'Phone')]/div").text
        except:
            phone = "N/A"

        # Extract amenities (e.g., Free Wi-Fi, Parking, etc.)
        try:
            amenities_elements = driver.find_elements(By.CLASS_NAME, "CsEnBe")
            amenities = ", ".join([amenity.text for amenity in amenities_elements if amenity.text.strip()])  # Convert to CSV string
        except:
            amenities = "N/A"

        # Extract working hours
        try:
            working_hours = driver.find_element(By.CLASS_NAME, "Jj1fXb").text.replace("\n", ", ")
        except:
            working_hours = "N/A"

        # Extract check-in and check-out times (if applicable)
        try:
            check_in_out_times = driver.find_elements(By.CLASS_NAME, "WgFkxc")
            if len(check_in_out_times) >= 2:
                check_in = check_in_out_times[0].text
                check_out = check_in_out_times[1].text
            else:
                check_in = "N/A"
                check_out = "N/A"
        except:
            check_in = "N/A"
            check_out = "N/A"

        result = {
            "name": name,
            "address": address,
            "rating": rating,
            "num_reviews": num_reviews,
            "phone": phone,
            "amenities": amenities,
            "working_hours": working_hours,
            "check_in": check_in,
            "check_out": check_out,
            "url": url
        }
        
        # Store result in a thread-safe way
        with lock:
            results.append(result)
        
        print(f"Scraped: {name} | {address} | Rating: {rating} | Reviews: {num_reviews} | Phone: {phone} | Amenities: {amenities} | Working Hours: {working_hours} | Check-in: {check_in} | Check-out: {check_out}")
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")

    finally:
        driver.quit()

# Thread worker function
def thread_worker(url_list):
    for url in url_list:
        scrape_google_maps(url)

# Function to save results to JSON
def save_to_json(filename="results.json"):
    with lock:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # Sample Google Maps URLs (Replace with actual URLs)
    search_urls = [
        "https://www.google.com/maps/place/SunDestin+Beach+Resort+by+Scenic+Stays/data=!4m10!3m9!1s0x88914479cbe95349:0xbdd42ac5d06c66f7!5m2!4m1!1i2!8m2!3d30.3846369!4d-86.468563!16s%2Fg%2F11g_hsjhm!19sChIJSVPpy3lEkYgR92Zs0MUq1L0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hampton+Inn+%26+Suites+Destin/data=!4m10!3m9!1s0x8891447e3573d10d:0xf145097abc1d3f2d!5m2!4m1!1i2!8m2!3d30.3850484!4d-86.4601919!16s%2Fg%2F1td4384b!19sChIJDdFzNX5EkYgRLT8dvHoJRfE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Surfside+Resort/data=!4m10!3m9!1s0x88915b673949d583:0x844fd6b6a78737be!5m2!4m1!1i2!8m2!3d30.3759776!4d-86.3663154!16s%2Fg%2F11xj0fsrb!19sChIJg9VJOWdbkYgRvjeHp7bWT4Q?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Wyndham+Garden+Fort+Walton+Beach+-+Destin+Hotel,+FL/data=!4m10!3m9!1s0x88913f2c1b0ab94b:0x7de393b48e40aba2!5m2!4m1!1i2!8m2!3d30.3966667!4d-86.6148726!16s%2Fg%2F1pp2wxrwf!19sChIJS7kKGyw_kYgRoqtAjrST430?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Seaside+Escape+at+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f6bed768b4f:0x90a8b966af4ef0d5!5m2!4m1!1i2!8m2!3d30.4130383!4d-86.6071846!16s%2Fg%2F11nxc6vp55!19sChIJT4t27Ws_kYgR1fBOr2a5qJA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Majestic+Sun+in+Miramar+Beach+by+Vacasa/data=!4m10!3m9!1s0x88915b8fb1265f91:0x1530ce814c6ff1e6!5m2!4m1!1i2!8m2!3d30.3755213!4d-86.3688883!16s%2Fg%2F1th644df!19sChIJkV8msY9bkYgR5vFvTIHOMBU?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Island+Resort+at+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f5244a9e305:0xc87a9b0267647c!5m2!4m1!1i2!8m2!3d30.3946464!4d-86.5889607!16s%2Fg%2F1tjcq6pr!19sChIJBeOpRFI_kYgRfGRnApt6yAA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Henderson+Park+Inn/data=!4m10!3m9!1s0x8891449c3ce5bb4d:0x1f74c318bcaaaf45!5m2!4m1!1i2!8m2!3d30.382766!4d-86.432238!16s%2Fg%2F1td_5zcb!19sChIJTbvlPJxEkYgRRa-qvBjDdB8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hilton+Garden+Inn+Destin+Miramar+Beach/data=!4m10!3m9!1s0x88915b04465799b1:0x8111ce29cd1a2bdf!5m2!4m1!1i2!8m2!3d30.3760275!4d-86.3525514!16s%2Fg%2F11ftg032n5!19sChIJsZlXRgRbkYgR3ysazSnOEYE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Henderson+Beach+Resort/data=!4m10!3m9!1s0x889144a72a58fcbd:0xa4f2f27137436d45!5m2!4m1!1i2!8m2!3d30.3844642!4d-86.4314956!16s%2Fg%2F11f2gshdxp!19sChIJvfxYKqdEkYgRRW1DN3Hy8qQ?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Mainsail+Resort/data=!4m10!3m9!1s0x88915be555f4ce89:0x59efe8f28b1d1c77!5m2!4m1!1i2!8m2!3d30.373449!4d-86.347711!16s%2Fg%2F11xs0c581!19sChIJic70VeVbkYgRdxwdi_Lo71k?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Pelican+Beach/data=!4m10!3m9!1s0x889143eda0e8ab53:0x6161a0221160cefd!5m2!4m1!1i2!8m2!3d30.3846743!4d-86.4745116!16s%2Fg%2F11g9jn0scf!19sChIJU6vooO1DkYgR_c5gESKgYWE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hilton+Garden+Inn+Ft.+Walton+Beach/data=!4m10!3m9!1s0x88913f4bf98e245d:0xd25e7e05a27105d4!5m2!4m1!1i2!8m2!3d30.3948843!4d-86.5977144!16s%2Fg%2F11cs4j3wq_!19sChIJXSSO-Us_kYgR1AVxogV-XtI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Ariel+Dunes+I+%28ADI%29+at+Seascape+Resort/data=!4m10!3m9!1s0x88915b84227b9017:0x42c13efd66c06841!5m2!4m1!1i2!8m2!3d30.377608!4d-86.366795!16s%2Fg%2F1tfb2s62!19sChIJF5B7IoRbkYgRQWjAZv0-wUI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Island+Echos+by+Vacasa/data=!4m10!3m9!1s0x88913f2a08150425:0x13b7d992ca17b8c9!5m2!4m1!1i2!8m2!3d30.3969758!4d-86.6206687!16s%2Fg%2F1tj_5_x3!19sChIJJQQVCCo_kYgRybgXypLZtxM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Holiday+Inn+Resort+Fort+Walton+Beach,+an+IHG+Hotel/data=!4m10!3m9!1s0x88913f4c086dbde5:0x39802cc9296d26d0!5m2!4m1!1i2!8m2!3d30.3948149!4d-86.5968212!16s%2Fg%2F1yfj43p9b!19sChIJ5b1tCEw_kYgR0CZtKcksgDk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Emerald+Grande+at+HarborWalk+Village/data=!4m10!3m9!1s0x8891414c2b72dc09:0xf31452fa34506fbe!5m2!4m1!1i2!8m2!3d30.3950538!4d-86.5119221!16s%2Fg%2F1vr3dys3!19sChIJCdxyK0xBkYgRvm9QNPpSFPM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Days+Inn+by+Wyndham+Destin/data=!4m10!3m9!1s0x88914477fbfd843d:0xb9da4cb7c6b3e7fa!5m2!4m1!1i2!8m2!3d30.387847!4d-86.4696791!16s%2Fg%2F1tj7x4gm!19sChIJPYT9-3dEkYgR-uezxrdM2rk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sandestin+Golf+and+Beach+Resort/data=!4m10!3m9!1s0x8891449dfc6f186d:0x7d3067df55fb0c74!5m2!4m1!1i2!8m2!3d30.3800044!4d-86.3301232!16s%2Fg%2F1tcvcp4m!19sChIJbRhv_J1EkYgRdAz7Vd9nMH0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Days+Inn+by+Wyndham+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913ed99577cb43:0xe808b7e586935a7!5m2!4m1!1i2!8m2!3d30.4057691!4d-86.6237053!16s%2Fg%2F1tfh5fdq!19sChIJQ8t3ldk-kYgRpzVpWH6LgA4?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Palms+of+Destin+Resort/data=!4m10!3m9!1s0x8891437e47c4093f:0x76c08500ab2c99d9!5m2!4m1!1i2!8m2!3d30.3897222!4d-86.4561111!16s%2Fg%2F1tf9p0sn!19sChIJPwnER35DkYgR2ZksqwCFwHY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Destin+Inn+%26+Suites/data=!4m10!3m9!1s0x889143f7760a9dbd:0xfc54140efd026d79!5m2!4m1!1i2!8m2!3d30.3919493!4d-86.4884793!16s%2Fg%2F1tf611l4!19sChIJvZ0KdvdDkYgReW0C_Q4UVPw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/SummerPlace+Inn+Destin+FL+Hotel/data=!4m10!3m9!1s0x88914478dc12ac2f:0xfce0eb05f86f30d0!5m2!4m1!1i2!8m2!3d30.3863454!4d-86.4602775!16s%2Fg%2F1hc72tjb8!19sChIJL6wS3HhEkYgR0DBv-AXr4Pw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Village+Inn+of+Destin/data=!4m10!3m9!1s0x88914153da24751b:0xef19f4afa6527b1d!5m2!4m1!1i2!8m2!3d30.394919!4d-86.5064586!16s%2Fg%2F1thnpk4m!19sChIJG3Uk2lNBkYgRHXtSpq_0Ge8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sterling+Shores+Beach+Resort+-+Destin+Vacation+Rentals+by+Vacasa/data=!4m10!3m9!1s0x8891448062d96f65:0xf6f4069e1ed30a94!5m2!4m1!1i2!8m2!3d30.3852275!4d-86.4585188!16s%2Fg%2F11cm_hcvk8!19sChIJZW_ZYoBEkYgRlArTHp4G9PY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Quality+Inn+Fort+Walton+Beach+-+Destin+West/data=!4m10!3m9!1s0x88913ec5bc63e7ad:0x3d3bf83e7407a1b7!5m2!4m1!1i2!8m2!3d30.4056489!4d-86.6342168!16s%2Fg%2F11f547hdck!19sChIJredjvMU-kYgRt6EHdD74Oz0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Four+Points+by+Sheraton+Destin-Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f4c11bae7a9:0xd944cc6a00b9d956!5m2!4m1!1i2!8m2!3d30.3952829!4d-86.5954559!16s%2Fg%2F1w8wbt56!19sChIJqee6EUw_kYgRVtm5AGrMRNk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Beal+House+Fort+Walton+Beachfront,+Tapestry+Collection+by+Hilton/data=!4m10!3m9!1s0x88913f346c8a0d73:0x632fe1cef9d19296!5m2!4m1!1i2!8m2!3d30.3957337!4d-86.6048178!16s%2Fg%2F1tk68g66!19sChIJcw2KbDQ_kYgRlpLR-c7hL2M?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Embassy+Suites+by+Hilton+Destin+Miramar+Beach/data=!4m10!3m9!1s0x88915b8d36b948b7:0xea82141ae6f6415b!5m2!4m1!1i2!8m2!3d30.3757446!4d-86.3580121!16s%2Fg%2F1v_vtp68!19sChIJt0i5No1bkYgRW0H25hoUguo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Destin+West+Gulfside+by+Beach+Time+Vacations/data=!4m10!3m9!1s0x88913f1a26034dcb:0xa46eea070a7cb089!5m2!4m1!1i2!8m2!3d30.3939748!4d-86.5874871!16s%2Fg%2F11j1_hwsvc!19sChIJy00DJho_kYgRibB8CgfqbqQ?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sleep+Inn+%26+Suites+Niceville+-+Destin/data=!4m10!3m9!1s0x889167fee58e4d65:0x30dcc255f92a311!5m2!4m1!1i2!8m2!3d30.4821374!4d-86.415308!16s%2Fg%2F11pf8f2cv9!19sChIJZU2O5f5nkYgREaOSXyXMDQM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Spark+by+Hilton+Destin/data=!4m10!3m9!1s0x8891435855d3533f:0xac3323793a32109!5m2!4m1!1i2!8m2!3d30.389753!4d-86.431226!16s%2Fg%2F11bxdx2nq1!19sChIJP1PTVVhDkYgRCSGjkzcywwo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Extended+Stay+America+Select+Suites+-+Pensacola+-+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f9ee5085f3d:0x2f020f641ae47e53!5m2!4m1!1i2!8m2!3d30.4420509!4d-86.5974273!16s%2Fg%2F1tff_8hx!19sChIJPV8I5Z4_kYgRU37kGmQPAi8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hole+Inn+the+Wall+Hotel-Fort+Walton+Beach-Sunset+Plaza-nearby+Beaches+%26+Hurlburt/data=!4m10!3m9!1s0x88913eda3b0a21fd:0xcdaf67191f008276!5m2!4m1!1i2!8m2!3d30.4058343!4d-86.6265277!16s%2Fg%2F1pp2t_gf0!19sChIJ_SEKO9o-kYgRdoIAHxlnr80?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sandpiper+Cove+Beach/data=!4m10!3m9!1s0x8891434f45b1d767:0xbd5d1509e46cdd24!5m2!4m1!1i2!8m2!3d30.3891303!4d-86.4834744!16s%2Fg%2F11g0grtmkv!19sChIJZ9exRU9DkYgRJN1s5AkVXb0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Motel+6+Destin,+FL/data=!4m10!3m9!1s0x88914155c7ea92b9:0xc3403c8b225e5957!5m2!4m1!1i2!8m2!3d30.3937259!4d-86.5011154!16s%2Fg%2F1tfn3j3g!19sChIJuZLqx1VBkYgRV1leIos8QMM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Beachside+Inn/data=!4m10!3m9!1s0x889144a8e24ea3db:0x8201e2be740f606a!5m2!4m1!1i2!8m2!3d30.3831767!4d-86.4265761!16s%2Fg%2F1tjt2qcp!19sChIJ26NO4qhEkYgRamAPdL7iAYI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Henderson+Beach+Vacation+Rentals/data=!4m10!3m9!1s0x8891458c15a0e271:0x2efcfc4f283e6fbd!5m2!4m1!1i2!8m2!3d30.3853155!4d-86.4308095!16s%2Fg%2F11kbz1lx5l!19sChIJceKgFYxFkYgRvW8-KE_8_C4?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Beach+Resort+By+Ocean+Reef+Resorts/data=!4m10!3m9!1s0x88915b7bc56fa9a7:0xaf2bc9f49c0397ec!5m2!4m1!1i2!8m2!3d30.3794209!4d-86.3956685!16s%2Fg%2F12hy9f7rk!19sChIJp6lvxXtbkYgR7JcDnPTJK68?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Spark+by+Hilton+Destin/data=!4m10!3m9!1s0x889143868ec7cf35:0x40a28916b48142f9!5m2!4m1!1i2!8m2!3d30.3897513!4d-86.4312145!16s%2Fg%2F11wmwvrbys!19sChIJNc_HjoZDkYgR-UKBtBaJokA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hilton+Grand+Vacations+Club+in+Sandestin+Golf+and+Beach+Resort/data=!4m10!3m9!1s0x88915eb2c1df9921:0x320aa68b935a5983!5m2!4m1!1i2!8m2!3d30.384909!4d-86.3245892!16s%2Fg%2F1yglpdj1s!19sChIJIZnfwbJekYgRg1lak4umCjI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Waterscape+Resort/data=!4m10!3m9!1s0x88913f8b4b7fdec7:0x57092c9d332352bd!5m2!4m1!1i2!8m2!3d30.3965151!4d-86.598576!16s%2Fg%2F11gr21j9fw!19sChIJx95_S4s_kYgRvVIjM50sCVc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Home2+Suites+by+Hilton+Destin/data=!4m10!3m9!1s0x88914480361fc485:0xe480df6551fb23dd!5m2!4m1!1i2!8m2!3d30.3865852!4d-86.4569092!16s%2Fg%2F11cs6ltmhw!19sChIJhcQfNoBEkYgR3SP7UWXfgOQ?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hampton+Inn+Ft.+Walton+Beach/data=!4m10!3m9!1s0x88913f4a0be8f9b3:0x4f1873ac2dd3fada!5m2!4m1!1i2!8m2!3d30.39551!4d-86.600316!16s%2Fg%2F1vlqq_1v!19sChIJs_noC0o_kYgR2vrTLaxzGE8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Leeward+Key+Condos/data=!4m10!3m9!1s0x88915b4cc3877c31:0x10b3a92f6a94bdac!5m2!4m1!1i2!8m2!3d30.3797603!4d-86.3964207!16s%2Fg%2F11tggn6zc9!19sChIJMXyHw0xbkYgRrL2Uai-psxA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sea+Oats+Condominiums+by+Southern+Vacation+Rentals/data=!4m10!3m9!1s0x88913f3589c6ae7f:0x703189ea305e04a!5m2!4m1!1i2!8m2!3d30.3955363!4d-86.600655!16s%2Fg%2F1td_zcm_!19sChIJf67GiTU_kYgRSuAFo54YAwc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Pelican+Isle+Condos+in+Fort+Walton+Beach+by+Vacasa/data=!4m10!3m9!1s0x88913ed3cd59dc95:0x66853d0f6b510446!5m2!4m1!1i2!8m2!3d30.3973968!4d-86.6280635!16s%2Fg%2F11gg9lqr_7!19sChIJldxZzdM-kYgRRgRRaw89hWY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Islander+by+Vacasa/data=!4m10!3m9!1s0x88913ed406800c27:0x12e37b3f602f0d90!5m2!4m1!1i2!8m2!3d30.3972663!4d-86.6252441!16s%2Fg%2F1tdd60wp!19sChIJJwyABtQ-kYgRkA0vYD974xI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Market+Street+Inn/data=!4m10!3m9!1s0x88915fe48d31c0af:0x30e042347a99187b!5m2!4m1!1i2!8m2!3d30.3907493!4d-86.3250135!16s%2Fg%2F11j2q0rx46!19sChIJr8AxjeRfkYgRexiZejRC4DA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Fairfield+Inn+%26+Suites+Fort+Walton+Beach-West+Destin/data=!4m10!3m9!1s0x88913f2bf8d32567:0x7c237dac0a238e6e!5m2!4m1!1i2!8m2!3d30.3969351!4d-86.6125555!16s%2Fg%2F1pzs24j4r!19sChIJZyXT-Cs_kYgRbo4jCqx9I3w?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Inn+on+Destin+Harbor,+Ascend+Hotel+Collection/data=!4m10!3m9!1s0x88914145c118c253:0xca1e4c3860a76617!5m2!4m1!1i2!8m2!3d30.3926314!4d-86.5016123!16s%2Fg%2F11t5nt7cbs!19sChIJU8IYwUVBkYgRF2anYDhMHso?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Fairfield+Inn+by+Marriott+Fort+Walton+Beach+Hurlburt+Area/data=!4m10!3m9!1s0x88913e909569b197:0x885837d36353552f!5m2!4m1!1i2!8m2!3d30.4228905!4d-86.649735!16s%2Fg%2F1pp2tyj8j!19sChIJl7FplZA-kYgRL1VTY9M3WIg?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Home2+Suites+by+Hilton+Fort+Walton+Beach+Eglin+Air+Force+Base/data=!4m10!3m9!1s0x88913e346267eab7:0x310734f9e929c6e8!5m2!4m1!1i2!8m2!3d30.4644393!4d-86.6219277!16s%2Fg%2F11vyvx60fl!19sChIJt-pnYjQ-kYgR6MYp6fk0BzE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Comfort+Inn+%26+Suites+Destin+near+Henderson+Beach/data=!4m10!3m9!1s0x889143ea76426ba5:0xbbe316767bb53274!5m2!4m1!1i2!8m2!3d30.389312!4d-86.43292!16s%2Fg%2F11tpb1xp3x!19sChIJpWtCdupDkYgRdDK1e3YW47s?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hotel+Effie+Sandestin,+Autograph+Collection/data=!4m10!3m9!1s0x8891595178e68b1b:0x5c4824aea1cd6d25!5m2!4m1!1i2!8m2!3d30.3914722!4d-86.325325!16s%2Fg%2F11j5h4xj2s!19sChIJG4vmeFFZkYgRJW3Noa4kSFw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Super+8+by+Wyndham+Ft+Walton+Beach/data=!4m10!3m9!1s0x88913ec42e741379:0x2394829286b1b6af!5m2!4m1!1i2!8m2!3d30.4073092!4d-86.6352466!16s%2Fg%2F1tppsrbc!19sChIJeRN0LsQ-kYgRr7axhpKClCM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Holiday+Inn+Express+%26+Suites+Fort+Walton+Beach+-+Eglin+Area,+an+IHG+Hotel/data=!4m10!3m9!1s0x8891158ffffffffb:0x744b3051d2186b7e!5m2!4m1!1i2!8m2!3d30.4651945!4d-86.6226866!16s%2Fg%2F11vzgjjq19!19sChIJ-____48VkYgRfmsY0lEwS3Q?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/La+Quinta+Inn+%26+Suites+by+Wyndham+Miramar+Beach-Destin/data=!4m10!3m9!1s0x889159dc21b1cb73:0xe19788c5abe18dc7!5m2!4m1!1i2!8m2!3d30.3843002!4d-86.3858566!16s%2Fg%2F11fn04wk59!19sChIJc8uxIdxZkYgRx43hq8WIl-E?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sleep+Inn+%26+Suites+Fort+Walton+Beach+-+Destin+West/data=!4m10!3m9!1s0x88913f41b21f7e65:0x5e27b44dc9332592!5m2!4m1!1i2!8m2!3d30.4045535!4d-86.6148661!16s%2Fg%2F11vyym4c8f!19sChIJZX4fskE_kYgRkiUzyU20J14?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Holiday+Inn+Express+%26+Suites+Destin+E+-+Commons+Mall+Area,+an+IHG+Hotel/data=!4m10!3m9!1s0x889144a82c926d79:0x19197e86774879c7!5m2!4m1!1i2!8m2!3d30.3869729!4d-86.4265725!16s%2Fg%2F1tctsfwx!19sChIJeW2SLKhEkYgRx3lId4Z-GRk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Waterscape+Condos+-+Fort+Walton+Beach+Vacation+Rentals+by+Vacasa/data=!4m10!3m9!1s0x88913f4a3de34a39:0x2ad3135e485e9524!5m2!4m1!1i2!8m2!3d30.3953714!4d-86.5983281!16s%2Fg%2F1yj4k38xs!19sChIJOUrjPUo_kYgRJJVeSF4T0yo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Fairfield+Inn+%26+Suites+Destin/data=!4m10!3m9!1s0x889143627f50bbc7:0xb639834d97fcf398!5m2!4m1!1i2!8m2!3d30.3874657!4d-86.4461334!16s%2Fg%2F11bbrp2gbl!19sChIJx7tQf2JDkYgRmPP8l02DObY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Hampton+Inn+%26+Suites+Mary+Esther-Fort+Walton+Beach/data=!4m10!3m9!1s0x88913ea1a2161f33:0x30eb851ac6a99ef0!5m2!4m1!1i2!8m2!3d30.4142646!4d-86.6573791!16s%2Fg%2F11c1wvxnn9!19sChIJMx8WoqE-kYgR8J6pxhqF6zA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Fairfield+Inn+%26+Suites+Fort+Walton+Beach-Eglin+AFB/data=!4m10!3m9!1s0x889140783aeb0f25:0x1ca0da2578f689c1!5m2!4m1!1i2!8m2!3d30.4478645!4d-86.579216!16s%2Fg%2F1tkc2wt7!19sChIJJQ_rOnhAkYgRwYn2eCXaoBw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Extended+Stay+America+Select+Suites+-+Destin+-+US+98+-+Emerald+Coast+Pkwy./data=!4m10!3m9!1s0x88915b6005e36521:0x6107cb478d09d012!5m2!4m1!1i2!8m2!3d30.387269!4d-86.400409!16s%2Fg%2F1tywyqhs!19sChIJIWXjBWBbkYgREtAJjUfLB2E?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Evoke+Destin+Hotel/data=!4m10!3m9!1s0x88915b592ac3e2cd:0xe9067a7d542f318a!5m2!4m1!1i2!8m2!3d30.379254!4d-86.3560911!16s%2Fg%2F11v3m_4f8j!19sChIJzeLDKllbkYgRijEvVH16Buk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Regency+Inn/data=!4m10!3m9!1s0x88913ec6f47b6e55:0x6ab69ea2fbc5cb8f!5m2!4m1!1i2!8m2!3d30.4079972!4d-86.6371398!16s%2Fg%2F1thw7hsb!19sChIJVW579MY-kYgRj8vF-6Ketmo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Tru+by+Hilton+Destin/data=!4m10!3m9!1s0x889143327408180f:0x23ecee737f9d0d9!5m2!4m1!1i2!8m2!3d30.3893706!4d-86.4469623!16s%2Fg%2F11ty4lky2t!19sChIJDxgIdDJDkYgR2dD5N-fOPgI?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Baymont+by+Wyndham+Fort+Walton+Beach+Mary+Esther/data=!4m10!3m9!1s0x88913ea463331947:0x48f66a7b50f487f7!5m2!4m1!1i2!8m2!3d30.4097669!4d-86.6537419!16s%2Fg%2F1ptzj3l7y!19sChIJRxkzY6Q-kYgR94f0UHtq9kg?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Club+Destin/data=!4m10!3m9!1s0x88914478f96bf893:0x1b0bc6ba26434240!5m2!4m1!1i2!8m2!3d30.3869354!4d-86.4656104!16s%2Fg%2F1pv5xy__6!19sChIJk_hr-XhEkYgRQEJDJrrGCxs?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Wingate+by+Wyndham+Destin/data=!4m10!3m9!1s0x8891438a1556b9cd:0xcdfb650b099bba0c!5m2!4m1!1i2!8m2!3d30.389878!4d-86.4749725!16s%2Fg%2F1tdmqv5t!19sChIJzblWFYpDkYgRDLqbCQtl-80?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Grand+Sandestin/data=!4m10!3m9!1s0x88915eb1c9c31e87:0x96821f7b8f70cb19!5m2!4m1!1i2!8m2!3d30.392485!4d-86.326313!16s%2Fg%2F11cnc11btt!19sChIJhx7DybFekYgRGctwj3sfgpY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Comfort+Inn+Miramar+Beach-Destin/data=!4m10!3m9!1s0x88915de8de7e7b7f:0x8a0dbf5a9787c910!5m2!4m1!1i2!8m2!3d30.385844!4d-86.376896!16s%2Fg%2F11q2w0zdmn!19sChIJf3t-3uhdkYgREMmHl1q_DYo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Homewood+Suites+by+Hilton+Destin/data=!4m10!3m9!1s0x8891447fe1a87ce5:0x8ea4934e592445b!5m2!4m1!1i2!8m2!3d30.3867848!4d-86.4593845!16s%2Fg%2F11pv9h8cmb!19sChIJ5Xyo4X9EkYgRW0SS5TRJ6gg?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Tru+by+Hilton+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913eda23a317ab:0x2dee43c4e1d92ee3!5m2!4m1!1i2!8m2!3d30.4057854!4d-86.6262263!16s%2Fg%2F11j5v13n40!19sChIJqxejI9o-kYgR4y7Z4cRD7i0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Fairway+Inn/data=!4m10!3m9!1s0x88913ed98bdf4983:0x51965ab772d46ede!5m2!4m1!1i2!8m2!3d30.4064083!4d-86.6256179!16s%2Fg%2F11r94dbw9!19sChIJg0nfi9k-kYgR3m7UcrdallE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Marina+Bay+Resort/data=!4m10!3m9!1s0x88913f300611e047:0x744bff13d9f9ce35!5m2!4m1!1i2!8m2!3d30.4027778!4d-86.6097222!16s%2Fg%2F11cmf3p1g2!19sChIJR-ARBjA_kYgRNc752RP_S3Q?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/La+Quinta+Inn+%26+Suites+by+Wyndham+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f258fc15eb3:0x37f6d1cdfabbab58!5m2!4m1!1i2!8m2!3d30.4046033!4d-86.6139802!16s%2Fg%2F1ts3014d!19sChIJs17BjyU_kYgRWKu7-s3R9jc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Comfort+Inn+%26+Suites/data=!4m10!3m9!1s0x88913ed9b797cabd:0x1837a71c92b61c41!5m2!4m1!1i2!8m2!3d30.405738!4d-86.624236!16s%2Fg%2F1th24l6p!19sChIJvcqXt9k-kYgRQRy2khynNxg?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Courtyard+Fort+Walton+Beach-West+Destin/data=!4m10!3m9!1s0x88913f340e85d5e5:0x8f3cd8c1234b7abc!5m2!4m1!1i2!8m2!3d30.3967608!4d-86.6080511!16s%2Fg%2F1q6634qtp!19sChIJ5dWFDjQ_kYgRvHpLI8HYPI8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Candlewood+Suites+Destin-Sandestin+Area,+an+IHG+Hotel/data=!4m10!3m9!1s0x88915b89e528cf7b:0x6d5e9205fd09bf1e!5m2!4m1!1i2!8m2!3d30.3851483!4d-86.3633028!16s%2Fg%2F1v26mwy0!19sChIJe88o5YlbkYgRHr8J_QWSXm0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Residence+Inn+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f2580d7ed85:0x3708228e34731249!5m2!4m1!1i2!8m2!3d30.403601!4d-86.613465!16s%2Fg%2F11qjttq_js!19sChIJhe3XgCU_kYgRSRJzNI4iCDc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Holiday+Inn+Express+Fort+Walton+Beach+Central,+an+IHG+Hotel/data=!4m10!3m9!1s0x88913ed8459b2d33:0x2382a47666a4a1!5m2!4m1!1i2!8m2!3d30.4057397!4d-86.6226453!16s%2Fg%2F11fxw9s1v2!19sChIJMy2bRdg-kYgRoaRmdqSCIwA?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/TownePlace+Suites+Fort+Walton+Beach-Eglin+AFB/data=!4m10!3m9!1s0x88913f9c3e7b2fb5:0xd502635c6a8958b3!5m2!4m1!1i2!8m2!3d30.4400858!4d-86.5940006!16s%2Fg%2F1q6kk0yyz!19sChIJtS97Ppw_kYgRs1iJalxjAtU?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Candlewood+Suites/data=!4m10!3m9!1s0x88913ec70e1ea473:0x33616ec24c5d458f!5m2!4m1!1i2!8m2!3d30.408533!4d-86.6402435!16s%2Fg%2F11hd7dhgv0!19sChIJc6QeDsc-kYgRj0VdTMJuYTM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Motel+8/data=!4m10!3m9!1s0x889143febe400da9:0xcdebb0879c4f46e0!5m2!4m1!1i2!8m2!3d30.3935337!4d-86.4957833!16s%2Fg%2F11g9wdctmq!19sChIJqQ1Avv5DkYgR4EZPnIew680?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Go+Waterscape/data=!4m10!3m9!1s0x88913f3855d7c0bf:0x5e44f54eed6ce2dd!5m2!4m1!1i2!8m2!3d30.3959234!4d-86.5988982!16s%2Fg%2F11tg7f1rnt!19sChIJv8DXVTg_kYgR3eJs7U71RF4?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Luau+Resort+2/data=!4m10!3m9!1s0x889159001d7c21f5:0x3c4b87be257b5ed!5m2!4m1!1i2!8m2!3d30.3717286!4d-86.3279558!16s%2Fg%2F11wwfk02mp!19sChIJ9SF8HQBZkYgR7bVX4nu4xAM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Economy+Motel/data=!4m10!3m9!1s0x88913f25777d6bbd:0x513a88303054d1e8!5m2!4m1!1i2!8m2!3d30.4046496!4d-86.6128773!16s%2Fg%2F1tkl42jq!19sChIJvWt9dyU_kYgR6NFUMDCIOlE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Silver+Beach+Towers+West/data=!4m10!3m9!1s0x8891447907b6baf7:0x7a8d1617a9e8f0aa!5m2!4m1!1i2!8m2!3d30.3847351!4d-86.4666041!16s%2Fg%2F11crzj5x21!19sChIJ97q2B3lEkYgRqvDoqRcWjXo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Inn+at+Crystal+Beach+by+Salt+Water+Vacations/data=!4m10!3m9!1s0x889144abf2202585:0x87233aeb0daf80b6!5m2!4m1!1i2!8m2!3d30.3820495!4d-86.4229494!16s%2Fg%2F1tfcp372!19sChIJhSUg8qtEkYgRtoCvDes6I4c?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Oceania+by+Holiday+Isle+Properties/data=!4m10!3m9!1s0x8891440926a80125:0x4f3dd5ca344d0d40!5m2!4m1!1i2!8m2!3d30.3842473!4d-86.4868646!16s%2Fg%2F1tjyph96!19sChIJJQGoJglEkYgRQA1NNMrVPU8?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Edgewater+Resort/data=!4m10!3m9!1s0x88915b4fb8af327d:0xa4d2e841dd768627!5m2!4m1!1i2!8m2!3d30.3746514!4d-86.3530036!16s%2Fg%2F11fjsb4ywy!19sChIJfTKvuE9bkYgRJ4Z23UHo0qQ?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Huntington+By+The+Sea+-+Miramar+Beach+Vacation+Rentals+by+Vacasa/data=!4m10!3m9!1s0x88915bf27f112007:0x27ceff40a1eac520!5m2!4m1!1i2!8m2!3d30.373917!4d-86.355198!16s%2Fg%2F1vgqdw59!19sChIJByARf_JbkYgRIMXqoUD_zic?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Beaux+Soleil/data=!4m10!3m9!1s0x88915bf2651a22db:0x43cd2e1022b22dfa!5m2!4m1!1i2!8m2!3d30.3795293!4d-86.3988017!16s%2Fg%2F11l3g3_4bs!19sChIJ2yIaZfJbkYgR-i2yIhAuzUM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Villa+Bianca/data=!4m10!3m9!1s0x88915bf9b17a6b8d:0x976212d4716f14d4!5m2!4m1!1i2!8m2!3d30.3797844!4d-86.4015963!16s%2Fg%2F11fnxvkhcf!19sChIJjWt6sflbkYgR1BRvcdQSYpc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Pelican+Beach+Resort+Condos/data=!4m10!3m9!1s0x8891447427105367:0xeb5657939b8a4468!5m2!4m1!1i2!8m2!3d30.3844906!4d-86.4747922!16s%2Fg%2F11f15m1r49!19sChIJZ1MQJ3REkYgRaESKm5NXVus?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Breakers+of+Fort+Walton+Beach/data=!4m10!3m9!1s0x88913f338d7a3c75:0x77fb7639da9bb2da!5m2!4m1!1i2!8m2!3d30.3959363!4d-86.6057022!16s%2Fg%2F1tf4ftkc!19sChIJdTx6jTM_kYgR2rKb2jl2-3c?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Village+of+Baytowne+Wharf/data=!4m10!3m9!1s0x88915eb18007f403:0x376d4194f3fddfb3!5m2!4m1!1i2!8m2!3d30.390788!4d-86.324086!16s%2Fg%2F11b8_6_g49!19sChIJA_QHgLFekYgRs9_985RBbTc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Spiaggia/data=!4m10!3m9!1s0x88915bb23a6cc455:0xa7cd9b8361193795!5m2!4m1!1i2!8m2!3d30.3798078!4d-86.401762!16s%2Fg%2F11r1_zcvvg!19sChIJVcRsOrJbkYgRlTcZYYObzac?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Crystal+Sands+-+Destin+Rentals/data=!4m10!3m9!1s0x88915b21e75b0a83:0x43217722aaaa13af!5m2!4m1!1i2!8m2!3d30.3814761!4d-86.4178677!16s%2Fg%2F11fkpvr5rx!19sChIJgwpb5yFbkYgRrxOqqiJ3IUM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Crystal+Sands+Condos/data=!4m10!3m9!1s0x88915be66483bb99:0xb8ac5011a171f772!5m2!4m1!1i2!8m2!3d30.3814616!4d-86.4177758!16s%2Fg%2F11l2v2tbfy!19sChIJmbuDZOZbkYgRcvdxoRFQrLg?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Brooks+and+Shorey+Resorts/data=!4m10!3m9!1s0x88913f27c8aa1f03:0x5b0753d2e6dacc51!5m2!4m1!1i2!8m2!3d30.4064104!4d-86.6047422!16s%2Fg%2F1v5k3t23!19sChIJAx-qyCc_kYgRUcza5tJTB1s?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Silver+Shells+Beach+Resort+%26+Spa/data=!4m10!3m9!1s0x889144821079b95d:0x1620ef406c87006c!5m2!4m1!1i2!8m2!3d30.3866487!4d-86.454691!16s%2Fg%2F11b7l2sj6y!19sChIJXbl5EIJEkYgRbACHbEDvIBY?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sterling+Sands+Vacation+Rentals/data=!4m10!3m9!1s0x889144792e78fdc9:0x41d05fac4538b4aa!5m2!4m1!1i2!8m2!3d30.3846709!4d-86.4645897!16s%2Fg%2F1tdy579v!19sChIJyf14LnlEkYgRqrQ4Raxf0EE?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Grandview+Condominums/data=!4m10!3m9!1s0x88915bf29cb504d7:0x33de4523e24f2610!5m2!4m1!1i2!8m2!3d30.3739196!4d-86.3560673!16s%2Fg%2F11g6jr2xg1!19sChIJ1wS1nPJbkYgRECZP4iNF3jM?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Magnolia+House+by+Holiday+Isle/data=!4m10!3m9!1s0x889146ab07b90d85:0x4c3c0b82c9c1ac32!5m2!4m1!1i2!8m2!3d30.386191!4d-86.503009!16s%2Fg%2F11b6dh7rz5!19sChIJhQ25B6tGkYgRMqzByYILPEw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/The+Islander+Resort/data=!4m10!3m9!1s0x889146aa05bdcb67:0x274c7d49a0e1deaa!5m2!4m1!1i2!8m2!3d30.3838159!4d-86.5004837!16s%2Fg%2F1thtdxrv!19sChIJZ8u9BapGkYgRqt7hoEl9TCc?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Emerald+Shores/data=!4m10!3m9!1s0x88915b42033560b5:0x65fa294436e8d6ff!5m2!4m1!1i2!8m2!3d30.3826965!4d-86.3965408!16s%2Fg%2F11fj2sv2y1!19sChIJtWA1A0JbkYgR_9boNkQp-mU?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Sea+Oats+Motel/data=!4m10!3m9!1s0x88915b5478476d55:0xfa6232f2a31d101e!5m2!4m1!1i2!8m2!3d30.3812082!4d-86.4154717!16s%2Fg%2F1tk9rjyl!19sChIJVW1HeFRbkYgRHhAdo_IyYvo?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Windancer/data=!4m10!3m9!1s0x88915bee205c7f3f:0xddf14c76e105ba29!5m2!4m1!1i2!8m2!3d30.3734581!4d-86.3514187!16s%2Fg%2F1tgx7cs5!19sChIJP39cIO5bkYgRKboF4XZM8d0?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Wyndham+Bay+Club+II/data=!4m10!3m9!1s0x88915eaaaec6cb0b:0xc117d8c3c328c4ed!5m2!4m1!1i2!8m2!3d30.3851393!4d-86.3373394!16s%2Fg%2F11bcdhs91x!19sChIJC8vGrqpekYgR7cQow8PYF8E?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Beach+Pointe+301+by+Destin+Getaways/data=!4m10!3m9!1s0x88915b5dfeb7c3bd:0xceeb7e8a4bae3a1!5m2!4m1!1i2!8m2!3d30.3802479!4d-86.3987261!16s%2Fg%2F11jpf0whs3!19sChIJvcO3_l1bkYgRoeO6pOi37gw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/St.+Croix+502+Silver+Shells+-+231887/data=!4m10!3m9!1s0x889144819e80d769:0x29a106982d64fe4c!5m2!4m1!1i2!8m2!3d30.385171!4d-86.455117!16s%2Fg%2F11ngj86kgy!19sChIJadeAnoFEkYgRTP5kLZgGoSk?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Maravilla+Beach+Resort+by+Panhandle+Getaways/data=!4m10!3m9!1s0x88915b646a4e2fe9:0xcecd2e5a16b5e9a8!5m2!4m1!1i2!8m2!3d30.3790969!4d-86.3919673!16s%2Fg%2F11cm_gq0w0!19sChIJ6S9OamRbkYgRqOm1Flouzc4?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Waterscape+Resort/data=!4m10!3m9!1s0x88913f4a5faf0f8f:0xd73f1f78b5282206!5m2!4m1!1i2!8m2!3d30.3946967!4d-86.5992339!16s%2Fg%2F11d_8yyq78!19sChIJjw-vX0o_kYgRBiIotXgfP9c?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Henderson+Beach+Villas/data=!4m10!3m9!1s0x8891453e84fe3b8f:0xc4ef50b6885f327d!5m2!4m1!1i2!8m2!3d30.3824825!4d-86.4302799!16s%2Fg%2F11fncklwdf!19sChIJjzv-hD5FkYgRfTJfiLZQ78Q?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Azure+Condo+Rentals+in+Fort+Walton+Beach+by+Vacasa/data=!4m10!3m9!1s0x88913f35bdcbef43:0x7c1ce4a5b3b3689f!5m2!4m1!1i2!8m2!3d30.3954037!4d-86.6019764!16s%2Fg%2F1tfqgl27!19sChIJQ-_LvTU_kYgRn2izs6XkHHw?authuser=0&hl=bs&rclk=1",
        "https://www.google.com/maps/place/Islander+%23615+-+Dolphin+View+I/data=!4m10!3m9!1s0x889146aa19ca0e45:0x24bce9fc09d8283!5m2!4m1!1i2!8m2!3d30.3839601!4d-86.5007436!16s%2Fg%2F11d_y97z4_!19sChIJRQ7KGapGkYgRg4KdwJ_OSwI?authuser=0&hl=bs&rclk=1"
    ]

    # Number of threads
    num_threads =  multiprocessing.cpu_count()
    chunk_size = len(search_urls) // num_threads

    # Creating threads
    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = None if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=thread_worker, args=(search_urls[start:end],))
        threads.append(thread)
        thread.start()

    # Waiting for threads to finish
    for thread in threads:
        thread.join()

    # Save results to JSON
    save_to_json()

    print("Scraping completed!")