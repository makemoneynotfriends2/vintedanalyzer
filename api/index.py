import requests
import time
import random
import logging
import urllib3
import json
import re
import pandas as pd
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# PHASE 1: CORE ENGINE SETUP (FROM YOUR WORKING BOT)
# ==============================================================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

# Enterprise Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [V-CORE-V12] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VintedBusinessEngine:
    """Der Kern deines 8-Figure Tools - Nutzt deine funktionierende Scrape-Logik"""
    def __init__(self):
        self.session = requests.Session()
        self.seen_items = deque(maxlen=5000)
        self.market_benchmarks = {}
        self.vinted_configs = {
            'germany': {'domain': 'vinted.de', 'currency': 'EUR', 'locale': 'de-DE'},
            'france': {'domain': 'vinted.fr', 'currency': 'EUR', 'locale': 'fr-FR'},
            'italy': {'domain': 'vinted.it', 'currency': 'EUR', 'locale': 'it-IT'}
        }

    def get_simple_headers(self, locale='de-DE'):
        """Headers aus deinem Bot übernommen"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': f'{locale},de;q=0.9',
        }

    def sync_session(self, domain):
        """Die kritische Cookie-Logik aus deinem Bot"""
        try:
            url = f"https://www.{domain}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = self.session.get(url, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                logger.info(f"✅ Connection to {domain} established.")
                return True
            return False
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return False

    def calculate_hype_score(self, item, avg_price):
        """8-Figure Reseller Analytik"""
        price = float(item.get('price_numeric') or item.get('price', {}).get('amount', 0))
        favs = int(item.get('favourite_count', 0))
        
        # Arbitrage Berechnung
        profit = avg_price - price
        steal_indicator = 1 if price < (avg_price * 0.65) else 0
        
        # Hype Score Algorithmus v12
        score = (favs * 2.5) + (profit * 0.8) + (steal_indicator * 50)
        return round(score, 1), round(profit, 2)

    def scrape_market(self, country, query):
        """Die Haupt-Scrape-Funktion"""
        config = self.vinted_configs.get(country)
        if not config: return []
        
        self.sync_session(config['domain'])
        
        api_url = f"https://www.{config['domain']}/api/v2/catalog/items"
        params = {
            'search_text': query,
            'order': 'newest_first',
            'per_page': '40',
            'currency': config['currency']
        }
        
        try:
            resp = self.session.get(api_url, params=params, headers=self.get_simple_headers(config['locale']), timeout=12, verify=False)
            if resp.status_code == 200:
                items = resp.json().get('items', [])
                
                # Benchmarking
                prices = [float(i.get('price_numeric') or i.get('price', {}).get('amount', 0)) for i in items if i.get('price_numeric') or i.get('price')]
                avg = sum(prices) / len(prices) if prices else 50
                
                processed = []
                for i in items:
                    score, profit = self.calculate_hype_score(i, avg)
                    
                    # URL RESOLVER FIX (Kein vinted.dehttps mehr)
                    raw_path = i.get('url', '')
                    # Wir stellen sicher, dass wir nur den Pfad nehmen und die Domain sauber davor setzen
                    clean_path = re.sub(r'https?://[^/]+', '', raw_path)
                    final_url = f"https://www.{config['domain']}{clean_path}"
                    
                    processed.append({
                        "id": i.get('id'),
                        "title": i.get('title'),
                        "brand": i.get('brand_title', 'Unknown'),
                        "price": i.get('price_numeric') or i.get('price', {}).get('amount'),
                        "favs": i.get('favourite_count', 0),
                        "url": final_url,
                        "photo": i.get('photos', [{}])[0].get('url', '') if i.get('photos') else '',
                        "market": country.upper(),
                        "score": score,
                        "profit": profit,
                        "avg": round(avg, 2),
                        "is_steal": score > 70
                    })
                return processed
            return []
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            return []

# Singleton instance
engine = VintedBusinessEngine()

# ==============================================================================
# PHASE 2: DASHBOARD CONTROLLER (SUCHEN FUNKTIONIERT JETZT)
# ==============================================================================
@app.route('/')
def index():
    # Wir nehmen den Suchbegriff aus dem 'q' Parameter der URL
    query = request.args.get('q', 'Ralph Lauren Vintage')
    
    # Paralleles Scanning für maximale Speed
    all_results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(engine.scrape_market, country, query) for country in ['germany', 'france', 'italy']]
        for future in futures:
            all_results.extend(future.result())

    # Sortiere die besten Deals nach Hype-Score ganz nach oben
    sorted_items = sorted(all_results, key=lambda x: x['score'], reverse=True)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Sovereign Ultimate | v12 Enterprise</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&display=swap');
            body { font-family: 'Space Grotesk', sans-serif; background: #050505; color: #fff; }
            .glass { background: rgba(15, 15, 15, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); }
            .steal-card { border: 2px solid #00ff41; box-shadow: 0 0 30px rgba(0, 255, 65, 0.2); }
            .hype-grad { background: linear-gradient(90deg, #00ff41, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        </style>
    </head>
    <body class="p-4 lg:p-12">
        <div class="max-w-[1700px] mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-end mb-16 gap-10">
                <div>
                    <h1 class="text-7xl font-black tracking-tighter italic">SOVEREIGN<span class="text-[#00ff41]">.ULTIMATE</span></h1>
                    <p class="text-zinc-600 font-bold tracking-[0.4em] uppercase text-xs mt-3">Advanced Global Arbitrage Infrastructure</p>
                </div>
                <div class="glass px-10 py-6 rounded-[2.5rem] border-l-4 border-l-[#00ff41]">
                    <p class="text-zinc-500 text-[10px] font-black uppercase mb-1">Engine Status</p>
                    <p class="text-white font-mono text-2xl tracking-widest">MULTI-MARKET ACTIVE</p>
                </div>
            </header>

            <div class="mb-20 glass p-3 rounded-[3rem]">
                <form action="/" method="get" class="flex gap-4">
                    <input type="text" name="q" value="{{ query }}" placeholder="Deep Search Market Analysis..." 
                        class="w-full bg-transparent p-6 rounded-[2.5rem] text-2xl outline-none focus:ring-0 transition-all border-none">
                    <button type="submit" class="bg-[#00ff41] text-black px-16 rounded-[2.5rem] font-black text-xl hover:scale-95 transition-transform uppercase">Scan Market</button>
                </form>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-12">
                {% for item in items %}
                <div class="glass rounded-[3.5rem] overflow-hidden flex flex-col transition-all hover:-translate-y-4 {{ 'steal-card' if item.is_steal else '' }}">
                    <div class="relative h-96 group">
                        <img src="{{ item.photo }}" class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110">
                        <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-transparent opacity-90"></div>
                        <div class="absolute top-8 left-8 flex flex-col gap-3">
                            <span class="bg-black/60 px-4 py-1 rounded-full text-[10px] font-bold text-zinc-400">{{ item.market }}</span>
                            {% if item.is_steal %}
                            <span class="bg-[#00ff41] text-black px-4 py-1 rounded-full text-[10px] font-black uppercase">Steal Opportunity</span>
                            {% endif %}
                        </div>
                        <div class="absolute bottom-8 right-8 text-right">
                            <p class="text-[10px] font-black text-zinc-500 uppercase">Hype Score</p>
                            <p class="text-3xl font-black hype-grad">{{ item.score }}</p>
                        </div>
                    </div>
                    
                    <div class="p-10 flex-grow">
                        <div class="mb-8">
                            <p class="text-[#00ff41] text-[10px] font-black uppercase tracking-widest mb-1">{{ item.brand }}</p>
                            <h3 class="text-2xl font-bold leading-tight h-16 line-clamp-2 tracking-tight">{{ item.title }}</h3>
                        </div>

                        <div class="flex justify-between items-end mb-10">
                            <div>
                                <p class="text-5xl font-black text-white italic tracking-tighter">{{ item.price }}€</p>
                                <p class="text-zinc-600 text-[10px] font-bold mt-2 uppercase">Mkt Benchmark: {{ item.avg }}€</p>
                            </div>
                            <div class="text-right">
                                <p class="text-[#00ff41] font-black text-2xl tracking-tighter">+{{ item.profit }}€</p>
                                <p class="text-zinc-600 text-[10px] font-bold uppercase mt-1">Est. Profit</p>
                            </div>
                        </div>

                        <a href="{{ item.url }}" target="_blank" 
                           class="block w-full bg-white text-black py-6 rounded-[2rem] text-center font-black hover:bg-[#00ff41] transition-all uppercase tracking-tighter text-sm">
                            Access Listing
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, items=sorted_items, query=query)

if __name__ == "__main__":
    app.run(debug=True)
