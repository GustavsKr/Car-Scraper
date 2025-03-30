from scrape_selected_links import *
from dbController import DbController
from scrapingController import ScrapingController
from utils.config import DB_CONNECTION_STRING, ss_links
from utils.logger import logger
from playwright.async_api import async_playwright

import asyncio, random


async def scrape_newest_links(browser, db_controller, website, url):
    global ss_links
    while True:
        try:
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': random.randint(1024, 1920), 'height': random.randint(768, 1080)},
                locale='en-US',
                timezone_id='Europe/Riga',
                geolocation={'longitude': 24.105, 'latitude': 56.946},
                permissions=['geolocation'],
                extra_http_headers={
                    'Referer': 'https://www.google.com/',
                    'Accept-Language': 'lv-LV,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                },
                storage_state=None  # Make sure no previous session or cache is retained
            )
            page = await context.new_page()
            last_saved_url = None 
            try:
                await page.goto(url, timeout=60000)
                logger.warning(f"Successfully (re)started {website} newest links page")
                await asyncio.sleep(2)  # Allow the page to stabilize
            except Exception:
                logger.exception("Error loading auto24.ee page")
                if page:
                    await page.close()
                page = await context.new_page()
                logger.warning(f"Attempting to restart {website} newest links page")
                await scrape_newest_links(context, db_controller, website, url)
                return

            for _ in range(2000): # Restart the context after 2000 page reloads (memory management/clears cache)
                try:
                    if website == "eng.auto24.ee":
                        await page.wait_for_selector("a.row-link[href]", timeout=60000)
                        scraped_urls = await page.evaluate('''
                            Array.from(document.querySelectorAll("a.row-link[href]"))
                                .map(a => a.getAttribute("href"))
                                .filter(url => url)
                        ''')

                    elif website == "skelbiu.lt":
                        await page.wait_for_selector("a.gallery-item-element-link[href]", timeout=60000)
                        scraped_urls = await page.evaluate('''
                            Array.from(document.querySelectorAll("a.gallery-item-element-link[href]"))
                                .map(a => a.getAttribute("href"))
                                .filter(url => url)
                        ''')

                    elif website == "ss.com":
                        await page.wait_for_selector("tr[id^='tr_'] a[href]", timeout=60000)
                        scraped_urls = await page.evaluate('''
                            Array.from(document.querySelectorAll("tr[id^='tr_'] a[href]"))
                                .filter(a => a.querySelector("img"))
                                .map(a => a.getAttribute("href"))
                                .filter(url => url && url.includes("/transport/cars/"))
                        ''')


                    untouched_urls = []

                    # Determine unmatched urls based on local last_saved_url
                    if scraped_urls:
                        if last_saved_url and last_saved_url in scraped_urls:
                            untouched_urls = scraped_urls[:scraped_urls.index(last_saved_url)]
                        last_saved_url = scraped_urls[0] if scraped_urls else last_saved_url

                    # Prepare links for batch insertion
                    links_to_insert = set()
                    for url in untouched_urls:                        
                        if not url.startswith("https://"):
                            full_url = "https://" + website + url
                        else:
                            full_url = url
                        links_to_insert.add(full_url)
                    
                    links_to_insert = list(links_to_insert)

                    # Batch insert new links
                    if links_to_insert:
                        logger.info(f"Storing {len(links_to_insert)} {website} links to ss_links")
                        ss_links.extend(links_to_insert)

                    # Reload the page for new data
                    await asyncio.sleep(1)
                    await page.reload(wait_until='load')
                except Exception: 
                    logger.exception(f"Error while scraping {website}:")
                    break
            if page:
                await page.close()
            if context:
                await context.close()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Error in scrape_newest_links:")
            logger.warning(f"Attempting to restart {website} newest links page")
        finally:
            if page:
                await page.close()
            if context:
                await context.close()


async def scrape_selected_links(browser, db_controller, scraper):
    try:
        logger.warning("Successfully started scrape_selected_links")
        global ss_links
        tasks = []
        while True:
            await asyncio.sleep(2)  # Allow other tasks to run
            try:
                if ss_links:
                    for url in ss_links:
                        # Determine the appropriate scraper
                        scraper_map = {
                            "eng.auto24.ee": scrape_auto24_selected_links,
                            "skelbiu.lt": scrape_autoplius_selected_links,
                            "ss.com": scrape_ss_selected_links, # Using BS4/Requests instead of playwright (faster and less resource intensive)
                        }
                        for key, func in scraper_map.items():
                            if key in url:
                                task = asyncio.create_task(
                                    scrape_with_timeout(
                                        func(browser, url, db_controller, scraper),
                                        timeout=90
                                    )
                                )
                                tasks.append(task)
                                await asyncio.sleep(1)  # Delay to avoid overwhelming resources
                                break
                # Clean up completed and cancelled tasks
                if tasks:
                    tasks = [task for task in tasks if not task.done()]
            except Exception as e:
                logger.exception(f"Error while processing links: {e}")
    except asyncio.CancelledError:
        return
    except Exception as e:
        logger.exception(f"Error in scrape_selected_links: {e}")
    finally:
        logger.info("Cleaning up pending tasks...")
        for task in tasks:
            if not task.done():
                task.cancel()
        if browser:
            await asyncio.gather(*tasks, return_exceptions=True)

async def scrape_with_timeout(scrape_task, timeout):
    try:
        return await asyncio.wait_for(scrape_task, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Scraping task timed out and was cancelled")
    except Exception as e:
        logger.error(f"Scraping task failed: {e}")

async def scrape_links_headless(scraper, db_controller):
    async with async_playwright() as playwright:
        while True:
            try:
                logger.warning("Starting headless browser")
                # Browser connection and event listeners
                browser = await playwright.chromium.launch(
                    headless=True,  # Headless browser
                    args = [
                        '--no-sandbox',                      # Required for running in Docker
                        '--disable-setuid-sandbox',          # Bypass sandboxing restrictions
                        '--disable-dev-shm-usage',           # Use /tmp for shared memory
                        '--disable-gpu',                     # Disable GPU as it’s unnecessary for headless
                        '--disable-extensions',              # Avoid loading unnecessary extensions
                        '--disable-blink-features=AutomationControlled',  # Minimize detection
                        '--disable-popup-blocking',          # Prevent pop-ups from interfering
                        '--no-zygote',                       # Improve performance by skipping zygote processes
                        '--headless=new',                    # Use new headless mode for better support
                        '--hide-scrollbars',                 # Reduce rendering overhead
                        '--mute-audio',                      # Avoid audio rendering overhead
                        '--enable-automation',               # Needed for legitimate bot scenarios
                        '--enable-low-end-device-mode',      # Uses less memory, good performance for running from docker
                        '--disable-features=TranslateUI',    # Disable translation prompt
                        '--disable-background-networking',   # Reduce unnecessary network activity
                        '--disable-background-timer-throttling',  # Prevent timer throttling
                        '--disable-background-fetch',        # Disable background fetches
                        '--disable-webgl',                   # Turn off WebGL for rendering optimization
                        '--disable-client-side-phishing-detection',  # Minimize resource use
                        '--disable-sync',                    # Avoid syncing overhead
                        '--disable-accelerated-video-decode',   # Avoid using hardware acceleration for video decoding
                        '--disable-web-security',            # For cross-origin requests (if needed)
                        '--blink-settings=imagesEnabled=false',  # Disable image loading
                        '--disable-cache',                   # Disable caching
                        '--disk-cache-size=0',               # No disk cache usage
                        '--renderer-process-limit=4',        # Restrict renderer processes to reduce memory overhead # You might adjust the limit (=2 or =3) if memory remains constrained.
                    ]
                )
                tasks = []
                try:
                    tasks = [
                        # Seperate pages that refresh and scrape the newest links and put them in ss_links variable
                        asyncio.create_task(scrape_newest_links(browser, db_controller, "eng.auto24.ee", "https://eng.auto24.ee/kasutatud/nimekiri.php?bn=2&a=100&aj=&ssid=221873451&j%5B%5D=1&j%5B%5D=2&j%5B%5D=3&j%5B%5D=4&j%5B%5D=5&j%5B%5D=6&j%5B%5D=61&j%5B%5D=7&j%5B%5D=8&j%5B%5D=69&j%5B%5D=70&j%5B%5D=9&j%5B%5D=10&j%5B%5D=11&ae=1&af=20&by=2&otsi=search")),
                        asyncio.create_task(scrape_newest_links(browser, db_controller, "skelbiu.lt", "https://www.skelbiu.lt/skelbimai/?autocompleted=1&keywords=&cost_min=&cost_max=&type=1&year_min=&year_max=&transmission=0&engine_min=&engine_max=&power_min=&power_max=&mileage_min=&mileage_max=&cities=0&distance=0&mainCity=0&search=1&category_id=31&user_type=0&ad_since_min=0&ad_since_max=0&visited_page=1&orderBy=1&detailsSearch=1")),
                        asyncio.create_task(scrape_newest_links(browser, db_controller, "ss.com", "https://www.ss.com/en/transport/today/")),

                        # Function for scraping newest links from ss_links variable
                        asyncio.create_task(scrape_selected_links(browser, db_controller, scraper)),
                    ]
                    logger.warning("Headless browser succesfully started")
                    # Run both scraping tasks concurrently
                    await asyncio.wait_for(asyncio.gather(*tasks), timeout=12*60*60) # Wait for 12 hours before restarting browser (to optimise memory)
                except:
                    logger.warning("12 hours have passed, restarting browser")
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                    tasks = []
                    if browser and browser.is_connected():
                        for context in browser.contexts:
                            for page in context.pages:
                                try:
                                    await page.close()
                                except Exception:
                                    logger.exception("Error closing page:")
                            try:
                                await context.close()
                            except Exception:
                                logger.exception("Error closing context:")
                        await browser.close()
            except Exception:
                logger.exception("Error in scrape_links_headless:")
                if browser and browser.is_connected():
                    for context in browser.contexts:
                        for page in context.pages:
                            try:
                                await page.close()
                            except Exception:
                                logger.exception("Error closing page:")
                        try:
                            await context.close()
                        except Exception:
                            logger.exception("Error closing context:")
                    await browser.close()


if __name__ == "__main__":
    try:
        db_controller = DbController(DB_CONNECTION_STRING)
        scraper = ScrapingController()
        # Will need to run alongside a non-headless browser if more bot-secure websites are present (for example, mobile.de)
        asyncio.run(scrape_links_headless(scraper, db_controller))
    except Exception:
        logger.exception("Failed starting the code")
        