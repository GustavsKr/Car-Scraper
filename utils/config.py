from dotenv import load_dotenv
import os

load_dotenv()

DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING') 
LOGGER_TOKEN = os.getenv('LOGGER_TOKEN')
# Stores all the newest links from various websites. Whenever a listing gets scraped then it gets removed from ss_links
ss_links = []