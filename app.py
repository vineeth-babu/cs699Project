from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy data
buy_sell_items = [
    {'name': 'Cycle', 'price': 2000},
    {'name': 'Textbook', 'price': 150}
]

lost_found_items = [
    {'item': 'ID Card', 'status': 'Lost'},
    {'item': 'Keys', 'status': 'Found'}
]

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Buy/Sell page
@app.route('/buy-sell', methods=['GET', 'POST'])
def buy_sell():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        if name and price:
            buy_sell_items.append({'name': name, 'price': price})
        return redirect(url_for('buy_sell'))
    return render_template('buy_sell.html', items=buy_sell_items)

# Lost & Found page
@app.route('/lost-found', methods=['GET', 'POST'])
def lost_found():
    if request.method == 'POST':
        item = request.form['item']
        status = request.form['status']
        if item and status:
            lost_found_items.append({'item': item, 'status': status})
        return redirect(url_for('lost_found'))
    return render_template('lost_found.html', items=lost_found_items)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
