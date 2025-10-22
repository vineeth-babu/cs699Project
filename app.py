from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "iitbay_secret_key"

DATABASE = "iitbay.db"

# -------------------- DATABASE --------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

        # Buy & Sell table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buy_sell_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                seller_name TEXT,
                roll_number TEXT,
                contact_number TEXT,
                email TEXT
            )
        """)

        # Lost & Found table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lost_found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                description TEXT,
                image_url TEXT,
                finder_contact TEXT,
                status TEXT NOT NULL
            )
        """)
        db.commit()

# -------------------- ROUTES --------------------
@app.route('/')
def home():
    return render_template('home.html')

# -------------------- REGISTER --------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'student')
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, password, role))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists. Try another."
    return render_template('register.html')

# -------------------- LOGIN --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                          (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('home'))
        else:
            return "Invalid credentials. Try again."
    return render_template('login.html')

# -------------------- LOGOUT --------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -------------------- BUY & SELL --------------------
@app.route('/buy-sell', methods=['GET', 'POST'])
def buy_sell():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = request.form['price']
        image_url = request.form.get('image_url')
        seller_name = request.form.get('seller_name')
        roll_number = request.form.get('roll_number')
        contact_number = request.form.get('contact_number')
        email = request.form.get('email')

        db.execute("""
            INSERT INTO buy_sell_items
            (name, description, price, image_url, seller_name, roll_number, contact_number, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, image_url, seller_name, roll_number, contact_number, email))
        db.commit()
        return redirect(url_for('buy_sell'))

    items = db.execute("SELECT * FROM buy_sell_items").fetchall()
    return render_template('buy_sell.html', items=items)

# -------------------- LOST & FOUND --------------------
@app.route('/lost-found', methods=['GET', 'POST'])
def lost_found():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        item = request.form['item']
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        finder_contact = request.form.get('finder_contact')
        status = request.form['status']

        db.execute("""
            INSERT INTO lost_found_items
            (item, description, image_url, finder_contact, status)
            VALUES (?, ?, ?, ?, ?)
        """, (item, description, image_url, finder_contact, status))
        db.commit()
        return redirect(url_for('lost_found'))

    items = db.execute("SELECT * FROM lost_found_items").fetchall()
    return render_template('lost_found.html', items=items)

# -------------------- MAIN --------------------
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, port=5001)
