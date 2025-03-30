from utils.logger import logger
import re, asyncio, random
from datetime import datetime
from utils.logger import logger

async def scrape_auto24_selected_links(browser, url, db_controller, scraper):
    """Scrapes auto24.ee cars"""
    try:
        await asyncio.sleep(30) # Wait for the car image to load in auto24 servers
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

        try:
            await page.goto(url, timeout=60000)
        except Exception:
            logger.exception(f"Error loading link {url}")
            return
        

        try:
            # Scrape car image URL
            car_img_url = await page.evaluate('''() => {
                const imgElement = document.querySelector("a.vImages__item img");
                return imgElement ? imgElement.src : null;
            }''')

            # Scrape car brand and model
            breadcrumbs_div = await page.query_selector("div.b-breadcrumbs")
            if breadcrumbs_div:
                # Extract all breadcrumb items in a single call
                breadcrumb_items = await breadcrumbs_div.query_selector_all(".b-breadcrumbs__item")
                breadcrumb_texts = [
                    (await item.text_content()).strip() for item in breadcrumb_items
                ]
                # Ensure there are enough breadcrumbs to determine brand and model
                if len(breadcrumb_texts) >= 3:
                    # Use the second-to-last breadcrumb as the car brand
                    car_brand = breadcrumb_texts[1].split()[0]
                    car_brand = re.sub(r"[^a-zA-Z0-9]+", "", car_brand)
                    car_brand = scraper.translate_car_brand(car_brand)
                    # Use the last breadcrumb as the car model
                    car_model = breadcrumb_texts[2].replace(" ", "").lower()
                    car_model = car_model.replace('+', 'plus')
                    car_model = re.sub(r"[^a-zA-Z0-9]+", "", car_model)
                else:
                    car_brand = car_model = None
            else:
                car_brand = car_model = None

            # Scrape price from the first element
            try:
                await page.wait_for_selector("tr.field-hind span.value", timeout=10000)
            except Exception:
                pass
            price_element = await page.query_selector("tr.field-hind span.value")
            scraped_price = scraper.get_int_from_string(await price_element.text_content() if price_element else None)
            # If price is not found, try to find it in the fallback element
            if scraped_price is None:
                # Scrape price from the second element (bargain price)
                bargain_price_element = await page.query_selector("tr.field-soodushind td.field span.value")
                if bargain_price_element:
                    scraped_price = scraper.get_int_from_string(await bargain_price_element.text_content())

            # Scrape year
            year_element = await page.query_selector("tr.field-month_and_year span.value")
            year_text = (await year_element.text_content()).strip() if year_element else None
            if year_text:
                if "/" in year_text:
                    parts = year_text.split("/")
                    if len(parts) > 1:
                        year = int(parts[1])  # Extract year after '/'
                    else:
                        logger.error(f"(auto24)Unexpected year format: {year_text}")
                        year = None
                else:
                    try:
                        # If no '/' is found, assume the year is the whole scraped value
                        year = int(year_text)
                    except ValueError:
                        logger.error(f"(auto24)Invalid year format: {year_text}")
                        year = None
            else:
                year = None

            # Scrape volume
            volume_element = await page.query_selector("tr.field-mootorvoimsus span.value")
            volume_text = await volume_element.text_content() if volume_element else None
            try:
                volume = float(volume_text.split()[0]) if volume_text else None
            except:
                volume = None

            # Scrape engine type
            engine_element = await page.query_selector("tr.field-kytus span.value")
            engine_type = (await engine_element.text_content()).strip().lower().split()[0] if engine_element else None
            engine_type = scraper.translate_engine_type(engine_type)

            # Scrape gearbox
            gearbox_element = await page.query_selector("tr.field-kaigukast_kaikudega span.value")
            if gearbox_element:
                gearbox_text = (await gearbox_element.text_content()).strip().lower()
                gearbox = gearbox_text.split(' ')[0]
            else:
                gearbox = None
            if gearbox == "semi-automatic":
                gearbox = "automatic"

            # Scrape body type
            body_type_element = await page.query_selector("tr.field-keretyyp span.value")
            body_type = (await body_type_element.text_content()).strip().lower() if body_type_element else None

            if body_type:
                # Extract the first word if parentheses are present
                body_type = body_type.split(' (')[0]
                body_type = scraper.translate_body_type(body_type)

            # Scrape description
            description=None
            try:
                raw_text = await page.eval_on_selector(
                ".-user_other",
                "el => el.innerHTML"
                )
                if raw_text:
                    description = raw_text.replace("<br>", " ")
                    description = re.sub(r'\s+', ' ', description).strip()
            except Exception:
                description = None


            # Scrape phone and company
            try:
                phone = await page.eval_on_selector(
                    "#pn-value .value",
                    "el => el.textContent.trim()"
                )
                phone = phone.replace(" ", "")
            except Exception:
                phone = None
            try:
                company = await page.eval_on_selector(
                    "h2.commonSubtitle a",
                    "el => el.textContent.trim()"
                )
            except Exception:
                company = None

            # Scrape color
            color_element = await page.query_selector("tr.field-varvus span.value")
            color = (await color_element.text_content()).lower() if color_element else None
            if color == "other":
                color = None
            if color:
                # Remove any text inside parentheses and strip extra spaces
                color = re.sub(r'\(.*?\)', '', color).strip()
                # Check if the first word is "light" and adjust accordingly
                words = color.split()
                if (words[0] == "light" or words[0] == "dark") and len(words) > 1:
                    # Take only the second word if the first word is "light" or "dark"
                    color = words[1].strip()
                else:
                    # Otherwise, just take the first word
                    color = words[0] if words else None
                # Remove any punctuation at the end of the color string
                color = re.sub(r'[^\w\s]', '', color).strip()
                color = scraper.translate_color(color)

            # Scrape area
            area_element = await page.query_selector("div.-location b")
            area = (await area_element.text_content()).strip().lower() if area_element else None
            # If the area element is not found, try the fallback location element
            if not area:
                area_fallback_element = await page.query_selector("div.-location")
                if area_fallback_element:
                    area_text = await area_fallback_element.text_content()
                    # Extract the area after the text "Location of a vehicle:"
                    area = area_text.split("Location of a vehicle:")[-1].strip().lower() if "Location of a vehicle:" in area_text else None
            if area and "un raj." in area:
                area = area.split()[0]
            if area:
                area = scraper.translate_area(area, "estonia")

            # Scrape run (mileage)
            run_element = await page.query_selector("tr.field-labisoit span.value")
            run_text = await run_element.text_content() if run_element else None
            run = scraper.get_int_from_string(run_text)

            # Scrape checkup
            checkup_element = await page.query_selector("div.-status b")
            scraped_checkup = (await checkup_element.text_content()).strip().lower() if checkup_element else None
            if scraped_checkup and re.match(r"^\d{4}-\d{2}-\d{2}$", scraped_checkup):
                # Convert from "YYYY-MM-DD" to "MM.YYYY"
                date_parts = scraped_checkup.split("-")
                scraped_checkup = f"{date_parts[1]}.{date_parts[0]}"

            if body_type == "other":
                body_type == None
            if engine_type == "other":
                engine_type = None
                
            if car_brand:
                # Add the car to the database
                db_controller.add_to_cars_table(
                    table_name="auto24_cars",
                    url=url,
                    car_img_url=car_img_url,
                    car_brand=car_brand,
                    car_model=car_model,
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
                    checkup=scraped_checkup,
                    fetching_date=datetime.now()
                )
                logger.info(f"ADDED {url} to auto24_cars")

        except Exception:
            logger.exception(f"Error scraping link {url}")

    finally:
        if page:
            await page.close()
        if context:
            await context.close()
