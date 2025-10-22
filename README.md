# IITBay: Buy, Sell and Find @ IITB

IITBay is a student-driven platform designed to make campus life simpler.
Students can sell items they no longer need, buy useful things at affordable prices, and post in the Lost & Found section to recover their belongings.
This project encourages reuse, saves money, and builds a stronger sense of community within IIT Bombay.

# Team Details

 Team Name: IITBay Developers

Vineeth - Backend Developer (Flask routes, templates, logic)
Harshith Matta - Frontend Design (HTML, CSS, styling, static content)
Jamala Mohan Sai Naik - Forms and UI Integration (template testing, navigation, layout)

# Project Setup Instructions

Clone the Repository
git clone https://github.com/your-username/IITBay.git

cd IITBay

Create and Activate Virtual Environment (Recommended)

For Windows:
python -m venv .venv
.venv\Scripts\activate

For macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

Install Required Libraries
Make sure you have pip installed, then run:
pip install -r requirements.txt

Example content of requirements.txt:
Flask==3.0.3

Run the Flask App
python app.py

After running, you should see:

Running on http://127.0.0.1:5001

Open this address in your browser to view the app.

# Project Structure

IITBay/
│
├── app.py - Flask backend
├── requirements.txt - Python dependencies
├── templates/ - HTML templates (Jinja2)
│ ├── base.html
│ ├── home.html
│ ├── buy_sell.html
│ └── lost_found.html
├── static/ - (Optional) CSS, JS, images
└── README.md - Project documentation

# Screenshots to Include for Submission

Home Page (/)

Buy/Sell Page (/buy-sell)

Lost & Found Page (/lost-found)

Optional: Screenshot of terminal showing Flask running

# Features (Current Version)

Basic Flask app setup

Navigation between Home, Buy/Sell, and Lost & Found

Form submission to add items dynamically (in-memory)

Jinja template inheritance (base.html)

Modular structure for future expansion