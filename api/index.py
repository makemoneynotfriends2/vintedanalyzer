from flask import Flask, jsonify
import requests
import random

app = Flask(__name__)

# Deine Target-Liste (genau wie du sie wolltest)
TARGETS = [
    {"brand": "Ralph Lauren", "sub": "Vintage"},
    {"brand": "Lacoste", "sub": "Tracksuit"},
    {"brand": "True Religion", "sub": "Jeans"},
    {"brand": "Football", "sub": "Tracksuit"},
    {"brand": "Gucci", "sub": "Vintage"},
    {"brand": "Armani", "sub": "Vintage"},
    {"brand": "Dolce & Gabbana", "sub": "Vintage"}
]

def get_vinted_data(query):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0'}
    session = requests.Session()
    session.get("https://www.vinted.de", headers=headers) # Cookies holen
    
    url = f"https://www.vinted.de/api/v2/catalog/items?search_text={query}&order=newest_first&per_page=10"
    try:
        r = session.get(url, headers=headers)
        return r.json().get('items', [])
    except:
        return []

@app.route('/')
def home():
    # Sucht bei jedem Refresh der Seite nach einem zufälligen Trend-Thema deiner Liste
    target = random.choice(TARGETS)
    query = f"{target['brand']} {target['sub']}"
    items = get_vinted_data(query)
    
    # Erstellt eine einfache Liste für den Browser
    html = f"<h1>Trend-Analyse für: {query}</h1><ul>"
    for item in items:
        price = item.get('price', {}).get('amount')
        url = f"https://www.vinted.de{item.get('url')}"
        html += f"<li><b>{item.get('title')}</b> - {price}€ <br> <a href='{url}' target='_blank'>Link zum Deal</a></li><br>"
    html += "</ul>"
    return html

# Wichtig für Vercel/Deployment
if __name__ == "__main__":
    app.run()
