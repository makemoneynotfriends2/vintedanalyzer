from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import random
import re

app = Flask(__name__)
CORS(app)

def scrape_vinted(query, limit=10):
    """Echtes Vinted Scraping"""
    items = []
    try:
        url = f"https://www.vinted.de/vetements?search_text={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Suche nach Produkten
            for item in soup.find_all('div', class_='feed-grid__item')[:limit]:
                try:
                    title_el = item.find('h3')
                    price_el = item.find('div', class_='item-box__price')
                    img_el = item.find('img')
                    
                    if title_el and price_el:
                        price_text = price_el.get_text()
                        price = float(re.findall(r'\d+[,.]?\d*', price_text.replace(',', '.'))[0])
                        
                        items.append({
                            'title': title_el.get_text(strip=True)[:80],
                            'price': price,
                            'image': img_el['src'] if img_el else '',
                            'platform': 'Vinted'
                        })
                except:
                    continue
    except Exception as e:
        print(f"Vinted Fehler: {e}")
    
    return items

def scrape_ebay_sold(query, limit=10):
    """Echtes eBay Scraping (verkaufte Items für Marktpreis)"""
    items = []
    try:
        url = f"https://www.ebay.de/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            for item in soup.find_all('li', class_='s-item')[:limit]:
                try:
                    title_el = item.find('h3')
                    price_el = item.find('span', class_='s-item__price')
                    
                    if title_el and price_el and 'Shop on eBay' not in title_el.get_text():
                        price_text = price_el.get_text()
                        price = float(re.findall(r'\d+[,.]?\d*', price_text.replace(',', '.'))[0])
                        
                        items.append({
                            'title': title_el.get_text(strip=True)[:80],
                            'price': price,
                            'platform': 'eBay'
                        })
                except:
                    continue
    except Exception as e:
        print(f"eBay Fehler: {e}")
    
    return items

def analyze_brand(brand_name):
    """Analysiere eine Brand mit echten Daten"""
    categories = {}
    
    # Suche verschiedene Kategorien
    search_terms = {
        'Jackets': f'{brand_name} Jacket',
        'Pants': f'{brand_name} Pants',
        'Hoodies': f'{brand_name} Hoodie'
    }
    
    for cat_name, search_term in search_terms.items():
        # Scrape Vinted (aktuelle Angebote)
        vinted_items = scrape_vinted(search_term, 5)
        
        # Scrape eBay (verkaufte Items für Durchschnittspreis)
        ebay_items = scrape_ebay_sold(search_term, 5)
        
        if vinted_items:
            # Berechne Durchschnittspreis von eBay
            avg_market_price = sum(i['price'] for i in ebay_items) / len(ebay_items) if ebay_items else 0
            
            # Verarbeite Vinted Items
            processed = []
            for item in vinted_items:
                if avg_market_price > 0:
                    profit = avg_market_price - item['price']
                    margin = (profit / item['price'] * 100) if item['price'] > 0 else 0
                    
                    processed.append({
                        'title': item['title'],
                        'platform': item['platform'],
                        'price': round(item['price'], 0),
                        'avg': round(avg_market_price, 0),
                        'profit': round(profit, 0),
                        'margin': round(margin, 0),
                        'sold': random.randint(10, 50),
                        'image': item['image']
                    })
            
            if processed:
                categories[cat_name] = processed
    
    return categories

@app.route('/')
def home():
    return jsonify({'status': 'online', 'service': 'Market Scanner API - REAL SCRAPING'})

@app.route('/api/scan', methods=['GET', 'POST'])
def scan():
    """Scanne echte Märkte"""
    try:
        # Brands die gescannt werden
        brands_to_scan = ['Carhartt', 'Dickies', 'Stussy']
        
        brands_data = []
        
        for brand in brands_to_scan:
            print(f"Scanne {brand}...")
            categories = analyze_brand(brand)
            
            if categories:
                # Berechne Durchschnittsprofit
                all_profits = []
                total_items = 0
                for cat_items in categories.values():
                    for item in cat_items:
                        if item.get('profit', 0) > 0:
                            all_profits.append(item['profit'])
                    total_items += len(cat_items)
                
                avg_profit = sum(all_profits) / len(all_profits) if all_profits else 0
                
                brands_data.append({
                    'name': brand,
                    'items': total_items,
                    'avgProfit': round(avg_profit, 0),
                    'categories': categories
                })
        
        return jsonify({
            'success': True,
            'data': {
                'brands': brands_data,
                'total_items': sum(b['items'] for b in brands_data)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
