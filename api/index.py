from flask import Flask
import requests
import random

app = Flask(__name__)

# Deine Target-Marken für 2026
TARGETS = [
    {"brand": "Ralph Lauren", "q": "Ralph Lauren Vintage"},
    {"brand": "Lacoste", "q": "Lacoste Tracksuit"},
    {"brand": "True Religion", "q": "True Religion Jeans"},
    {"brand": "Football", "q": "Football Tracksuit Vintage"},
    {"brand": "Gucci", "q": "Gucci Vintage"}
]

def fetch_vinted(query):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}
    s = requests.Session()
    try:
        s.get("https://www.vinted.de", headers=headers, timeout=5)
        r = s.get(f"https://www.vinted.de/api/v2/catalog/items?search_text={query}&order=newest_first", headers=headers, timeout=5)
        return r.json().get('items', [])[:10]
    except:
        return []

@app.route('/')
def index():
    t = random.choice(TARGETS)
    items = fetch_vinted(t['q'])
    
    # Hier bauen wir das Design direkt im Python-Code
    items_html = ""
    for i in items:
        price = i.get('price', {}).get('amount', '??')
        url = f"https://www.vinted.de{i.get('url')}"
        img = i.get('photos', [{}])[0].get('url', '')
        items_html += f"""
        <div style="border:1px solid #ddd; padding:10px; margin:10px; border-radius:8px; display:flex; align-items:center;">
            <img src="{img}" style="width:80px; height:80px; object-fit:cover; margin-right:15px; border-radius:5px;">
            <div>
                <h3 style="margin:0;">{i.get('title')}</h3>
                <p style="color:green; font-weight:bold; font-size:1.2em;">{price} €</p>
                <a href="{url}" target="_blank" style="background:black; color:white; padding:5px 10px; text-decoration:none; border-radius:3px;">Zum Artikel</a>
            </div>
        </div>"""

    return f"""
    <html>
        <head><title>Vinted Analyzer Pro</title></head>
        <body style="font-family:sans-serif; max-width:600px; margin:auto; padding:20px;">
            <h1>Vinted Scanner: {t['brand']}</h1>
            <p>Suche nach: <b>{t['q']}</b></p>
            <hr>
            {items_html if items_html else "<p>Keine Artikel gefunden oder Bot-Sperre.</p>"}
            <script>setTimeout(() => location.reload(), 60000);</script>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
