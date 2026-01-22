import requests
import time
import random
import logging
import urllib3
import json
import re
import io
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, make_response
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Union, Tuple
from bs4 import BeautifulSoup

# ==============================================================================
# PHASE 1: SYSTEM ARCHITECTURE & GLOBAL SECURITY LAYER
# ==============================================================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SOVEREIGN-CORE-V11] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GlobalConfig:
    """Zentrale Steuerungseinheit für alle Markt-Parameter"""
    VERSION = "11.0.4-ENTERPRISE"
    CORE_ID = "RESALE-SOVEREIGN-8FIGURE-CORE"
    
    MARKETS = {
        "germany": {"domain": "vinted.de", "currency": "EUR", "locale": "de-DE", "tz": "Europe/Berlin"},
        "france": {"domain": "vinted.fr", "currency": "EUR", "locale": "fr-FR", "tz": "Europe/Paris"},
        "italy": {"domain": "vinted.it", "currency": "EUR", "locale": "it-IT", "tz": "Europe/Rome"},
        "spain": {"domain": "vinted.es", "currency": "EUR", "locale": "es-ES", "tz": "Europe/Madrid"},
        "uk": {"domain": "vinted.co.uk", "currency": "GBP", "locale": "en-GB", "tz": "Europe/London"}
    }
    
    # Erweiterte Marken-Heuristik für Resale-Value
    BRANDS = {
        "ralph lauren": {"weight": 1.4, "tags": ["vintage", "90s", "polo sport", "bear"]},
        "lacoste": {"weight": 1.2, "tags": ["tracksuit", "vintage", "tn"]},
        "true religion": {"weight": 1.8, "tags": ["ricky", "super t", "billy", "joey"]},
        "nike": {"weight": 1.5, "tags": ["vintage", "football", "center swoosh"]},
        "stussy": {"weight": 1.7, "tags": ["8ball", "dice", "world tour"]},
        "gucci": {"weight": 2.2, "tags": ["vintage", "monogram", "belt"]}
    }

    SCAN_LIMITS = {"max_items": 100, "request_timeout": 15, "retry_attempts": 3}
    
    # Sentiment-Vektoren für die Zustands-Analyse
    SENTIMENT_VECTORS = {
        "POSITIVE": ["neu", "etikett", "ungetragen", "ovp", "top", "deadstock", "mint", "brandneu"],
        "NEGATIVE": ["loch", "fleck", "flecken", "riss", "kaputt", "defekt", "beschädigt", "gebraucht"],
        "VINTAGE_BOOST": ["vintage", "90s", "y2k", "selten", "rare", "archive"]
    }

# ==============================================================================
# PHASE 2: DATA PERSISTENCE & ANALYTICS ENGINE (HEAVY LOGIC)
# ==============================================================================
class SovereignDataVault:
    """Verwaltet Markt-Snapshots und historische Preis-Daten für Arbitrage-Berechnungen"""
    def __init__(self):
        self._market_buffer = deque(maxlen=25000)
        self._blacklist = set()
        self._brand_intelligence = {}
        self._last_update = None

    def ingest_snapshot(self, items: List[Dict], market: str):
        """Integriert neue Scans in den Datenspeicher und berechnet Benchmarks"""
        timestamp = datetime.now()
        processed_count = 0
        
        for item in items:
            item_id = item.get('id')
            if item_id in self._blacklist: continue
            
            try:
                raw_price = item.get('price_numeric') or item.get('price', {}).get('amount')
                price = float(raw_price) if raw_price else 0.0
                
                entry = {
                    "id": item_id,
                    "market": market,
                    "brand": item.get('brand_title', 'Unknown').lower(),
                    "price": price,
                    "favs": int(item.get('favourite_count', 0)),
                    "ts": timestamp,
                    "title": item.get('title', '').lower()
                }
                self._market_buffer.append(entry)
                processed_count += 1
            except Exception as e:
                continue
        
        self._last_update = timestamp
        self._update_intelligence()
        logger.info(f"Ingested {processed_count} items into Vault for {market}")

    def _update_intelligence(self):
        """Berechnet Preis-Benchmarks mittels Pandas für maximale Performance"""
        if len(self._market_buffer) < 10: return
        
        df = pd.DataFrame(list(self._market_buffer))
        # Gruppierung nach Marke für Durchschnitts-Preise
        brand_stats = df.groupby('brand')['price'].agg(['mean', 'median', 'std', 'count']).to_dict('index')
        
        for brand, stats in brand_stats.items():
            self._brand_intelligence[brand] = {
                "avg": stats['mean'],
                "med": stats['median'],
                "volatility": stats['std'] if not pd.isna(stats['std']) else 0,
                "volume": stats['count']
            }

    def get_benchmark(self, brand: str) -> Dict:
        brand = brand.lower()
        return self._brand_intelligence.get(brand, {"avg": 45.0, "med": 40.0, "volatility": 15.0})

# ==============================================================================
# PHASE 3: MASTER CRAWLER & SESSION MANAGEMENT
# ==============================================================================
class ResaleSessionManager:
    """Verwaltet HTTP-Sessions, Cookies und simuliert menschliches Verhalten"""
    def __init__(self):
        self.session_pool = {}
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]

    def _get_headers(self, locale: str = "de-DE"):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': f'{locale},en;q=0.9',
            'Connection': 'keep-alive',
            'DNT': '1'
        }

    def initialize_market_session(self, market_key: str):
        config = GlobalConfig.MARKETS.get(market_key)
        if not config: return None
        
        session = requests.Session()
        try:
            # Initialer Handshake zur Cookie-Gewinnung
            logger.info(f"Handshaking with {config['domain']}...")
            session.get(f"https://www.{config['domain']}", headers=self._get_headers(config['locale']), timeout=10, verify=False)
            self.session_pool[market_key] = session
            return session
        except Exception as e:
            logger.error(f"Failed to initialize {market_key}: {e}")
            return None

    def get_session(self, market_key: str):
        return self.session_pool.get(market_key) or self.initialize_market_session(market_key)

# ==============================================================================
# PHASE 4: ANALYTICS CORE & SENTIMENT PROCESSING
# ==============================================================================
class SovereignAnalyzer:
    """Das Herzstück: Analysiert Artikel auf Profitabilität und Trend-Potential"""
    @staticmethod
    def run_deep_analysis(item: Dict, benchmark: Dict) -> Dict:
        title = item.get('title', '').lower()
        raw_price = item.get('price_numeric') or item.get('price', {}).get('amount')
        price = float(raw_price) if raw_price else 0.0
        favs = int(item.get('favourite_count', 0))
        
        # 1. Arbitrage Heuristik
        avg_market = benchmark.get('avg', 50.0)
        price_delta = avg_market - price
        is_steal = price < (avg_market * 0.65) # 35% Steal-Schwelle
        
        # 2. Sentiment Analyse
        sentiment_score = 50
        for word in GlobalConfig.SENTIMENT_VECTORS["POSITIVE"]:
            if word in title: sentiment_score += 12
        for word in GlobalConfig.SENTIMENT_VECTORS["NEGATIVE"]:
            if word in title: sentiment_score -= 25
        for word in GlobalConfig.SENTIMENT_VECTORS["VINTAGE_BOOST"]:
            if word in title: sentiment_score += 15
            
        # 3. Liquiditäts-Score (Hype)
        # Formel: (Favoriten * gewichteter Faktor) + (Marge * Profit-Faktor)
        hype_score = (favs * 2.5) + (max(0, price_delta) * 0.8) + (sentiment_score / 2)
        
        # 4. URL RESOLVER (FIX FÜR DEINEN FEHLER)
        raw_url = item.get('url', '')
        # Extrahiere nur den Pfad, falls eine volle URL vorhanden ist
        path = re.sub(r'https?://[^/]+', '', raw_url)
        
        return {
            "clean_url": path, # Nur der Pfad
            "mkt_avg": round(avg_market, 2),
            "est_profit": round(price_delta, 2),
            "is_steal": is_steal,
            "hype_score": round(hype_score, 1),
            "sentiment": sentiment_score
        }

# ==============================================================================
# PHASE 5: THE SOVEREIGN ORCHESTRATOR (CONTROLLER)
# ==============================================================================
vault = SovereignDataVault()
session_manager = ResaleSessionManager()
analyzer = SovereignAnalyzer()

def scan_worker(query: str, market_key: str) -> List[Dict]:
    """Einzelner Worker für parallele Markt-Scans"""
    config = GlobalConfig.MARKETS.get(market_key)
    session = session_manager.get_session(market_key)
    if not session: return []
    
    url = f"https://www.{config['domain']}/api/v2/catalog/items"
    params = {'search_text': query, 'order': 'newest_first', 'per_page': '50'}
    
    try:
        resp = session.get(url, params=params, headers=session_manager._get_headers(config['locale']), timeout=12, verify=False)
        if resp.status_code == 200:
            items = resp.json().get('items', [])
            vault.ingest_snapshot(items, market_key)
            return items
        return []
    except Exception as e:
        logger.error(f"Worker Error [{market_key}]: {e}")
        return []

@app.route('/')
def main_dashboard():
    query = request.args.get('q', 'Ralph Lauren Vintage')
    
    # Parallele Markt-Execution (DE, FR, IT)
    target_markets = ["germany", "france", "italy"]
    all_raw_items = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scan_worker, query, m): m for m in target_markets}
        for future in as_completed(futures):
            market = futures[future]
            items = future.result()
            for i in items:
                i['market_context'] = market
                all_raw_items.append(i)

    # Verarbeitung und Veredelung der Daten
    processed_items = []
    for raw in all_raw_items:
        m_key = raw.get('market_context')
        m_config = GlobalConfig.MARKETS[m_key]
        
        brand = raw.get('brand_title', 'Unknown')
        benchmark = vault.get_benchmark(brand)
        analysis = analyzer.run_deep_analysis(raw, benchmark)
        
        # FINAL URL COMPOSITION (FIX)
        final_url = f"https://www.{m_config['domain']}{analysis['clean_url']}"
        
        processed_items.append({
            "id": raw.get('id'),
            "title": raw.get('title'),
            "brand": brand,
            "price": raw.get('price_numeric') or raw.get('price', {}).get('amount'),
            "favs": raw.get('favourite_count', 0),
            "url": final_url,
            "photo": raw.get('photos', [{}])[0].get('url', '') if raw.get('photos') else '',
            "market_name": m_key.upper(),
            "analysis": analysis
        })

    # Ranking: Die besten Deals nach Hype-Score zuerst
    final_items = sorted(processed_items, key=lambda x: x['analysis']['hype_score'], reverse=True)

    # ==============================================================================
    # PHASE 6: ENTERPRISE UI (TAILWIND / JAVASCRIPT)
    # ==============================================================================
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sovereign.Core v11 | Enterprise Resale</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700&display=swap');
            body { font-family: 'Space Grotesk', sans-serif; background-color: #030303; color: #f2f2f2; }
            .glass { background: rgba(10, 10, 10, 0.85); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.06); }
            .steal-glow { border: 2px solid #00ff41; box-shadow: 0 0 35px rgba(0, 255, 65, 0.25); }
            .hype-badge { background: linear-gradient(90deg, #ff0055, #ff00aa); }
            .market-badge { background: #1a1a1a; color: #888; font-size: 10px; padding: 2px 8px; border-radius: 4px; }
        </style>
    </head>
    <body class="p-4 md:p-12">
        <div class="max-w-[1700px] mx-auto">
            <header class="flex flex-col md:flex-row justify-between items-end mb-16 gap-10">
                <div>
                    <h1 class="text-7xl font-black tracking-tighter italic">SOVEREIGN<span class="text-[#00ff41]">.11</span></h1>
                    <p class="text-zinc-600 font-bold tracking-[0.4em] uppercase text-xs mt-3">Advanced Global Arbitrage Infrastructure</p>
                </div>
                <div class="flex gap-6">
                    <div class="glass px-8 py-5 rounded-[2rem] text-right border-l-4 border-l-[#00ff41]">
                        <p class="text-zinc-500 text-[10px] font-black uppercase mb-1">Vault Capacity</p>
                        <p class="text-white font-mono text-2xl tracking-widest">25.000+ ITEMS</p>
                    </div>
                </div>
            </header>

            <div class="mb-20 glass p-3 rounded-[3rem]">
                <form action="/" method="get" class="flex gap-4">
                    <input type="text" name="q" value="{{ query }}" placeholder="Global Market Intelligence Search..." 
                        class="w-full bg-zinc-900/40 border-none p-6 rounded-[2.5rem] text-2xl outline-none focus:ring-2 focus:ring-[#00ff41]/30 transition-all">
                    <button type="submit" class="bg-[#00ff41] text-black px-16 rounded-[2.5rem] font-black text-xl hover:scale-95 transition-transform">SCAN</button>
                </form>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-12">
                {% for item in items %}
                <div class="glass rounded-[3.5rem] overflow-hidden flex flex-col relative transition-all hover:-translate-y-4 {{ 'steal-glow' if item.analysis.is_steal else '' }}">
                    <div class="relative h-96 group">
                        <img src="{{ item.photo }}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-[1.5s]">
                        <div class="absolute inset-0 bg-gradient-to-t from-[#030303] via-transparent to-transparent opacity-80"></div>
                        
                        <div class="absolute top-8 left-8 flex flex-col gap-3">
                            <span class="market-badge">{{ item.market_name }}</span>
                            {% if item.analysis.is_steal %}
                            <span class="bg-[#00ff41] text-black px-5 py-2 rounded-2xl text-[10px] font-black uppercase tracking-tighter">Profit Opportunity</span>
                            {% endif %}
                            <span class="hype-badge text-white px-5 py-2 rounded-2xl text-[10px] font-black uppercase tracking-tighter">Hype Score: {{ item.analysis.hype_score }}</span>
                        </div>
                    </div>
                    
                    <div class="p-10 flex-grow">
                        <div class="mb-8">
                            <p class="text-zinc-500 text-[10px] font-black uppercase tracking-[0.2em] mb-2">{{ item.brand }}</p>
                            <h3 class="text-2xl font-bold leading-tight h-16 line-clamp-2 tracking-tight">{{ item.title }}</h3>
                        </div>

                        <div class="flex justify-between items-end mb-10">
                            <div>
                                <p class="text-5xl font-black text-white italic tracking-tighter">{{ item.price }}€</p>
                                <p class="text-zinc-600 text-[10px] font-bold mt-2 uppercase">Mkt Benchmark: {{ item.analysis.mkt_avg }}€</p>
                            </div>
                            <div class="text-right">
                                <p class="text-[#00ff41] font-black text-2xl tracking-tighter">+{{ item.analysis.est_profit }}€</p>
                                <p class="text-zinc-600 text-[10px] font-bold uppercase mt-1">Est. Marge</p>
                            </div>
                        </div>

                        <a href="{{ item.url }}" target="_blank" 
                           class="block w-full bg-white text-black py-6 rounded-[2rem] text-center font-black hover:bg-[#00ff41] transition-all uppercase tracking-tighter text-sm">
                            Access Inventory
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """, items=final_items, query=query)

if __name__ == "__main__":
    app.run(debug=True)
