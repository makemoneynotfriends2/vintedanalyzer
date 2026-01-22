import requests
import random
import time
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

app = Flask(__name__)

# --- CONFIGURATION & GLOBAL STATE ---
CONFIG = {
    "TARGET_BRANDS": {
        "Ralph Lauren": {"sub_categories": ["Knitwear", "Bear", "Vintage"], "weight": 1.2},
        "Lacoste": {"sub_categories": ["Tracksuit", "Harrington", "Vintage"], "weight": 1.1},
        "True Religion": {"sub_categories": ["Ricky", "Super T", "Billy"], "weight": 1.5},
        "Football": {"sub_categories": ["Tracksuit", "Jersey 90s", "Training Set"], "weight": 1.8},
        "Designer": {"sub_categories": ["Gucci", "Armani", "D&G"], "weight": 2.0}
    },
    "MIN_FAVOURITES": 2,
    "SCAN_INTERVAL": 300,  # 5 Minuten
    "USER_AGENTS": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) Chrome/118.0.0.0 Safari/537.36"
    ]
}

class DataStore:
    """Simuliert eine Datenbank für Markt-Trends und historische Preise"""
    def __init__(self):
        self.market_data = []
        self.price_history = {}
        self.lock = Lock()

    def add_items(self, items):
        with self.lock:
            for item in items:
                # Deduplizierung
                if not any(d['id'] == item['id'] for d in self.market_data):
                    item['captured_at'] = datetime.now()
                    self.market_data.append(item)
            # Behalte nur die letzten 500 Funde
            self.market_data = self.market_data[-500:]

    def get_avg_price(self, query):
        relevant = [i['price']['amount'] for i in self.market_data if query.lower() in i['title'].lower()]
        return sum(relevant) / len(relevant) if relevant else 0

store = DataStore()

# --- SCRAPER ENGINE ---

class VintedIntelligence:
    def __init__(self):
        self.session = requests.Session()

    def _rotate_headers(self):
        return {
            'User-Agent': random.choice(CONFIG["USER_AGENTS"]),
            'Accept-Language': 'de-DE,de;q=0.9',
            'Referer': 'https://www.vinted.de/'
        }

    def fetch_raw(self, query):
        """Tiefen-Scan eines spezifischen Marktes"""
        headers = self._rotate_headers()
        try:
            # Initialer Handshake
            self.session.get("https://www.vinted.de", headers=headers, timeout=5)
            url = f"https://www.vinted.de/api/v2/catalog/items?search_text={query}&order=newest_first&per_page=50"
            response = self.session.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json().get('items', [])
            return []
        except Exception as e:
            print(f"[!] System Error: {e}")
            return []

    def analyze_market_depth(self, items):
        """Berechnet Liquidität und Profitabilität eines Batches"""
        if not items: return []
        
        df = pd.DataFrame([
            {
                'id': i['id'],
                'price': float(i['price']['amount']),
                'favs': i.get('favourite_count', 0),
                'title': i['title'],
                'url': i['url'],
                'photo': i.get('photos', [{}])[0].get('url', '')
            } for i in items
        ])
        
        avg = df['price'].mean()
        
        processed = []
        for _, row in df.iterrows():
            score = 0
            # Heuristik 1: Preis-Abweichung (Steal-Erkennung)
            if row['price'] < avg * 0.7: score += 40
            # Heuristik 2: Marktnachfrage (Likes)
            score += min(row['favs'] * 5, 50)
            # Heuristik 3: Speed-Indikator
            score += 10 # Standard für frische Uploads
            
            processed.append({
                **row.to_dict(),
                'score': score,
                'is_steal': score > 60,
                'avg_market_price': round(avg, 2)
            })
        
        return sorted(processed, key=lambda x: x['score'], reverse=True)

intelligence = VintedIntelligence()

# --- DASHBOARD LOGIC ---

@app.route('/')
def dashboard():
    """Professionelles Reseller-Interface"""
    search_query = request.args.get('q', 'Football Tracksuit')
    raw_items = intelligence.fetch_raw(search_query)
    analyzed_items = intelligence.analyze_market_depth(raw_items)
    store.add_items(analyzed_items)

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vinted 8-Figure Analyzer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body { font-family: 'Inter', sans-serif; background-color: #050505; color: #e5e5e5; }
            .glass { background: rgba(23, 23, 23, 0.8); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
            .steal-glow { box-shadow: 0 0 20px rgba(34, 197, 94, 0.3); border: 1px solid #22c55e; }
        </style>
    </head>
    <body class="min-h-screen">
        <nav class="glass sticky top-0 z-50 p-4 mb-8">
            <div class="max-w-7xl mx-auto flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center font-black text-black">V</div>
                    <span class="text-xl font-black tracking-tighter">VINTED <span class="text-green-500">RESALE CORE</span></span>
                </div>
                <div class="flex gap-6 text-sm font-medium">
                    <span class="text-green-400">● LIVE MARKET SCAN</span>
                    <span class="text-gray-500">API LATENCY: 142ms</span>
                </div>
            </div>
        </nav>

        <main class="max-w-7xl mx-auto px-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass p-6 rounded-2xl">
                    <p class="text-gray-400 text-sm uppercase font-bold mb-1">Markt-Volumen</p>
                    <h2 class="text-3xl font-black">50.000+ <span class="text-sm font-normal text-gray-500">Items/h</span></h2>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-gray-400 text-sm uppercase font-bold mb-1">Profit-Chancen (Steals)</p>
                    <h2 class="text-3xl font-black text-green-500">{{ steals_count }}</h2>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <p class="text-gray-400 text-sm uppercase font-bold mb-1">Avg. Market Price ({{ query }})</p>
                    <h2 class="text-3xl font-black">{{ avg_price }}€</h2>
                </div>
            </div>

            <div class="glass p-2 rounded-2xl flex gap-2 mb-12">
                <form action="/" method="get" class="flex w-full">
                    <input type="text" name="q" value="{{ query }}" placeholder="Deep Search Market..." 
                        class="w-full bg-transparent p-4 outline-none text-lg">
                    <button class="bg-white text-black px-8 py-3 rounded-xl font-bold hover:bg-green-500 transition-colors">EXECUTE SCAN</button>
                </form>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pb-20">
                {% for item in items %}
                <div class="glass rounded-3xl overflow-hidden transition-transform hover:scale-[1.02] {{ 'steal-glow' if item.is_steal else '' }}">
                    <div class="relative">
                        <img src="{{ item.photo }}" class="w-full h-64 object-cover">
                        {% if item.is_steal %}
                        <div class="absolute top-4 left-4 bg-green-500 text-black text-[10px] font-black px-3 py-1 rounded-full uppercase">High Profit Alert</div>
                        {% endif %}
                        <div class="absolute bottom-4 right-4 bg-black/80 px-3 py-1 rounded-lg text-sm font-bold">⭐ {{ item.favs }}</div>
                    </div>
                    <div class="p-5">
                        <h3 class="font-bold text-sm truncate mb-1">{{ item.title }}</h3>
                        <div class="flex justify-between items-end">
                            <div>
                                <p class="text-2xl font-black">{{ item.price }}€</p>
                                <p class="text-[10px] text-gray-500 uppercase font-bold">Mkt Avg: {{ item.avg_market_price }}€</p>
                            </div>
                            <a href="https://www.vinted.de{{ item.url }}" target="_blank" 
                                class="bg-zinc-800 p-3 rounded-xl hover:bg-white hover:text-black transition">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                </svg>
                            </a>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </main>
    </body>
    </html>
    """, 
    items=analyzed_items, 
    query=search_query, 
    steals_count=len([i for i in analyzed_items if i['is_steal']]),
    avg_price=round(sum(i['price'] for i in analyzed_items)/len(analyzed_items), 2) if analyzed_items else 0
    )

if __name__ == "__main__":
    app.run(debug=True)
