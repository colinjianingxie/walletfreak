from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random

logger = logging.getLogger(__name__)

class HyattScraper:
    def scrape_url(self, url: str) -> List[Dict]:
        """
        Fetches the Hyatt URL and parses hotel options using Playwright with stealth measures.
        """
        try:
            logger.info(f"Fetching URL via Playwright: {url}")
            
            with sync_playwright() as p:
                # Launch browser (can be headless)
                browser = p.chromium.launch(headless=True)
                
                # Create context with stealth settings
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                # Apply stealth
                stealth = Stealth()
                stealth.apply_stealth_sync(page)
                
                # Navigate
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for hotel cards using a selector we know (data-js='hotel-card')
                # Add random sleep to be safe
                time.sleep(random.uniform(3, 6))
                
                try:
                    page.wait_for_selector("div[data-js='hotel-card']", timeout=40000)
                except Exception:
                    logger.warning("Timeout waiting for hotel cards selector. Dumping HTML for debug.")
                    with open("debug_scrape_error.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                
                html_content = page.content()
                browser.close()
                return self.parse_html(html_content)
                
        except Exception as e:
            logger.error(f"Error scraping Hyatt URL with Playwright: {e}")
            return []

    def parse_html(self, html_content: str) -> List[Dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        hotels = []
        
        # Find all hotel cards
        cards = soup.find_all('div', {'data-js': 'hotel-card'})
        
        for card in cards:
            try:
                hotel_data = {
                    'name': self._get_hotel_name(card),
                    'rating': card.get('data-hotel-rating'),
                    'rate': card.get('data-rate'),
                    'currency': card.get('data-currency-code'),
                    'brand': card.get('data-brand'),
                    'distance': card.get('data-distance-from-centerpoint'),
                    'booking_status': card.get('data-booking-status'),
                    'image_url': self._get_image_url(card),
                }
                
                # Format price/points
                if hotel_data['rate']:
                    try:
                        rate_val = float(hotel_data['rate'])
                        hotel_data['rate_display'] = f"{rate_val:,.0f}"
                    except:
                        hotel_data['rate_display'] = hotel_data['rate']
                else:
                    hotel_data['rate_display'] = 'N/A'

                hotel_data['price'] = hotel_data['rate_display']
                # Generate a simple ID based on name (safe enough for selection UI)
                hotel_data['id'] = str(hash(hotel_data['name']))

                hotels.append(hotel_data)
            except Exception as e:
                logger.warning(f"Error parsing a hotel card: {e}")
                continue
                
        return hotels

    def _get_hotel_name(self, card) -> str:
        img = card.find('img')
        if img and img.get('alt'):
            return img.get('alt')
        return "Unknown Hotel"

    def _get_image_url(self, card) -> Optional[str]:
        img = card.find('img')
        if img:
            if img.get('src'):
                return img.get('src')
            if img.get('data-src'):
                return img.get('data-src')
        return None
