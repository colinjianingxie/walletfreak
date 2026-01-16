import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
import re
import time
import random

# KML URL
KML_URL = "https://www.google.com/maps/d/kml?mid=1HygPCP9ghtDptTNnpUpd_C507Mq_Fhec&forcekml=1"

def fetch_kml():
    try:
        response = requests.get(KML_URL, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch KML: {response.status_code}")
            return None
        return response.content
    except Exception as e:
        print(f"Error fetching KML: {e}")
        return None

def parse_description_content(desc_html):
    """
    Parses the KML description (HTML/text).
    Returns a dictionary with extracted fields and the cleaned description.
    """
    if not desc_html:
        return {
            "description": "",
            "price_calendar_link": "",
            "hotelft_link": "",
            "images": [],
            "stars": "Not available",
            "address": "Not available"
        }

    # Soup for extracting images and robust text parsing if needed
    soup = BeautifulSoup(desc_html, 'html.parser')
    
    # Extract images
    images = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]
    
    # Address (fallback usually in text)
    # In the specific KML shown, address isn't clearly labelled but usually the first line or so.
    # However, the user example showed "Program: FHR..." as the text. 
    # Let's rely on the text lines for key-value extraction.
    
    # Replace <br> with newlines to process line by line
    text_content = desc_html.replace('<br>', '\n').replace('<br/>', '\n')
    # Use BS4 to strip other tags but keep the newlines we just made
    clean_text = BeautifulSoup(text_content, 'html.parser').get_text()
    
    lines = clean_text.split('\n')
    
    final_desc_lines = []
    price_calendar_link = ""
    hotelft_link = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("Price_Calendar:"):
            price_calendar_link = line.replace("Price_Calendar:", "").strip()
        elif line.startswith("hotelft_link:"):
            hotelft_link = line.replace("hotelft_link:", "").strip()
        elif line.startswith("location:"):
            # Skip valid JSON list location in description as we have KML coords
            continue
        elif line.startswith("Amex_Reservation:"):
            # Keep this in description or extract? User didn't ask to extract/remove this one specifically,
            # but usually "Pricing Calendar" and "hotelft" were the requested ones.
            # I'll keep it in description as requested "separate field ... (and remove from description)" applied to the other two.
            final_desc_lines.append(line)
        else:
            final_desc_lines.append(line)
            
    final_description = "\n".join(final_desc_lines)
    
    # Try to find address if possible, otherwise it defaults to "Not available" from previous logic
    # The previous logic for address was: soup.find('p').text... 
    # If the KML description is just key-values, maybe there isn't a standalone address line?
    # In the provided JSON example, the "address" field was effectively the same as "description".
    # I will stick to returning the full description as address fallback if needed, or just "Not available" if not distinct.
    # However, to be safe, I'll pass "Not available" and let the external check handle it if needed.
    address = "Not available" 

    # Stars
    stars_match = re.search(r'(\d+(\.\d+)?)\s*(?:star|stars)', clean_text, re.IGNORECASE)
    stars = stars_match.group(1) if stars_match else "Not available"

    return {
        "description": final_description,
        "price_calendar_link": price_calendar_link,
        "hotelft_link": hotelft_link,
        "images": images,
        "stars": stars,
        "address": address
    }

def get_external_star_rating(hotel_name, address):
    # Reduced timeout and added error handling
    try:
        location = address if address != "Not available" else ""
        query = f"{hotel_name} {location} site:tripadvisor.com"
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200: return "Not found"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find('a', href=re.compile(r'https://www\.tripadvisor\.com/Hotel_Review.*'))
        if not link: return "Not found"
        
        ta_url = link['href']
        ta_response = requests.get(ta_url, headers=headers, timeout=10)
        if ta_response.status_code != 200: return "Not found"

        ta_soup = BeautifulSoup(ta_response.text, 'html.parser')
        bubble_span = ta_soup.find('span', class_=re.compile(r'ui_bubble_rating bubble_\d+'))
        if bubble_span:
            return str(int(bubble_span['class'][1].replace('bubble_', '')) / 10)
            
        rating_match = re.search(r'(\d\.\d) of 5 bubbles', ta_response.text)
        return rating_match.group(1) if rating_match else "Not found"
    except:
        return "Not found"

def get_image_urls(hotel_name, address, num=3):
    try:
        location = address if address != "Not available" else ""
        query = f"{hotel_name} {location}"
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&tbm=isch"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code != 200: return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and src.startswith('http'):
                images.append(src)
            if len(images) >= num: break
        return images
    except:
        return []

def scrape_map_data():
    kml_content = fetch_kml()
    if not kml_content: return []
    
    root = ET.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    hotels = []
    
    folders = root.findall('.//kml:Folder', ns)
    for folder in folders:
        folder_name_tag = folder.find('kml:name', ns)
        folder_name = folder_name_tag.text.strip() if folder_name_tag is not None else ""
        
        if "Fine Hotels" in folder_name:
            program_type = "Fine Hotels + Resorts"
            min_nights = 1
        elif "Hotel Collection" in folder_name:
            program_type = "The Hotel Collection"
            min_nights = 2
        else:
            continue
            
        placemarks = folder.findall('kml:Placemark', ns)
        for pm in placemarks:
            name_tag = pm.find('kml:name', ns)
            name = name_tag.text.strip() if name_tag is not None else "Unnamed"
            
            desc_tag = pm.find('kml:description', ns)
            desc_content = desc_tag.text if desc_tag is not None else ""
            
            coord_tag = pm.find('kml:Point/kml:coordinates', ns)
            coords = coord_tag.text.strip() if coord_tag is not None else ""
            
            lat = None
            lon = None
            if coords:
                # KML coords are usually lon,lat,alt
                try:
                    parts = coords.split(',')
                    if len(parts) >= 2:
                        lon = float(parts[0])
                        lat = float(parts[1])
                except ValueError:
                    pass
            
            parsed = parse_description_content(desc_content)
            
            stars = parsed["stars"]
            if stars == "Not available":
                # Only try fetching if really needed and be gentle
                stars = get_external_star_rating(name, parsed["address"])
                time.sleep(random.uniform(1, 2)) 
            
            img_urls = parsed["images"]
            if not img_urls:
                img_urls = get_image_urls(name, parsed["address"])
                time.sleep(random.uniform(1, 2))
                
            hotel_data = {
                "name": name,
                "program_type": program_type,
                "min_nights": min_nights,
                "lat": lat,
                "lon": lon,
                "address": parsed["address"], # Often effectively same as description in this KML
                "image_urls": img_urls,
                "stars": stars,
                "description": parsed["description"],
                "price_calendar_link": parsed["price_calendar_link"],
                "hotelft_link": parsed["hotelft_link"]
            }
            
            hotels.append(hotel_data)
            print(f"Processed {name}")

    return hotels

def main():
    hotels = scrape_map_data()
    print(f"Extracted {len(hotels)} hotels.")
    
    with open('map_hotels_data.json', 'w') as f:
        json.dump(hotels, f, indent=4)
    print("Data saved to map_hotels_data.json")

if __name__ == "__main__":
    main()
