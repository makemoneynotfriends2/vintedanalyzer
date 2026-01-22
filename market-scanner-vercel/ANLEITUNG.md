# 🚀 MARKET SCANNER - DEPLOYMENT ANLEITUNG

## 📦 Was ist in diesem Ordner?

```
market-scanner-vercel/
├── index.html          ← Frontend (Deine UI)
├── api/
│   └── index.py        ← Backend (Python API)
├── requirements.txt    ← Python Packages
└── vercel.json         ← Vercel Config
```

---

## 🎯 DEPLOYMENT IN 3 SCHRITTEN

### **SCHRITT 1: GitHub Repository erstellen**

1. Gehe zu **github.com**
2. Klicke oben rechts auf **"+" → "New repository"**
3. Name: `market-scanner`
4. Wähle: **Public**
5. Klicke **"Create repository"**

6. Auf der nächsten Seite:
   - Klicke **"uploading an existing file"**
   - **Drag & Drop ALLE Dateien aus diesem Ordner** in den Browser
     (index.html, vercel.json, requirements.txt, und den api/ Ordner)
   - Klicke unten **"Commit changes"**

✅ **GitHub fertig!**

---

### **SCHRITT 2: Vercel Account & Deployment**

1. Gehe zu **vercel.com**
2. Klicke **"Sign Up"**
3. Wähle: **"Continue with GitHub"**
4. Erlaube Vercel Zugriff auf GitHub

5. Nach Login:
   - Klicke **"Add New..."** → **"Project"**
   - Wähle dein Repository: **"market-scanner"**
   - Klicke **"Import"**

6. Deployment Settings:
   - **Framework Preset:** Other
   - **Root Directory:** ./
   - **Build Command:** (leer lassen)
   - **Output Directory:** (leer lassen)
   - Klicke **"Deploy"**

7. Warte 1-2 Minuten...

✅ **FERTIG!** Du bekommst eine URL wie: `https://market-scanner-xyz.vercel.app`

---

### **SCHRITT 3: Testen**

1. Öffne deine Vercel URL im Browser
2. Klicke **"Check Markets"**
3. Nach 2 Sekunden sollten Daten erscheinen!

✅ **Alles läuft!**

---

## 🔧 TROUBLESHOOTING

### "Deploy failed"?
- Prüfe ob ALLE Dateien hochgeladen wurden
- Besonders wichtig: `api/` Ordner mit `index.py`
- In Vercel: Settings → Environment Variables (keine nötig für Start)

### "API Error"?
- Öffne Browser Console (F12)
- Schaue nach Fehlermeldungen
- Vercel Logs checken: Projekt → Deployments → Letztes Deployment → Logs

### Keine Daten?
- Aktuell nutzt die App Mock-Daten (Test-Daten)
- Echtes Scraping kommt in Version 2 (siehe unten)

---

## 🎨 ANPASSUNGEN

### Frontend ändern:
1. Bearbeite `index.html` lokal
2. Committen & pushen zu GitHub (oder direkt in GitHub bearbeiten)
3. Vercel deployed automatisch neu!

### Backend ändern:
1. Bearbeite `api/index.py`
2. Committen & pushen
3. Vercel deployed automatisch neu!

---

## 🚀 NÄCHSTE SCHRITTE (Optional)

### Version 2: Echtes Scraping aktivieren
1. Scraper-Code hinzufügen (in `api/index.py`)
2. Mehr Kategorien hinzufügen
3. Bilder von Vinted/eBay laden

### Features erweitern:
- Export als CSV
- Favoriten speichern
- Email-Benachrichtigungen bei neuen Deals
- Dark/Light Mode Toggle

---

## 💰 KOSTEN

- **GitHub:** 0€ (kostenlos)
- **Vercel:** 0€ (100GB Bandwidth + 100GB-Hours/Monat kostenlos)

**Solange du unter diesen Limits bleibst = komplett kostenlos!**

---

## 📞 SUPPORT

Bei Problemen:
1. Check Vercel Deployment Logs
2. Browser Console (F12) für Frontend Errors
3. GitHub Repository prüfen ob alle Dateien da sind

✅ **VIEL ERFOLG!**
