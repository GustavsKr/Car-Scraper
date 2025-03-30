# 🚗 Baltic Car Marketplace Scraper

A real-time car scraper that monitors and collects listings from major Baltic marketplaces:

- 🇱🇻 [ss.com](https://ss.com)  
- 🇱🇹 [autoplius.lt](https://autoplius.lt)  
- 🇪🇪 [auto24.ee](https://auto24.ee)

The app scrapes the **newest listings every second**, processes their data, and stores everything into a **MySQL database**

---

## 🛠️ Technologies Used

- **Python**
- **MySQL + SQLAlchemy**
- **Playwright (async)**
- **BeautifulSoup + Requests**

---

## 🗃️ Database Overview

Data is stored in **three separate tables** based on source:

- `ss_cars`
- `autoplius_cars`
- `auto24_cars`

### 📋 Columns (shared across all tables)

| Column         | Type             | Description                           |
|----------------|------------------|---------------------------------------|
| `id`           | Integer (PK)     | Auto-incrementing ID                  |
| `url`          | String           | Full link to the listing              |
| `img_url`      | String           | URL to the main image                 |
| `brand`        | String           | Car brand (e.g., BMW, Toyota)         |
| `model`        | String           | Car model                             |
| `price`        | Decimal          | Price in EUR                          |
| `year`         | Integer          | Year of manufacture                   |
| `volume`       | Decimal          | Engine volume in liters               |
| `engine_type`  | Enum             | gasoline, diesel, electric, hybrid... |
| `gearbox`      | Enum             | manual or automatic                   |
| `body_type`    | Enum             | sedan, suv, convertible, etc.         |
| `color`        | Enum             | black, white, blue, silver, etc.      |
| `area`         | String           | Listing location                      |
| `deal_type`    | String           | Sale type                             |
| `run`          | Integer          | Mileage in kilometers                 |
| `checkup`      | String (MM.YYYY) | Technical inspection date             |
| `fetching_date`| Timestamp        | Time the listing was scraped          |

---

## 🔔 Use Cases

- 📬 Notify yourself when certain listings appear (via Gmail, Telegram, etc.)
- 📊 Analyze car prices, trends, or availability
