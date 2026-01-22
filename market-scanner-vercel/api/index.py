from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Mock data generator for initial version
def generate_market_data():
    brands = [
        {
            'name': 'Carhartt',
            'items': 45,
            'avgProfit': 42,
            'categories': {
                'Jackets': [
                    {'title': 'Carhartt Detroit Jacket Brown', 'platform': 'Vinted', 'price': 45, 'avg': 89, 'profit': 44, 'margin': 98, 'sold': 23, 'image': ''},
                    {'title': 'Carhartt Active Jacket Navy', 'platform': 'eBay', 'price': 52, 'avg': 95, 'profit': 43, 'margin': 83, 'sold': 18, 'image': ''},
                    {'title': 'Carhartt Chore Coat Vintage', 'platform': 'Vinted', 'price': 38, 'avg': 78, 'profit': 40, 'margin': 105, 'sold': 31, 'image': ''}
                ],
                'Pants': [
                    {'title': 'Carhartt Double Knee Pants Tan', 'platform': 'Vinted', 'price': 32, 'avg': 68, 'profit': 36, 'margin': 113, 'sold': 42, 'image': ''},
                    {'title': 'Carhartt Carpenter Jeans Blue', 'platform': 'eBay', 'price': 28, 'avg': 55, 'profit': 27, 'margin': 96, 'sold': 38, 'image': ''}
                ]
            }
        },
        {
            'name': 'Dickies',
            'items': 38,
            'avgProfit': 28,
            'categories': {
                'Pants': [
                    {'title': 'Dickies 874 Work Pant Black', 'platform': 'Vinted', 'price': 25, 'avg': 48, 'profit': 23, 'margin': 92, 'sold': 52, 'image': ''},
                    {'title': 'Dickies 874 Khaki', 'platform': 'eBay', 'price': 28, 'avg': 52, 'profit': 24, 'margin': 86, 'sold': 45, 'image': ''}
                ],
                'Shirts': [
                    {'title': 'Dickies Work Shirt Short Sleeve', 'platform': 'Vinted', 'price': 18, 'avg': 35, 'profit': 17, 'margin': 94, 'sold': 38, 'image': ''}
                ]
            }
        },
        {
            'name': 'Stüssy',
            'items': 32,
            'avgProfit': 38,
            'categories': {
                'Hoodies': [
                    {'title': 'Stüssy Basic Hoodie Black', 'platform': 'Vinted', 'price': 42, 'avg': 78, 'profit': 36, 'margin': 86, 'sold': 28, 'image': ''},
                    {'title': 'Stüssy Stock Logo Hoodie Grey', 'platform': 'eBay', 'price': 48, 'avg': 85, 'profit': 37, 'margin': 77, 'sold': 22, 'image': ''}
                ],
                'T-Shirts': [
                    {'title': 'Stüssy World Tour Tee White', 'platform': 'Vinted', 'price': 22, 'avg': 45, 'profit': 23, 'margin': 105, 'sold': 35, 'image': ''}
                ]
            }
        }
    ]
    
    return {
        'brands': brands,
        'timestamp': datetime.now().isoformat(),
        'total_items': sum(b['items'] for b in brands)
    }

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'service': 'Market Scanner API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/scan', methods=['POST', 'GET'])
def scan_markets():
    try:
        # Generate mock data (in production this would scrape real data)
        data = generate_market_data()
        
        return jsonify({
            'success': True,
            'data': data,
            'cached': False
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel requires this
app = app
