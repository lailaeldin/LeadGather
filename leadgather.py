#!/usr/bin/env python3
"""
BizBuySell Business Listings Scraper
Scrapes business listings from BizBuySell.com
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from typing import List, Dict
import sys


class BizBuySellScraper:
    def __init__(self):
        self.base_url = "https://www.bizbuysell.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_listings(self, url: str) -> List[Dict]:
        """
        Scrape business listings from the given URL
        
        Args:
            url: The URL to scrape
            
        Returns:
            List of dictionaries containing business listing data
        """
        print(f"Scraping: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
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
                    f.write(response.text)
                print("Page HTML saved to 'page_content.html' for manual inspection.")
                
                # Try to extract any useful information from the page
                title = soup.find('title')
                if title:
                    print(f"Page title: {title.get_text(strip=True)}")
            
            return listings
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return []
        except Exception as e:
            print(f"Error parsing page: {e}")
            return []
    
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
    
    scraper = BizBuySellScraper()
    listings = scraper.scrape_listings(url)
    
    if listings:
        scraper.print_listings(listings)
        scraper.save_to_json(listings)
        scraper.save_to_csv(listings)
    else:
        print("\nNo listings were extracted. The page might use JavaScript to load content.")
        print("You may need to use Selenium or Playwright for dynamic content.")
        print("The page HTML has been saved to 'page_content.html' for inspection.")


if __name__ == "__main__":
    main()
