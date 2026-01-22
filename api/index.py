from flask import Flask, render_template_string, request, jsonify
import requests
import time
import random
from datetime import datetime

app = Flask(__name__)

# Konfiguration & Marken-Cluster
BRAND_CONFIG = {
    "Ralph Lauren": ["Knitwear", "Polo Bear", "Rugby Shirt", "Vintage"],
    "Lacoste": ["Tracksuit", "Vintage Jacket", "Harrington"],
    "True Religion": ["Ricky", "Super T", "Billy"],
    "Football": ["Tracksuit", "Jersey 90s", "Training Set"],
    "Designer": ["Gucci Vintage", "Armani Jacket", "D&G Mesh"]
}

class VintedProScanner:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9',
            'Referer': 'https://www.vinted.de/'
        }
        self.session = requests.Session()
        self.last_sync = None

    def get_session(self):
        """Initialisiert die Verbindung und umgeht einfache Bot-Sperren"""
        try:
            self.session.get("https://www.vinted.de", headers=self.headers, timeout=10)
            return True
        except:
            return False

    def scan_market(self, query):
        """Sucht Artikel und führt eine Basis-Analyse durch"""
        url = f"https://www.vinted.de/api/v2/catalog/items?search_text={query}&order=newest_first&per_page=20"
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                items = response.json().get('items', [])
                return self.analyze_deals(items)
            return []
        except:
            return []

    def analyze_deals(self, items):
        """Markiert potentielle Steals basierend auf Preis-Durchschnitt"""
        if not items: return []
        prices = [float(i['price']['amount']) for i in items if i.get('price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        for item in items:
            item_price = float(item['price']['amount'])
            # Deal-Indikator: 30% unter Durchschnitt = Profit-Chance
            item['is_steal'] = item_price < (avg_price * 0.7)
            item['profit_margin'] = round(avg_price - item_price, 2)
        return items

scanner = VintedProScanner()

# --- ROUTES ---

@app.route('/')
def dashboard():
    query = request.args.get('search', 'Football Tracksuit')
    if not scanner.last_sync: scanner.get_session()
    
    results = scanner.scan_market(query)
    
    # Integriertes CSS & HTML für ein echtes Dashboard-Feeling
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Vinted Business Analyzer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .steal-card { border: 2px solid #22c55e; box-shadow: 0 0 15px rgba(34, 197, 94, 0.2); }
            body { background: #0f172a; color: #f8fafc; }
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
                <h1 class="text-3xl font-bold text-green-400">VINTED <span class="text-white">PRO ANALYZER</span></h1>
                <div class="text-right">
                    <p class="text-xs text-slate-400">Status: <span class="text-green-500">Live</span></p>
                    <p class="text-xs text-slate-400">User: David (IT-Kfm)</p>
                </div>
            </header>

            <form action="/" method="get" class="mb-10 flex gap-2">
                <input type="text" name="search" placeholder="z.B. Lacoste Vintage..." value="{{q}}" 
                    class="w-full bg-slate-800 border border-slate-600 p-3 rounded-lg focus:outline-none focus:border-green-500">
                <button type="submit" class="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-bold transition">SCAN</button>
            </form>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for item in items %}
                <div class="bg-slate-800 rounded-xl overflow-hidden {{ 'steal-card' if item.is_steal else '' }}">
                    <img src="{{ item.photos[0].url if item.photos else '' }}" class="w-full h-48 object-cover">
                    <div class="p-4">
                        <h3 class="font-semibold text-lg truncate">{{ item.title }}</h3>
                        <div class="flex justify-between items-center mt-3">
                            <span class="text-2xl font-bold">{{ item.price.amount }} {{ item.price.currency_code }}</span>
                            {% if item.is_steal %}
                            <span class="bg-green-500 text-black text-xs font-bold px-2 py-1 rounded">POTENTIELLER PROFIT: {{ item.profit_margin }}€</span>
                            {% endif %}
                        </div>
                        <a href="https://www.vinted.de{{ item.url }}" target="_blank" 
                           class="block text-center mt-4 bg-slate-700 hover:bg-slate-600 py-2 rounded transition">Link öffnen</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, items=results, q=query)

if __name__ == "__main__":
    app.run()
