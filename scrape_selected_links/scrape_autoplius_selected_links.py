from utils.logger import logger
from datetime import datetime
import re, random


async def scrape_autoplius_selected_links(browser, url, db_controller, scraper):
    """Scrapes autoplius.lt and skelbiu.lt cars through skelbiu.lt"""
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
        await page.goto(url, timeout=90000)

        if page.url.startswith("https://www.skelbiu.lt/"):
            await scrape_skelbiu_selected_links(page, url, db_controller, scraper)
        else:
            await scrape_autopl_selected_links(page, url, db_controller, scraper)
    finally:
        if page:
            await page.close()
        if context:
            await context.close()



async def scrape_skelbiu_selected_links(page, url, db_controller, scraper):
    """Scrapes skelbiu.lt cars"""
    try:
        # Initialize variables
        car_img_url = car_brand = car_model = scraped_price = year = volume = engine_type = \
        gearbox = body_type = color = area = run = checkup = None

        # Scrape car image URL (if available, otherwise None)
        car_img_element = await page.query_selector("div.main-photo.js-open-photo img")
        car_img_url = await car_img_element.get_attribute("src") if car_img_element else None

        # Scrape area
        area_element = await page.query_selector("p.cities")
        area = (await area_element.text_content()).strip().lower() if area_element else None
        if area:
            area = scraper.translate_area(area, "lithuania")

        # Scrape price
        price_element = await page.query_selector("p.price")
        if price_element:
            price_text = (await price_element.text_content()).strip() if price_element else None
            scraped_price = scraper.get_int_from_string(price_text)

        # Scrape car details from the details container
        details_rows = await page.query_selector_all("div#details-container div.details-row")
        for row in details_rows:
            label_element = await row.query_selector("label")
            value_element = await row.query_selector("span")
            label = (await label_element.text_content()).strip().lower() if label_element else None
            value = (await value_element.text_content()).strip() if value_element else None

            if not label or not value:
                continue

            if "gamintojas" in label:
                car_brand = scraper.translate_car_brand(car_brand)
            elif "modelis" in label:
                car_model = value
                car_model = car_model.replace("+", "plus")
                car_model = scraper.clean_text(car_model)
            elif "metai" in label:
                year = int(value)
            elif "kėbulo tipas" in label:
                body_type = value.lower().strip()
                body_type = scraper.translate_body_type(body_type)
            elif "rida" in label:
                run = scraper.get_int_from_string(value)
            elif "spalva" in label:
                color = value.split("/")[0].strip().lower()
                color = scraper.translate_color(color)
            elif "darb. tūris" in label:
                volume_match = re.search(r'[\d.]+', value)
                volume = float(volume_match.group(0)) if volume_match else None
            elif "techninė apžiūra" in label:
                checkup = value.replace("-", ".")  # Convert to MM.YYYY format
                if checkup:
                    parts = checkup.split(".")
                    if len(parts) == 2:
                        checkup = f"{parts[1]}.{parts[0]}"  # Swap MM and YYYY
            elif "kuras" in label:
                engine_type = value.lower().strip()
                engine_type = scraper.translate_engine_type(engine_type)
            elif "pavarų dėžė" in label:
                gearbox = value.lower()
                gearbox = "manual" if "mechaninė" in gearbox else "automatic" if "automatinė" in gearbox else None
            elif "kėbulo numeris (vin)" in label:
                vin = value.strip().upper()
        if body_type == "other":
            body_type == None
        if engine_type == "other":
            engine_type = None

        if car_brand:
            # Add car details to the database
            db_controller.add_to_cars_table(
                table_name="autoplius_cars",
                url=page.url,
                img_url=car_img_url,
                brand=car_brand,
                model=car_model,
                price=scraped_price,
                year=year,
                volume=volume,
                engine_type=engine_type,
                gearbox=gearbox,
                body_type=body_type,
                color=color,
                area=area,
                deal_type="sell",
                run=run,
                checkup=checkup,
                fetching_date=datetime.now(),
            )
            logger.info(f"ADDED {page.url} to autoplius_cars")
    except Exception:
        logger.exception(f"Error scraping details from link {url} (autoplius.lt)")

async def scrape_autopl_selected_links(page, url, db_controller, scraper):
    """Scrapes autoplius.lt cars"""
    try:
        # Initialize variables
        car_img_url = car_brand = car_model = scraped_price = year = volume = engine_type = \
        gearbox = body_type = color = area = run = checkup = None

        color_translations = {
            "balta": "white",
            "geltona": "yellow",
            "juoda": "black",
            "mėlyna": "blue",
            "oranžinė": "orange",
            "pilka": "grey",
            "sidabrinė": "silver",
            "raudona": "red",
            "ruda": "brown",
            "violetinė": "purple",
            "žalia": "green",
            "kita": "other",
            "marga": "other",
        }
    
        try:
            # Navigate to the URL
            await page.goto(url, timeout=90000)
        except Exception:
            logger.exception(f"Error loading link {url}")
            return

        # Initialize variables
        car_img_url = car_brand = car_model = scraped_price = year = volume = engine_type = \
        gearbox = body_type = color = area = run = scraped_checkup = checkup = None

        try:
            # Scrape car image url 
            try:
                await page.wait_for_selector("div.thumbnail img", timeout=10000)  # Adjust timeout as needed
            except Exception:
                pass
            car_img_element = await page.query_selector("div.thumbnail img")
            car_img_url = await car_img_element.get_attribute("src") if car_img_element else None

            # Scrape car brand and model
            breadcrumbs_element = await page.query_selector("ol.breadcrumbs")
            if breadcrumbs_element:
                breadcrumb_items = await breadcrumbs_element.query_selector_all("li.crumb a")
                if len(breadcrumb_items) >= 2:
                    # Extract the car brand and model from the last two breadcrumb items
                    car_brand = (await breadcrumb_items[-2].text_content()).strip()  # Second-to-last item is the brand
                    car_model = (await breadcrumb_items[-1].text_content()).strip()  # Last item is the model
                    car_model = car_model.replace("+", "plus")
                    car_model = scraper.clean_text(car_model)
                    car_model = re.sub(r"[^a-zA-Z0-9\s]+", "", car_model) if car_model else None
                    # Translate/format car brand 
                    car_brand = scraper.translate_car_brand(car_brand)

            # Scrape price
            price_element = await page.query_selector("div.price")
            price_text = (await price_element.text_content()).strip() if price_element else None
            if price_text:
                # Split the text by newline or non-breaking space and clean up
                price_lines = price_text.split("\n")  # Break into lines
                price_main = price_lines[0].strip()  # Take the first line (main price part)
                # Extract the numeric part from the cleaned main price line
                scraped_price = scraper.get_int_from_string(price_main)
            else:
                scraped_price = None

            # Scrape area
            area_element = await page.query_selector("span.seller-contact-location")
            area_text = (await area_element.text_content()).strip() if area_element else None
            area = area_text.split(",")[0].strip().lower() if area_text else None
            if area:
                area = scraper.translate_area(area, "lithuania")

            # Scrape parameters from parameter rows
            parameter_rows = await page.query_selector_all("div.parameter-row")
            for row in parameter_rows:
                label_element = await row.query_selector("div.parameter-label")
                value_element = await row.query_selector("div.parameter-value")
                label = (await label_element.text_content()).strip().lower() if label_element else None
                value = (await value_element.text_content()).strip() if value_element else None

                if not label or not value:
                    continue

                if "pirma registracija" in label:
                    year = int(value.split("-")[0])  # Extract year
                elif "rida" in label:
                    run = scraper.get_int_from_string(value)  # Extract mileage
                elif "kuro tipas" in label:
                    engine_type = value.lower().strip()  # Extract fuel type
                    engine_type = scraper.translate_engine_type(engine_type)
                elif "kėbulo tipas" in label:
                    body_type = value.lower().split(" ")[0]
                    body_type = scraper.translate_body_type(body_type)
                elif "pavarų dėžė" in label:
                    gearbox = value.lower()
                    gearbox = "manual" if "mechaninė" in gearbox else "automatic" if "automatinė" in gearbox else None
                elif "spalva" in label:
                    color = value.split("/")[0].strip().lower()  # Extract main color
                    color = scraper.translate_color(color)
                elif "variklis" in label and "cm" in value.lower():
                    if value and ("cc" in value.lower() or "cm³" in value.lower()):
                        volume_match = re.search(r'\d+', value)
                        if volume_match:
                            volume_int = int(volume_match.group(0))
                            volume = round(volume_int / 1000, 1)  # Convert cc or cm³ to liters and round to one decimal place  # Convert engine volume
                elif "tech. apžiūra iki" in label:
                    scraped_checkup = value.replace("-", ".")  # Convert to MM.YYYY format
                    if scraped_checkup:
                        parts = scraped_checkup.split(".")
                        if len(parts) == 2:
                            checkup = f"{parts[1]}.{parts[0]}"  # Swap MM and YYYY

            if body_type == "other":
                body_type = None
            if engine_type == "other":
                engine_type = None

            if car_brand:
                # Add car details to the database
                db_controller.add_to_cars_table(
                    table_name="autoplius_cars",
                    url=page.url,
                    img_url=car_img_url,
                    brand=car_brand,
                    model=car_model,
                    price=scraped_price,
                    year=year,
                    volume=volume,
                    engine_type=engine_type,
                    gearbox=gearbox,
                    body_type=body_type,
                    color=color,
                    area=area,
                    deal_type="sell",
                    run=run,
                    checkup=checkup,
                    fetching_date=datetime.now(),
                )
                logger.info(f"ADDED {page.url} to autoplius_cars")
        except Exception:
            logger.exception(f"Error scraping details from link {page.url}")
    except Exception:
        logger.exception(f"Error scraping link {page.url}")