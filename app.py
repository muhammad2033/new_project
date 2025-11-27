from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime
import os
app = Flask(__name__)
app.secret_key = 'maaz_gems_secret_key_2024'

# Database setup
def init_db():
    conn = sqlite3.connect('gemstones.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS gemstones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            color TEXT NOT NULL,
            size TEXT,
            weight REAL NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'available',
            description TEXT,
            featured INTEGER DEFAULT 0,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_sold TIMESTAMP
        )
    ''')
    
    # Insert sample data if table is empty
    c.execute('SELECT COUNT(*) FROM gemstones')
    if c.fetchone()[0] == 0:
        sample_gemstones = [
            ('Royal Blue Sapphire', 'Sapphire', 'Deep Royal Blue', '12mm x 10mm', 4.2, 2850, 'available', 'Exceptional Ceylon blue sapphire with vivid color and excellent clarity. Perfect for engagement rings or luxury jewelry.', 1),
            ('Pigeon Blood Ruby', 'Ruby', 'Pigeon Blood Red', '8mm x 8mm', 2.8, 4200, 'available', 'Rare Burmese ruby with the coveted pigeon blood color. Exceptional clarity and brilliance.', 1),
            ('Colombian Emerald', 'Emerald', 'Vivid Green', '10mm x 8mm', 3.5, 3200, 'available', 'Premium Colombian emerald with excellent transparency and vibrant green color.', 0),
            ('Pink Diamond', 'Diamond', 'Fancy Pink', '6mm x 6mm', 1.2, 8500, 'sold', 'Rare fancy pink diamond with exceptional cut and clarity.', 0),
            ('Amethyst Crystal', 'Amethyst', 'Deep Purple', '15mm x 12mm', 6.8, 450, 'available', 'Beautiful amethyst crystal with deep purple color and natural formation.', 0),
            ('Golden Topaz', 'Topaz', 'Imperial Golden', '14mm x 10mm', 5.2, 680, 'available', 'Stunning imperial topaz with golden honey color and excellent brilliance.', 0),
        ]
        
        for gem in sample_gemstones:
            c.execute('''
                INSERT INTO gemstones (name, type, color, size, weight, price, status, description, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', gem)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

def get_db_connection():
    conn = sqlite3.connect('gemstones.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = 'SELECT * FROM gemstones WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (name LIKE ? OR type LIKE ? OR color LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if status_filter != 'all':
        query += ' AND status = ?'
        params.append(status_filter)
    
    query += ' ORDER BY featured DESC, date_added DESC'
    
    gemstones = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('index.html', gemstones=gemstones, search=search, status_filter=status_filter)

@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    password = request.form['password']
    if password == 'maaz123':
        session['admin_logged_in'] = True
        flash('Successfully logged in!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid password!', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    
    query = 'SELECT * FROM gemstones WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (name LIKE ? OR type LIKE ? OR color LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if status_filter != 'all':
        query += ' AND status = ?'
        params.append(status_filter)
    
    query += ' ORDER BY date_added DESC'
    
    gemstones = conn.execute(query, params).fetchall()
    
    # Get counts
    counts = {
        'all': conn.execute('SELECT COUNT(*) FROM gemstones').fetchone()[0],
        'available': conn.execute('SELECT COUNT(*) FROM gemstones WHERE status = "available"').fetchone()[0],
        'sold': conn.execute('SELECT COUNT(*) FROM gemstones WHERE status = "sold"').fetchone()[0]
    }
    
    conn.close()
    
    return render_template('admin_dashboard.html', gemstones=gemstones, search=search, status_filter=status_filter, counts=counts)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_gemstone():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO gemstones (name, type, color, size, weight, price, status, description, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['name'],
            request.form['type'],
            request.form['color'],
            request.form['size'],
            float(request.form['weight']),
            float(request.form['price']),
            request.form['status'],
            request.form['description'],
            1 if 'featured' in request.form else 0
        ))
        conn.commit()
        conn.close()
        flash('Gemstone added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_gemstone.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
def edit_gemstone(id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        conn.execute('''
            UPDATE gemstones 
            SET name=?, type=?, color=?, size=?, weight=?, price=?, status=?, description=?, featured=?
            WHERE id=?
        ''', (
            request.form['name'],
            request.form['type'],
            request.form['color'],
            request.form['size'],
            float(request.form['weight']),
            float(request.form['price']),
            request.form['status'],
            request.form['description'],
            1 if 'featured' in request.form else 0,
            id
        ))
        conn.commit()
        conn.close()
        flash('Gemstone updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    gemstone = conn.execute('SELECT * FROM gemstones WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not gemstone:
        flash('Gemstone not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_gemstone.html', gemstone=gemstone)

@app.route('/admin/delete/<int:id>')
def delete_gemstone(id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM gemstones WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Gemstone deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_status/<int:id>')
def toggle_status(id):
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    gemstone = conn.execute('SELECT status FROM gemstones WHERE id = ?', (id,)).fetchone()
    
    if gemstone:
        new_status = 'sold' if gemstone['status'] == 'available' else 'available'
        date_sold = datetime.now() if new_status == 'sold' else None
        
        conn.execute('UPDATE gemstones SET status = ?, date_sold = ? WHERE id = ?', 
                    (new_status, date_sold, id))
        conn.commit()
        flash(f'Gemstone marked as {new_status}!', 'success')
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)