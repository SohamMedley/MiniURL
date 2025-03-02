from flask import Flask, request, jsonify, redirect, send_from_directory
import sqlite3
import string
import random
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')

def init_db():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT NOT NULL,
        short_code TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        clicks INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.route('/')
def index():
    # Serve index.html from the project root directory.
    return send_from_directory(os.path.abspath(os.path.dirname(__file__)), 'index.html')

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.json
    original_url = data.get('url')
    custom_text = data.get('custom_text')
    
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Add http:// if not present
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'http://' + original_url
    
    # Use custom text if provided; otherwise, generate a random code.
    short_code = custom_text if custom_text else generate_short_code()
    
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM urls WHERE short_code = ?", (short_code,))
        existing = c.fetchone()
        
        if existing and custom_text:
            return jsonify({'error': 'Custom text already in use'}), 400
        
        while existing and not custom_text:
            short_code = generate_short_code()
            c.execute("SELECT * FROM urls WHERE short_code = ?", (short_code,))
            existing = c.fetchone()
        
        c.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (original_url, short_code))
        conn.commit()
        
        # Generate the shortened URL without the '/go' prefix.
        short_url = f"{request.host_url}{short_code}"
        
        return jsonify({
            'original_url': original_url,
            'short_url': short_url,
            'created_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

# Updated dynamic redirection route (catching any short code)
@app.route('/<short_code>')
def redirect_to_url(short_code):
    # Prevent reserved keywords from being treated as short codes.
    if short_code in ['api', 'static']:
        return redirect('/')
        
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    try:
        c.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
        result = c.fetchone()
        
        if result:
            original_url = result[0]
            # Update click count
            c.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,))
            conn.commit()
            return redirect(original_url)
        else:
            # If not found, serve the index page.
            return send_from_directory(os.path.abspath(os.path.dirname(__file__)), 'index.html')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

@app.route('/api/stats/<short_code>', methods=['GET'])
def get_url_stats(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    try:
        c.execute("SELECT original_url, created_at, clicks FROM urls WHERE short_code = ?", (short_code,))
        result = c.fetchone()
        
        if result:
            return jsonify({
                'original_url': result[0],
                'created_at': result[1],
                'clicks': result[2]
            })
        else:
            return jsonify({'error': 'URL not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
