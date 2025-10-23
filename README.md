#  IITBay: Buy, Sell and Find @ IITB  

**IITBay** is a student-driven web application built using **Flask** to simplify campus life at **IIT Bombay**.  
It allows students to:  
-  Buy and sell used items within the campus  
-  Report and recover lost belongings through the **Lost & Found** section  
-  Encourage reuse, save money, and build community  

---

##  Team Details  

**Team Name:** *Team Alpha*  
###  Vineeth — Backend Developer
- Built the complete **Flask backend**
- Implemented all **routes** and logic
- Designed **database setup (`iitbay.db`)**
- Created **login/register system** and **session management**

---

###  Harshith Matta — Frontend Designer
- Designed **UI layout and overall styling (`style.css`)**
- Implemented **responsive design**
- Created **`product_detail.html`** and **`lostfound_detail.html`** pages
- Improved **database column consistency** and naming

---

###  Jamala Mohan Sai Naik — UI & Form Integration
- Created **`buy_sell.html`** and **`lost_found.html`** form pages
- Handled **frontend–backend integration**
- Tested **navigation**, **form submission**, and **data flow** across templates

##  Features  

-  **User Authentication:** Register and login system with session-based access  
-  **Buy & Sell Portal:** Add, browse, and view items for sale  
-  **Lost & Found Section:** Report and search lost/found items  
-  **Dynamic Detail Pages:** Individual item pages for detailed view  
-  **SQLite Database:** Persistent data storage (`iitbay.db`)  
-  **Template Inheritance:** Clean modular structure using Jinja2  
-  **Role System:** Default user role = `student` (extendable for admin later)

---

##  Project Structure  

IITBay/
│
├── app.py # Flask backend (main application)
├── iitbay.db # SQLite database file
├── requirements.txt # Python dependencies
├── static/
│ └── style.css # Custom frontend styling
│
├── templates/
│ ├── base.html
│ ├── home.html
│ ├── register.html
│ ├── login.html
│ ├── buy_sell.html
│ ├── lost_found.html
│ ├── product_detail.html
│ ├── lostfound_detail.html
│ └── test.html # Test page for verifying Flask setup
│
└── README.md # Project documentation

##  Setup Instructions

###  1. Clone the Repository
git https://github.com/vineeth-babu/cs699Project.git
cd cs699Project

###  2. Create and Activate a Virtual Environment

For Windows:

python -m venv .venv
.venv\Scripts\activate


For macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

### 3. Install Dependencies
pip install -r requirements.txt


Example requirements.txt:

Flask==3.0.3

### 4. Run the Flask App
python app.py


If successful, you should see:

Running on http://127.0.0.1:5001


Open this address in your browser to view the app.

## Testing Flask Setup

Create a simple test file inside the templates folder named test.html:

<h1>Hello Flask!</h1>
<p>If you see this, Flask is working.</p>


Then run:

python app.py


Visit http://127.0.0.1:5001/test to confirm Flask is running.

## Future Enhancements

--Image upload functionality for items

--Search and filter system

--Analytics on popular items and campus activity

## Tech Stack

Backend: Flask (Python)

Database: SQLite3

Frontend: HTML, CSS (custom), Jinja2 templates

Version Control: Git & GitHub