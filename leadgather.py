#!/usr/bin/env python3
"""
BizBuySell Business Listings Scraper
Scrapes business listings from BizBuySell.com using Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import csv
from typing import List, Dict
import time


class BizBuySellScraper:
    def __init__(self, headless: bool = False):
        """
        Initialize the scraper with Selenium WebDriver
        
        Args:
            headless: Run browser in headless mode (default: False)
        """
        self.base_url = "https://www.bizbuysell.com"
        self.driver = None
        self.headless = headless
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure ChromeDriver is installed and in your PATH.")
            print("You can install it with: brew install chromedriver (macOS) or download from https://chromedriver.chromium.org/")
            raise
    
    def scrape_listings(self, url: str, wait_time: int = 5) -> List[Dict]:
        """
        Scrape business listings from the given URL
        
        Args:
            url: The URL to scrape
            wait_time: Time to wait for page to load (seconds)
            
        Returns:
            List of dictionaries containing business listing data
        """
        print(f"Scraping: {url}")
        
        try:
            self.driver.get(url)
            # Wait for page to load
            time.sleep(wait_time)
            
            # Wait for listings to appear (if they exist)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            listings = []
            
            # Try multiple possible selectors for listings
            # The actual structure may vary, so we'll try common patterns
            listing_selectors = [
                {'tag': 'div', 'class': 'listing-card'},
                {'tag': 'div', 'class': 'result'},
                {'tag': 'article', 'class': 'listing'},
                {'tag': 'div', 'class': 'business-listing'},
                {'tag': 'div', 'class': 'listing'},
            ]
            
            found_listings = []
            for selector in listing_selectors:
                found_listings = soup.find_all(selector['tag'], class_=selector['class'])
                if found_listings:
                    print(f"Found {len(found_listings)} listings using selector: {selector}")
                    break
            
            # If no listings found with class selectors, try finding any div with data attributes
            if not found_listings:
                found_listings = soup.find_all('div', {'data-listing-id': True})
                if found_listings:
                    print(f"Found {len(found_listings)} listings using data attributes")
            
            # If still no listings, try finding all article tags or divs with specific patterns
            if not found_listings:
                found_listings = soup.find_all('article')
                if not found_listings:
                    found_listings = soup.find_all('div', class_=lambda x: x and ('listing' in x.lower() or 'result' in x.lower()))
            
            print(f"Total elements found: {len(found_listings)}")
            
            # Extract data from each listing
            for idx, listing in enumerate(found_listings, 1):
                try:
                    listing_data = self._extract_listing_data(listing, idx)
                    if listing_data:
                        listings.append(listing_data)
                except Exception as e:
                    print(f"Error extracting listing {idx}: {e}")
                    continue
            
            # If no structured listings found, extract all text content as fallback
            if not listings:
                print("\nWarning: No structured listings found. Saving page content for inspection.")
                with open('page_content.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("Page HTML saved to 'page_content.html' for manual inspection.")
                
                # Try to extract any useful information from the page
                title = soup.find('title')
                if title:
                    print(f"Page title: {title.get_text(strip=True)}")
            
            return listings
            
        except Exception as e:
            print(f"Error scraping URL: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def __del__(self):
        """Clean up: close the browser"""
        if self.driver:
            self.driver.quit()
    
    def _extract_listing_data(self, listing_element, index: int) -> Dict:
        """
        Extract data from a single listing element
        
        Args:
            listing_element: BeautifulSoup element containing listing data
            index: Listing index number
            
        Returns:
            Dictionary with listing data
        """
        data = {
            'index': index,
            'title': '',
            'price': '',
            'location': '',
            'description': '',
            'link': '',
            'revenue': '',
            'cash_flow': '',
        }
        
        # Extract title
        title_selectors = ['h2', 'h3', 'h4', '.title', '.listing-title', 'a.title']
        for selector in title_selectors:
            title_elem = listing_element.select_one(selector)
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                # Get link if title is a link
                if title_elem.name == 'a' or title_elem.find('a'):
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    href = link_elem.get('href', '')
                    if href:
                        data['link'] = href if href.startswith('http') else self.base_url + href
                break
        
        # Extract price
        price_selectors = ['.price', '.listing-price', '.asking-price', '[class*="price"]']
        for selector in price_selectors:
            price_elem = listing_element.select_one(selector)
            if price_elem:
                data['price'] = price_elem.get_text(strip=True)
                break
        
        # Extract location
        location_selectors = ['.location', '.listing-location', '.address', '[class*="location"]']
        for selector in location_selectors:
            location_elem = listing_element.select_one(selector)
            if location_elem:
                data['location'] = location_elem.get_text(strip=True)
                break
        
        # Extract description
        desc_selectors = ['.description', '.listing-description', '.summary', 'p']
        for selector in desc_selectors:
            desc_elem = listing_element.select_one(selector)
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
                break
        
        # Extract revenue and cash flow if available
        text_content = listing_element.get_text().lower()
        if 'revenue' in text_content or 'sales' in text_content:
            revenue_elem = listing_element.find(string=lambda text: text and ('revenue' in text.lower() or 'sales' in text.lower()))
            if revenue_elem:
                data['revenue'] = revenue_elem.strip()
        
        if 'cash flow' in text_content:
            cashflow_elem = listing_element.find(string=lambda text: text and 'cash flow' in text.lower())
            if cashflow_elem:
                data['cash_flow'] = cashflow_elem.strip()
        
        return data
    
    def save_to_json(self, listings: List[Dict], filename: str = 'listings.json'):
        """Save listings to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(listings)} listings to {filename}")
    
    def save_to_csv(self, listings: List[Dict], filename: str = 'listings.csv'):
        """Save listings to CSV file"""
        if not listings:
            print("No listings to save.")
            return
        
        fieldnames = listings[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(listings)
        print(f"\nSaved {len(listings)} listings to {filename}")
    
    def print_listings(self, listings: List[Dict]):
        """Print listings to console"""
        if not listings:
            print("\nNo listings found.")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(listings)} listings:")
        print(f"{'='*80}\n")
        
        for listing in listings:
            print(f"Listing #{listing['index']}")
            print(f"  Title: {listing['title']}")
            print(f"  Price: {listing['price']}")
            print(f"  Location: {listing['location']}")
            if listing['revenue']:
                print(f"  Revenue: {listing['revenue']}")
            if listing['cash_flow']:
                print(f"  Cash Flow: {listing['cash_flow']}")
            if listing['link']:
                print(f"  Link: {listing['link']}")
            if listing['description']:
                desc = listing['description'][:100] + '...' if len(listing['description']) > 100 else listing['description']
                print(f"  Description: {desc}")
            print('-' * 80)


def main():
    url = "https://www.bizbuysell.com/businesses-for-sale/?q=bHQ9MzAsNDAsODA%3D"
    
    scraper = None
    try:
        scraper = BizBuySellScraper(headless=False)  # Set to True to run without opening browser window
        listings = scraper.scrape_listings(url, wait_time=5)
        
        if listings:
            scraper.print_listings(listings)
            scraper.save_to_json(listings)
            scraper.save_to_csv(listings)
        else:
            print("\nNo listings were extracted.")
            print("The page HTML has been saved to 'page_content.html' for inspection.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if scraper and scraper.driver:
            scraper.driver.quit()


if __name__ == "__main__":
    main()
