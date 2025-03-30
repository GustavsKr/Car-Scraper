import re
from datetime import datetime
from bs4 import BeautifulSoup
from requests import Session
from utils.logger import logger

async def scrape_ss_selected_links(browser, url, db_controller, scraper):
    try:
        with Session() as session:
            # Extract data from car link
            url_response = session.get(url)
            soup = BeautifulSoup(url_response.text, "html.parser")

            # Set all variables to None
            deal_type = car_brand = car_model = area = img_url = scraped_price = brand_model = run = \
            engine_type = volume = gearbox = body_type = listing_date = scraped_checkup = volume_engine = company = None

            # Scrape deal type
            headtitle = soup.select_one('h2.headtitle')
            headtitle_links = soup.select('h2.headtitle a')
            for type in ["sell", "buy", "repair", "change", "miscellaneous"]:
                if type in headtitle.get_text(strip=True).lower():
                    deal_type = type
                    break

            # Exract area seperately
            contacts_table = soup.find('table', class_='contacts_table')
            place_td = contacts_table.find('td', string="Place:")
            if place_td:
                place_td = place_td.find_next_sibling('td')
                if place_td:
                    area = place_td.get_text(strip=True).split()[0].lower() 
                    if area == "yurmala":
                        area = "jurmala"
                    if area == "lithuania,":
                        area = "lithuania"
                else:
                    logger.error("No next sibling found for 'Place:' td")
            else:
                logger.error("'Place:' td not found in contacts_table")

            # Extract 'src' attributes from all car images
            image_elements = soup.select('img.pic_thumbnail.isfoto')
            scraped_item_imgs = [img.get("src") for img in image_elements if img.get("src")]
            all_image_urls = [f"{img[:-5]}800.jpg" if img else None for img in scraped_item_imgs]
            # Assign the first image URL
            img_url = all_image_urls[0] if all_image_urls else None

            # Extract the price seperately
            scraped_price = scraper.bs4_scrape_element(soup, 'span[id="tdo_8"]')
            if scraped_price is None:
                scraped_price = scraper.bs4_scrape_element(soup, 'td[id="tdo_8"]')
            if scraped_price and scraped_price.endswith("€"):
                scraped_price = scraped_price.replace(' ', '').replace('€', '').replace(',', '.')
            if scraped_price == 'call':
                scraped_price = None
                
            # Extract the rest of car parameters separately
            if "transport/cars" in url:
                volume_engine = scraper.bs4_scrape_element(soup, 'td[id="tdo_15"]')
                if volume_engine:
                    if volume_engine == "electric":
                        engine_type = volume_engine
                        volume = None
                    else:
                        try:
                            parts = volume_engine.split(" ", 1)
                            volume = parts[0]
                            engine_type = parts[1] if len(parts) > 1 else None  # Set engine_type to None if not present
                        except ValueError:
                            logger.error(f"Error splitting volume and engine type: {volume_engine}")

                scraped_checkup = scraper.bs4_scrape_element(soup, 'td[id="tdo_223"]')
                if not scraped_checkup or not re.match(r"^\d{2}\.\d{4}$", scraped_checkup):
                    scraped_checkup = None

                scraped_gearbox = scraper.bs4_scrape_element(soup, 'td[id="tdo_35"]')
                if scraped_gearbox:
                    gearbox = 'manual' if 'manual' in scraped_gearbox else ('automatic' if 'automatic' in scraped_gearbox else None)
                else:
                    gearbox = None
                    
                run = scraper.bs4_scrape_element(soup, 'td[id="tdo_16"]')
                if run:
                    run = run.replace(' ', '')      
                    run = int(run)              
                body_type = scraper.bs4_scrape_element(soup, 'td[id="tdo_32"]')

                # Scraping brand and model
                if len(headtitle_links) >= 3:
                    car_brand = headtitle_links[1].text.strip().lower()
                    car_model = headtitle_links[2].text.strip().lower().replace('+', 'plus')

                if "exclusive-cars" in url or "retro-cars" in url or "sport-cars" in url or "tuned-cars" in url:
                    scraped_checkup = None
                    car_brand = scraper.bs4_scrape_element(soup, 'td[id="tdo_51"]')
                    car_model = scraper.bs4_scrape_element(soup, 'td[id="tdo_24"]').replace('+', 'plus')
                    run=None
                    body_type = None
                    if "retro-cars" in url:
                        gearbox = None
                elif "electric-cars" in url:
                    engine_type = "electric"
                    volume = None
                    gearbox = None
                    scraped_checkup = None
                    body_type = None
                    brand_model = scraper.bs4_scrape_element(soup, 'td[id="tdo_51"]')
                    if brand_model:
                        car_brand, car_model = brand_model.split(" ", 1)
                        car_model = car_model.replace('+', 'plus')
                    else:
                        car_brand, car_model = None, None 

                car_brand = scraper.translate_car_brand(car_brand)
                car_model = re.sub(r'[\s&()!-]+', '', car_model) if car_model else None 
                
                color = scraper.bs4_scrape_element(soup, 'td[id="tdo_17"]').split()[0] if scraper.bs4_scrape_element(soup, 'td[id="tdo_17"]') else None
                if color == "ligh":
                    color = "blue"
                elif color == "dark":
                    color = "red"
                color = scraper.translate_color(color)
                year = scraper.bs4_scrape_element(soup, 'td[id="tdo_18"]').split()[0] if scraper.bs4_scrape_element(soup, 'td[id="tdo_18"]') else None,
                body_type = scraper.translate_body_type(body_type)
                engine_type = scraper.translate_engine_type(engine_type)

                if car_brand:
                    db_controller.add_to_cars_table(
                        table_name="ss_cars",
                        url=url,
                        img_url=img_url,
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
                        deal_type=deal_type,
                        run=run,
                        checkup=scraped_checkup,
                        fetching_date=datetime.now()
                    )
                    logger.info(f"ADDED {url} to ss_cars")
    except Exception as e:
        logger.error(f"Error in scrape_ss_selected_links:", exc_info=e)