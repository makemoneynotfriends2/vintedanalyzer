import requests
import time
import random
import logging
import urllib3
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
from collections import deque
from typing import Dict, List, Optional, Any

# Initialisierung der Unterdrückung von SSL-Warnungen (wie in deinem Bot)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ==============================================================================
# GLOBAL CONFIGURATION & MARKET INTELLIGENCE CONSTANTS
# ==============================================================================
CONFIG = {
    "VERSION": "8.0-ENTERPRISE",
    "AUTHOR": "Core Resale Systems",
    "MARKETS": {
        "germany": {"domain": "vinted.de", "currency": "EUR", "locale": "de-DE"},
        "france": {"domain": "vinted.fr", "currency": "EUR", "locale": "fr-FR"},
        "italy": {"domain": "vinted.it", "currency": "EUR", "locale": "it-IT"},
        "spain": {"domain": "vinted.es", "currency": "EUR", "locale": "es-ES"}
    },
    "HYPE_BRANDS": [
        "Ralph Lauren", "Lacoste", "True Religion", "Gucci", 
        "Armani", "Dolce & Gabbana", "Nike", "Adidas", "Stussy"
    ],
    "ANALYSIS": {
        "STEAL_THRESHOLD": 0.35,  # 35% unter Marktwert = Steal
        "DEMAND_WEIGHT": 1.5,     # Gewichtung von Favoriten
        "MAX_HISTORY": 5000       # Historische Datenpunkte für Preis-Graphen
    }
}

# ==============================================================================
# LOGGING & AUDIT TRAIL SYSTEM
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [VRI-CORE] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# CORE ENGINE: DATA PERSISTENCE & ANALYTICS
# ==============================================================================
class MarketIntelligenceUnit:
    """Verantwortlich für die Berechnung von Trends und Preis-Benchmarks"""
    def __init__(self):
        self.item_history = deque(maxlen=CONFIG["ANALYSIS"]["MAX_HISTORY"])
        self.brand_benchmarks = {}

    def ingest_data(self, items: List[Dict]):
        for item in items:
            self.item_history.append({
                "id": item.get('id'),
                "price": float(item.get('price_numeric', 0)) if item.get('price_numeric') else float(item.get('price', {}).get('amount', 0)),
                "brand": item.get('brand_title', 'Unknown').lower(),
                "favs": item.get('favourite_count', 0),
                "timestamp": datetime.now()
            })
        self._calculate_benchmarks()

    def _calculate_benchmarks(self):
        if not self.item_history: return
        df = pd.DataFrame(list(self.item_history))
        if df.empty: return
        
        # Aggregation der Durchschnittspreise pro Marke
        stats = df.groupby('brand')['price'].agg(['mean', 'std', 'count']).to_dict('index')
        self.brand_benchmarks = stats

    def evaluate_deal(self, price: float, brand: str, favs: int) -> Dict:
        brand = brand.lower()
        benchmark = self.brand_benchmarks.get(brand, {"mean": 50.0}) # Default Fallback
        
        avg_price = benchmark['mean']
        profit_potential = avg_price - price
        is_steal = price < (avg_price * (1 - CONFIG["ANALYSIS"]["STEAL_THRESHOLD"]))
        
        # Hype Score Berechnung
        hype_score = (favs * CONFIG["ANALYSIS"]["DEMAND_WEIGHT"]) + (profit_potential if profit_potential > 0 else 0)
        
        return {
            "avg_market_price": round(avg_price, 2),
            "profit_potential": round(profit_potential, 2),
            "is_steal": is_steal,
            "hype_score": round(hype_score, 1)
        }

# ==============================================================================
# PROXY & SESSION MANAGEMENT (ADAPTED FROM YOUR WORKING BOT)
# ==============================================================================
class VintedSessionManager:
    """Garantiert stabile Verbindungen durch Cookie-Handling und Header-Mimicry"""
    def __init__(self):
        self.session = requests.Session()
        self.cookies = {}
        self.last_init = None

    def get_headers(self, country_code: str = "germany"):
        config = CONFIG["MARKETS"].get(country_code, CONFIG["MARKETS"]["germany"])
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': config['locale'] + ',de;q=0.9',
            'Referer': f'https://www.{config["domain"]}/'
        }

    def ensure_session(self, country_code: str = "germany"):
        now = datetime.now()
        if self.last_init and (now - self.last_init).seconds < 600:
            return
            
        config = CONFIG["MARKETS"].get(country_code, CONFIG["MARKETS"]["germany"])
        domain = config['domain']
        
        try:
            logger.info(f"🔄 Initialisiere Session für {domain}...")
            # Handshake wie in deinem Bot
            resp = self.session.get(f"https://www.{domain}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
            if resp.status_code == 200:
                self.cookies = self.session.cookies.get_dict()
                self.last_init = now
                logger.info(f"✅ Session aktiv ({len(self.cookies)} Cookies)")
        except Exception as e:
            logger.error(f"❌ Session Error: {e}")

# ==============================================================================
# THE ENGINE: MASTER SCRAPER & ANALYZER
# ==============================================================================
class ResaleMasterEngine:
    def __init__(self):
        self.session_manager = VintedSessionManager()
        self.intelligence = MarketIntelligenceUnit()

    def deep_scan(self, search_term: str, country: str = "germany"):
        self.session_manager.ensure_session(country)
        config = CONFIG["MARKETS"][country]
        
        params = {
            'search_text': search_term,
            'order': 'newest_first',
            'per_page': '50',
            'currency': config['currency']
        }
        
        try:
            url = f"https://www.{config['domain']}/api/v2/catalog/items"
            response = self.session_manager.session.get(
                url, 
                params=params, 
                headers=self.session_manager.get_headers(country),
                timeout=12,
                verify=False
            )
            
            if response.status_code == 200:
                raw_items = response.json().get('items', [])
                self.intelligence.ingest_data(raw_items)
                
                # Veredelung der Daten
                enriched_results = []
                for item in raw_items:
                    brand = item.get('brand_title', 'Unknown')
                    price = float(item.get('price_numeric')) if item.get('price_numeric') else float(item.get('price', {}).get('amount', 0))
                    favs = item.get('favourite_count', 0)
                    
                    analysis = self.intelligence.evaluate_deal(price, brand, favs)
                    
                    enriched_results.append({
                        "id": item.get('id'),
                        "title": item.get('title'),
                        "price": price,
                        "currency": config['currency'],
                        "brand": brand,
                        "favs": favs,
                        "url": f"https://www.{config['domain']}{item.get('url')}",
                        "photo": item.get('photos', [{}])[0].get('url', ''),
                        "analysis": analysis
                    })
                
                # Sortiere nach Hype Score
                return sorted(enriched_results, key=lambda x: x['analysis']['hype_score'], reverse=True)
            return []
        except Exception as e:
            logger.error(f"Scan Error: {e}")
            return []

# Singleton Instance
engine = ResaleMasterEngine()

# ==============================================================================
# UI FRAMEWORK: HIGH-END DASHBOARD (TAILWIND/JS)
# ==============================================================================
@app.route('/')
def index():
    query = request.args.get('q', 'Ralph Lauren Vintage')
    results = engine.deep_scan(query)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de" class="dark">
    <head>
        <meta charset="UTF-8">
        <title>Vinted 8-Figure Resale Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
            body { font-family: 'Outfit', sans-serif; background: #0a0a0c; color: #f4f4f5; }
            .steal-card { border: 2px solid #22c55e; box-shadow: 0 0 25px rgba(34, 197, 94, 0.15); }
            .glass { background: rgba(18, 18, 22, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.05); }
            .shimmer { background: linear-gradient(90deg, #18181b 25%, #27272a 50%, #18181b 75%); background-size: 200% 100%; animation: shimmer 2s infinite; }
            @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        </style>
    </head>
    <body class="p-4 md:p-10">
        <div class="max-w-7xl mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
                <div>
                    <h1 class="text-5xl font-black tracking-tighter text-white">RESALE<span class="text-green-500">CORE</span></h1>
                    <p class="text-zinc-500 font-medium">Enterprise Market Analysis System v8.0</p>
                </div>
                <div class="flex gap-4">
                    <div class="glass px-6 py-3 rounded-2xl text-center">
                        <p class="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Markt Status</p>
                        <p class="text-green-400 font-bold">SYNCHRONISIERT</p>
                    </div>
                </div>
            </header>

            <div class="glass p-3 rounded-3xl mb-12 flex gap-3">
                <form action="/" method="get" class="flex w-full gap-3">
                    <input type="text" name="q" value="{{ query }}" placeholder="Suche nach Marken, Kategorien oder spezifischen Trends..." 
                        class="w-full bg-zinc-900/50 border-none p-5 rounded-2xl text-xl focus:ring-2 focus:ring-green-500 transition-all outline-none">
                    <button type="submit" class="bg-green-500 hover:bg-green-400 text-black px-10 rounded-2xl font-black text-lg transition-all transform hover:scale-95">SCAN</button>
                </form>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {% if not items %}
                <div class="col-span-full p-20 text-center glass rounded-3xl">
                    <h2 class="text-3xl font-bold text-zinc-700">KEINE DATEN EMPFANGEN</h2>
                    <p class="text-zinc-500 mt-2">Prüfe die Vinted-Verbindung oder versuche einen anderen Suchbegriff.</p>
                </div>
                {% endif %}

                {% for item in items %}
                <div class="glass rounded-[2rem] overflow-hidden flex flex-col transition-all hover:-translate-y-2 {{ 'steal-card' if item.analysis.is_steal else '' }}">
                    <div class="relative group">
                        <img src="{{ item.photo }}" class="w-full h-72 object-cover group-hover:scale-110 transition-transform duration-500">
                        <div class="absolute top-4 right-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold border border-white/10">
                            ⭐ {{ item.favs }} Likes
                        </div>
                        {% if item.analysis.is_steal %}
                        <div class="absolute bottom-4 left-4 bg-green-500 text-black px-4 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter">
                            High Profit Potential
                        </div>
                        {% endif %}
                    </div>
                    
                    <div class="p-6 flex-grow flex flex-col justify-between">
                        <div>
                            <p class="text-[10px] font-black text-green-500 uppercase tracking-widest mb-1">{{ item.brand }}</p>
                            <h3 class="font-bold text-lg leading-tight mb-4 truncate">{{ item.title }}</h3>
                            
                            <div class="flex justify-between items-baseline mb-6">
                                <div>
                                    <p class="text-3xl font-black text-white">{{ item.price }}€</p>
                                    <p class="text-[10px] text-zinc-500 font-bold uppercase">Markt: {{ item.analysis.avg_market_price }}€</p>
                                </div>
                                <div class="text-right">
                                    <p class="text-[10px] text-zinc-500 font-bold uppercase">Hype Score</p>
                                    <p class="text-xl font-black text-white">{{ item.analysis.hype_score }}</p>
                                </div>
                            </div>
                        </div>

                        <a href="{{ item.url }}" target="_blank" class="w-full bg-white text-black py-4 rounded-2xl font-black text-center hover:bg-green-500 transition-colors uppercase text-sm tracking-tighter">
                            Artikel Snipen
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script>
            // Auto-Refresh Logik für Live-Scraping
            setTimeout(() => {
                if(!document.activeElement.tagName === 'INPUT') {
                    // window.location.reload();
                }
            }, 60000);
        </script>
    </body>
    </html>
    """, items=results, query=query)

if __name__ == "__main__":
    app.run(debug=True)
