import requests
import time
import random

class VintedProAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9'
        })
        self.cookies = None

    def get_initial_cookies(self):
        try:
            # Vinted braucht einen initialen Aufruf für die Session-Cookies
            r = self.session.get("https://www.vinted.de", timeout=10)
            self.cookies = r.cookies
            print("[✓] Session aktiv - Bereit für Trend-Suche.")
        except:
            print("[!] Verbindung fehlgeschlagen. Prüfe dein Internet.")

    def analyze_trends(self, brand, category_keyword):
        if not self.cookies: self.get_initial_cookies()
        
        # Kombinierte Suche für bessere Treffer (z.B. "Ralph Lauren Knitwear")
        query = f"{brand} {category_keyword}"
        url = "https://www.vinted.de/api/v2/catalog/items"
        
        params = {
            "search_text": query,
            "order": "newest_first",
            "per_page": 10,
            "price_to": 80  # Filter für Reselling-Margen (kannst du anpassen)
        }

        try:
            response = self.session.get(url, params=params, cookies=self.cookies)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"\n--- TREND-CHECK: {query.upper()} ---")
                for item in items:
                    title = item.get('title')
                    price = item.get('price', {}).get('amount')
                    # Trend-Indikator: Artikel mit vielen Favoriten bei kurzem Listing
                    favs = item.get('favourite_count', 0)
                    print(f"🔥 [{favs} Favs] {title} - {price}€")
                    print(f"🔗 https://www.vinted.de{item.get('url')}")
            elif response.status_code == 429:
                print("⚠️ Rate Limit erreicht. Pause für 2 Minuten...")
                time.sleep(120)
        except Exception as e:
            print(f"Fehler: {e}")

if __name__ == "__main__":
    bot = VintedProAnalyzer()
    
    # Deine spezifische Target-Liste
    targets = [
        {"brand": "Ralph Lauren", "trends": ["Knitwear", "Rugby Shirt", "Polo Sport"]},
        {"brand": "Lacoste", "trends": ["Vintage Trainingsjacke", "Tracksuit", "Wolle"]},
        {"brand": "True Religion", "trends": ["Ricky Super T", "Bootcut", "Jeans"]},
        {"brand": "Gucci", "trends": ["Vintage Belt", "Monogram", "Accessoires"]},
        {"brand": "Football", "trends": ["Tracksuit", "Jersey", "Training Set"]},
        {"brand": "Dolce & Gabbana", "trends": ["Vintage Mesh", "D&G Belt", "Jacket"]}
    ]

    while True:
        for target in targets:
            brand = target["brand"]
            for sub_trend in target["trends"]:
                bot.analyze_trends(brand, sub_trend)
                # Zufällige Pause zwischen 10-20 Sek, um Bot-Schutz zu umgehen
                time.sleep(random.randint(10, 20))
