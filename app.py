from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "iitbay_secret_key"

DATABASE = "iitbay.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buy_sell_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image TEXT,
                seller_name TEXT,
                roll_number TEXT,
                contact TEXT,
                email TEXT,
                user_id INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lost_found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                description TEXT,
                image TEXT,
                contact TEXT,
                status TEXT NOT NULL
            )
        """)
        db.commit()


@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')


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


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/buy-sell', methods=['GET', 'POST'])
def buy_sell():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        price = request.form['price']
        image = request.form.get('image')
        seller_name = request.form.get('seller_name')
        roll_number = request.form.get('roll_number')
        contact = request.form.get('contact')
        email = request.form.get('email')

        db.execute("""
            INSERT INTO buy_sell_items
            (name, description, price, image, seller_name, roll_number, contact, email, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, image, seller_name, roll_number, contact, email, session['user_id']))
        db.commit()
        return redirect(url_for('buy_sell'))

    items = db.execute("SELECT * FROM buy_sell_items ORDER BY id DESC").fetchall()
    return render_template('buy_sell.html', items=items)


@app.route('/product/<int:item_id>')
def product_detail(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        return "Item not found!", 404
    return render_template('product_detail.html', item=item)


# ---------- EDIT PRODUCT ----------
@app.route('/product/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_product(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."

    if item['user_id'] != session['user_id']:
        return "You are not allowed to edit this item."

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.form['image']

        db.execute("""
            UPDATE buy_sell_items
            SET name = ?, description = ?, price = ?, image = ?
            WHERE id = ?
        """, (name, description, price, image, item_id))
        db.commit()

        return redirect(url_for('product_detail', item_id=item_id))

    return render_template('edit_product.html', item=item)


# ---------- DELETE PRODUCT ----------
@app.route('/product/<int:item_id>/delete')
def delete_product(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    item = db.execute("SELECT * FROM buy_sell_items WHERE id = ?", (item_id,)).fetchone()

    if item is None:
        return "Item not found."

    if item['user_id'] != session['user_id']:
        return "You are not allowed to delete this item."

    db.execute("DELETE FROM buy_sell_items WHERE id = ?", (item_id,))
    db.commit()

    return redirect(url_for('buy_sell'))


@app.route('/lost-found', methods=['GET', 'POST'])
def lost_found():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        item = request.form['item']
        description = request.form.get('description')
        image = request.form.get('image')
        contact = request.form.get('contact')
        status = request.form['status']

        db.execute("""
            INSERT INTO lost_found_items
            (item, description, image, contact, status)
            VALUES (?, ?, ?, ?, ?)
        """, (item, description, image, contact, status))
        db.commit()
        return redirect(url_for('lost_found'))

    items = db.execute("SELECT * FROM lost_found_items ORDER BY id DESC").fetchall()
    return render_template('lost_found.html', items=items)


@app.route('/lost-found/<int:item_id>')
def lost_found_detail(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    item = db.execute("SELECT * FROM lost_found_items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        return "Item not found!", 404
    return render_template('lostfound_detail.html', item=item)


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, port=5001)
