import re, unicodedata, difflib, json
from difflib import get_close_matches
from utils.logger import logger

class ScrapingController:
    def __init__(self):
        with open("json/carData.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        self.car_brands = data.get("car_brand")
        self.areas = data.get("area")

    def clean_text(self, text):
        """Filters out unwanted characters and whitespaces (allow only letters, numbers, and dots)."""
        return re.sub(r'[^a-zA-Z0-9.]', '', text).strip()
    
    def get_int_from_string(self, text):
        """Converts a string to an integer, removing non-numeric characters."""
        return int(re.sub(r'\D', '', text)) if text else None
    
    def bs4_scrape_element(self, soup, selector, attr="text"):
        """Scrapes a selector using BeautifulSoup/Requests and lowercases it"""
        try:
            element = soup.select_one(selector)
            if element:
                element = element.text.strip() if attr == "text" else element.get(attr)
                if isinstance(element, str):
                    element = element.lower()
                return element
        except Exception as e:
            logger.error(f"Error scraping {selector}: {e}")
        return None

    def translate_area(self, input_area: str, default_value):
        """
        Translates the input area to a valid area in the areas dictionary.
        If no exact match is found, attempts to find the closest match.
        """
        if not input_area:
            logger.error("Area input is empty or None.")
            return default_value
        
        # Normalize the input and remove diacritical marks
        normalized_area = unicodedata.normalize('NFD', input_area)
        ascii_area = re.sub(r'[\u0300-\u036f]', '', normalized_area)
        cleaned_area = re.sub(r'[^a-z]', '', ascii_area.lower())
        
        # Check if the area is valid (country or city)
        for country, details in self.areas.items():
            if cleaned_area == country or cleaned_area in details.get("cities", {}):
                return cleaned_area  # Return the valid area
        
        # Collect all possible areas (countries and cities)
        possible_areas = {country for country in self.areas}
        for details in self.areas.values():
            possible_areas.update(details.get("cities", {}).keys())
        
        # Try to find the closest match
        closest_matches = get_close_matches(cleaned_area, possible_areas, n=1, cutoff=0.6)
        if closest_matches:
            closest_match = closest_matches[0]
            return closest_match  # Return the closest match
        
        # If no match is found, return "estonia" as the default
        logger.warning(f"Invalid area: {input_area}. Defaulting to {default_value}.")
        return default_value
    
    def translate_car_brand(self, car_brand):
        """
        Translates the input car_brand to a valid car_brand in the car_brands dictionary.
        If no exact match is found, attempts to find the closest match.
        """
        if not car_brand:
            return None
        car_brand = car_brand.replace("+", "plus").lower()
        car_brand = re.sub(r'[\s&()!-]+', '', car_brand) if car_brand else None 
        if car_brand in ["vw", "wv"]:
            car_brand = "volkswagen"
        if car_brand == "газ":
            car_brand = "gaz"
        if car_brand == "заз":
            car_brand = "zaz"
        car_brand_keys = self.car_brands.keys()
        
        # Handle exact matches and substring matches
        for key in car_brand_keys:
            if car_brand in key or key in car_brand:
                return key
        
        # Handle misspellings using closest match
        corrected_brand = difflib.get_close_matches(car_brand, car_brand_keys, n=1, cutoff=0.7)
        if corrected_brand:
            return corrected_brand[0]
        
        # Log an error if translation fails
        logger.error(f"error translating {car_brand}")
        return car_brand
    
    def translate_color(self, color):
        color_translations = {
            "beige": "beige",
            "blue": "blue",
            "brown": "brown",
            "bronze": "bronze",
            "yellow": "yellow",
            "grey": "grey",
            "gray": "grey",
            "green": "green",
            "red": "red",
            "black": "black",
            "silver": "silver",
            "pink": "pink",
            "white": "white",
            "orange": "orange",
            "gold": "gold",
            "golden": "gold",
            "purple": "purple",
            "violet": "purple",
            "matte": "matte",
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
            "balts": "white",
            "brūna": "brown",
            "brūns": "brown",
            "melna": "black",
            "melns": "black",
            "sudraba": "silver",
            "sudrabs": "silver",
            "zila": "blue",
            "zils": "blue",
            "gaišizils": "blue",
            "gaišizila": "blue",
            "tumšisarkans": "red",
            "tumšisarkana": "red",
            "sarkana": "red",
            "sarkans": "red",
            "zaļa": "green",
            "zaļš": "green",
            "pelēka": "grey",
            "pelēks": "grey",
            "violets": "purple",
            "violeta": "purple",
            "dzeltena": "yellow",
            "dzeltens": "yellow",
            "oranža": "orange",
            "oranžs": "orange",
            "zelta": "gold",
            "zelts": "gold",
            "other": None,
            "kita": None,
            "-": None,
            "": None
        }
        if not color:
            return None
        color = color.replace(" ", "").lower()
        if color in color_translations:
            color = color_translations[color]  # Translate to English
            return color
        else:
            logger.error(f"color '{color}' not found in color_translations")
            return None
    
    def translate_body_type(self, body_type):
        body_type_translations = {
            "compact": "hatchback",
            "small car": "hatchback",
            "small": "hatchback",
            "hatchback": "hatchback",
            "convertible": "convertible",
            "cabriolet": "convertible",
            "roadster": "convertible",
            "open": "convertible",
            "sports car": "coupe/sportscar",
            "sports": "coupe/sportscar",
            "coupe": "coupe/sportscar",
            "suv": "suv/off-road/jeep",
            "off-road": "suv/off-road/jeep",
            "jeep": "suv/off-road/jeep",
            "truck": "suv/off-road/jeep",
            "station wagon": "stationwagon/universal",
            "station wagon/van": "van/minivan",
            "station": "stationwagon/universal",
            "universal": "stationwagon/universal",
            "touring": "stationwagon/universal",
            "sedan": "sedan",
            "saloon": "sedan",
            "van": "van/minivan",
            "flatbed van": "van/minivan",
            "panel van": "van/minivan",
            "van-high roof": "van/minivan",
            "transporter": "van/minivan",
            "rigid": "van/minivan",
            "commercial vehicle": "van/minivan",
            "small commercial vehicle": "van/minivan",
            "minibus": "van/minivan",
            "minivan": "van/minivan",
            "miniven": "van/minivan",
            "pickup": "pickup",
            "off-road/pickup": "pickup",
            "off-road/pick-up": "pickup",
            "other": None,
            "others": None,
            "-": None,
            "apvidus": "suv/off-road/jeep",
            "hečbeks": "hatchback",
            "hecbeks": "hatchback",
            "kabriolets": "convertible",
            "kupeja": "coupe/sportscar",
            "mikroautobuss": "van/minivan",
            "minivens": "van/minivan",
            "krovininis mikroautobusas": "van/minivan",
            "keleivinis mikroautobusas": "van/minivan",
            "sedans": "sedan",
            "universālis": "stationwagon/universal",
            "universalis": "stationwagon/universal",
            "cits": None,
            "hečbekas": "hatchback",
            "sedanas": "sedan",
            "kupė": "coupe/sportscar",
            "kupe": "coupe/sportscar",
            "kabrioletas": "convertible",
            "universalas": "stationwagon/universal",
            "vienatūris": "hatchback",
            "vienaturis": "compact/smallcar",
            "visureigis": "suv/off-road/jeep",
            "krosoveris": "suv/off-road/jeep",
            "komercinis": "van/minivan",
            "limuzinas": "sedan",
            "pikapas": "pickup",
            "keleivinis": "van/minivan",
            "krovininis": "van/minivan",
            "kita": None
        }
        if not body_type:
            return None
        if body_type in body_type_translations:
            body_type = body_type_translations[body_type]
            return body_type
        else:
            logger.error(f"body_type '{body_type}' not found in body_type_translations")
            return None

    def translate_engine_type(self, engine_type):
        engine_type_translations = {
            "petrol": "gasoline",
            "gasoline": "gasoline",
            "gasoline/gas": "gasoline",
            "diesel": "diesel",
            "electric": "electric",
            "hybrid (diesel/electric)": "hybrid",
            "hybrid (petrol/electric)": "hybrid",
            "hybrid (electric/gasoline)": "hybrid",
            "hybrid (electric/diesel)": "hybrid",
            "electric/diesel": "hybrid",
            "hybrid": "hybrid",
            "plug-in hybrid": "hybrid",
            "plug-in": "hybrid",
            "cng": "naturalgas",
            "natural gas": "naturalgas",
            "gas": "naturalgas",
            "natural": "naturalgas",
            "lpg": "lpg",
            "ethanol": "ethanol",
            "hydrogen": "hydrogen",
            "others": None,
            "other": None,
            "dīzelis": "diesel",
            "benzīns": "gasoline",
            "benzīns/gāze": "gasoline",
            "benzīns/elektriskais": "hybrid",
            "dīzelis/elektriskais": "hybrid",
            "hibrīds": "hybrid",
            "elektriskais": "electric",
            "cits": None,
            "dyzelinas": "diesel",
            "benzinas": "gasoline",
            "benzinas / dujos": "gasoline",
            "benzinas / elektra": "hybrid",
            "benzinas + elektra": "hybrid",
            "elektra": "electric",
            "dyzelinas / elektra": "hybrid",
            "dyzelinas + elektra": "hybrid",
            "dyzelinas + dujos": "diesel",
            "benzinas + dujos": "gasoline",
            "bioetanolis (e85)": "ethanol",
            "benzinas / elektra / dujos": "hybrid",
            "vandenilis": "hydrogen",
            "kita": None
        }
        if not engine_type:
            return None
        if engine_type in engine_type_translations:
            engine_type = engine_type_translations[engine_type]
            return engine_type
        else:
            logger.error(f"engine_type '{engine_type}' not found in engine_type_translations")
            return None
    