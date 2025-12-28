from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os
import requests

# Explicitly set static and template folders
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Weather API Configuration
# IMPORTANT: Replace with your actual API key
WEATHER_API_KEY = "42acc1014f52253403e8036232212026"
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Database setup
def init_db():
    """Initialize the database with all tables"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Weather search history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT,
            temperature REAL,
            weather_description TEXT,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'Personal',
            priority TEXT DEFAULT 'Medium',
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # URL Shortener table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ============ PORTFOLIO ROUTES ============

@app.route('/')
def index():
    """Render the main portfolio page"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Render the admin page to view contact messages"""
    return render_template('admin.html')

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        
        # Validation
        if not name or not email or not message:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Save to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)',
            (name, email, message)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Thank you! Your message has been sent.'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ URL SHORTENER ROUTES ============

import string
import random

def generate_short_code(length=6):
    """Generate a random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route('/urlshort')
def urlshort_app():
    """Render the URL shortener page"""
    return render_template('urlshort/urlshort.html')

@app.route('/api/urls', methods=['POST'])
def create_short_url():
    """Create a shortened URL"""
    try:
        data = request.get_json()
        original_url = data.get('url')
        custom_code = data.get('custom_code', '').strip()
        
        if not original_url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # Validate URL format
        if not (original_url.startswith('http://') or original_url.startswith('https://')):
            original_url = 'https://' + original_url
        
        # Generate or use custom short code
        if custom_code:
            short_code = custom_code
            # Check if custom code already exists
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Custom code already taken'}), 400
            conn.close()
        else:
            # Generate unique short code
            short_code = generate_short_code()
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            # Ensure uniqueness
            while True:
                cursor.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
                if not cursor.fetchone():
                    break
                short_code = generate_short_code()
            conn.close()
        
        # Save to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO urls (original_url, short_code)
            VALUES (?, ?)
        ''', (original_url, short_code))
        url_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        short_url = f"http://localhost:5000/s/{short_code}"
        
        return jsonify({
            'success': True,
            'id': url_id,
            'original_url': original_url,
            'short_code': short_code,
            'short_url': short_url
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/urls', methods=['GET'])
def get_urls():
    """Get all shortened URLs"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM urls ORDER BY created_at DESC')
        urls = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Add full short URL to each
        for url in urls:
            url['short_url'] = f"http://localhost:5000/s/{url['short_code']}"
        
        return jsonify({'success': True, 'urls': urls})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/s/<short_code>')
def redirect_short_url(short_code):
    """Redirect short code to original URL"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Get original URL and increment clicks
        cursor.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,))
        result = cursor.fetchone()
        
        if result:
            original_url = result[0]
            # Increment click count
            cursor.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (short_code,))
            conn.commit()
            conn.close()
            
            # Redirect to original URL
            from flask import redirect
            return redirect(original_url)
        else:
            conn.close()
            return "Short URL not found", 404
    
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/api/urls/<int:url_id>', methods=['DELETE'])
def delete_url(url_id):
    """Delete a shortened URL"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM urls WHERE id = ?', (url_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'URL deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather/history', methods=['GET'])
def get_weather_history():
    """Get recent weather search history"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT city, country, temperature, weather_description, searched_at
            FROM weather_history
            ORDER BY searched_at DESC
            LIMIT 10
        ''')
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'history': history})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def save_weather_search(city, country, temperature, weather_description):
    """Save weather search to database"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO weather_history (city, country, temperature, weather_description)
            VALUES (?, ?, ?, ?)
        ''', (city, country, temperature, weather_description))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving weather search: {e}")

# ============ TASK MANAGER ROUTES ============

@app.route('/tasks')
def tasks_app():
    """Render the task manager page"""
    return render_template('tasks/tasks.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description', '')
        category = data.get('category', 'Personal')
        priority = data.get('priority', 'Medium')
        due_date = data.get('due_date', '')
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, category, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, category, priority, due_date))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'task_id': task_id, 'message': 'Task created successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Build update query dynamically based on provided fields
        updates = []
        values = []
        
        if 'title' in data:
            updates.append('title = ?')
            values.append(data['title'])
        if 'description' in data:
            updates.append('description = ?')
            values.append(data['description'])
        if 'category' in data:
            updates.append('category = ?')
            values.append(data['category'])
        if 'priority' in data:
            updates.append('priority = ?')
            values.append(data['priority'])
        if 'due_date' in data:
            updates.append('due_date = ?')
            values.append(data['due_date'])
        if 'completed' in data:
            updates.append('completed = ?')
            values.append(1 if data['completed'] else 0)
        
        if not updates:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/stats', methods=['GET'])
def get_task_stats():
    """Get task statistics"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM tasks')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as completed FROM tasks WHERE completed = 1')
        completed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as pending FROM tasks WHERE completed = 0')
        pending = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'completed': completed,
                'pending': pending
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Retrieve all contact messages for admin"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contacts ORDER BY created_at DESC')
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'contacts': contacts})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/manifest.json')
def manifest():
    """Serve the PWA manifest file"""
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    """Serve the service worker file"""
    return send_from_directory('static/js', 'sw.js')

# ============ WEATHER APP ROUTES ============

@app.route('/weather')
def weather_app():
    """Render the weather dashboard"""
    return render_template('weather/weather.html')

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather for a city"""
    city = request.args.get('city')
    
    if not city:
        return jsonify({'success': False, 'error': 'City name is required'}), 400
    
    try:
        url = f"{WEATHER_BASE_URL}/weather"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Save to search history
            save_weather_search(
                city=data['name'],
                country=data['sys']['country'],
                temperature=data['main']['temp'],
                weather_description=data['weather'][0]['description']
            )
            
            weather_data = {
                'success': True,
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
                'sunrise': data['sys']['sunrise'],
                'sunset': data['sys']['sunset']
            }
            
            return jsonify(weather_data)
        
        elif response.status_code == 404:
            return jsonify({'success': False, 'error': 'City not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch weather data'}), response.status_code
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    """Get 5-day forecast for a city"""
    city = request.args.get('city')
    
    if not city:
        return jsonify({'success': False, 'error': 'City name is required'}), 400
    
    try:
        url = f"{WEATHER_BASE_URL}/forecast"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            daily_forecasts = []
            seen_dates = set()
            
            for item in data['list']:
                date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                hour = datetime.fromtimestamp(item['dt']).hour
                
                if date not in seen_dates and 11 <= hour <= 13:
                    daily_forecasts.append({
                        'date': date,
                        'temperature': round(item['main']['temp'], 1),
                        'temp_min': round(item['main']['temp_min'], 1),
                        'temp_max': round(item['main']['temp_max'], 1),
                        'description': item['weather'][0]['description'],
                        'icon': item['weather'][0]['icon'],
                        'humidity': item['main']['humidity']
                    })
                    seen_dates.add(date)
                    
                    if len(daily_forecasts) == 5:
                        break
            
            return jsonify({
                'success': True,
                'city': data['city']['name'],
                'forecasts': daily_forecasts
            })
        
        else:
            return jsonify({'success': False, 'error': 'Failed to fetch forecast'}), response.status_code
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)