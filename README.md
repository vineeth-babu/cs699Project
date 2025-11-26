#  IITBay: Buy, Sell and Find @ IITB  

**GitHub Repository:** [https://github.com/vineeth-babu/cs699Project](https://github.com/vineeth-babu/cs699Project)

##  Team Details  

**Team Name:** *Team Alpha*  
###  Vineeth 
- Built the complete Flask backend
- Implemented all routes and logic
- Designed database setup (`iitbay.db`)
- Created login/register system and session management
- Integrated Razorpay payment system for secure transactions

---

###  Harshith Matta 
- Designed UI layout and overall styling (`style.css`)
- Implemented responsive design
- Created `product_detail.html` and `lostfound_detail.html` pages
- Implemented real-time chat system for user communication
- Improved database column consistency and naming
- Added notification system at app level and Gmail-based notifications using SSL and SMTP
---

###  Jamala Mohan Sai Naik 
- Created `buy_sell.html` and `lost_found.html` form pages
- Handled frontend–backend integration
- Tested navigation, form submission, and data flow across templates
- Implemented notification display and ensured smooth user updates

---
## Code Structure

CS699PROJECT/
│
├── static/
│   ├── uploads/             # Folder where user-uploaded images are saved
│   └── style.css            # CSS file that handles the design and colors
│
├── templates/
│   ├── add_item.html        # Form to post a new item for sale
│   ├── add_lost_item.html   # Form to report a lost or found object
│   ├── base.html            # Master layout containing the header and menu
│   ├── buy_sell.html        # Main page showing items available for sale
│   ├── edit_lost_item.html  # Allows users to edit their lost/found reports
│   ├── edit_product.html    # Allows sellers to update item details
│   ├── home.html            # The welcome page users see first
│   ├── login.html           # Form for users to sign in
│   ├── lost_found.html      # Main page listing lost and found reports
│   ├── lostfound_detail.html # Shows full info for a specific lost item report
│   ├── pay.html             # The checkout page for making payments
│   ├── product_detail.html  # Shows full info for a single item for sale
│   ├── register.html        # Form for new users to create an account
│   └── your_products.html   # Dashboard showing items the user posted
│
├── venv/                    # Virtual environment folder (contains libraries)
├── .env                     # Stores secret keys and configuration settings
├── .gitignore               # Tells Git which files to ignore (like venv or .env)
├── app.py                   # Main code that runs the website and database
├── iitbay.db                # Database file where user and item data is stored
├── Presentation_Team_Alpha.pptx # Project presentation slides
├── README.md                # This documentation file
└── requirements.txt         # List of python libraries needed to run the app

##  Features  

-  **User Authentication:** Register and login system with session-based access  
-  **Buy & Sell Portal:** Add, browse, and view items for sale  
-  **Lost & Found Section:** Report and search lost/found items  
-  **Dynamic Detail Pages:** Individual item pages for detailed view  
-  **SQLite Database:** Persistent data storage (`iitbay.db`)  
-  **Template Inheritance:** Clean modular structure using Jinja2  
-  **Role System:** Default user role = `student` (extendable for admin later)
-  **Razorpay Payment Integration** Secure online payments inside the platform
-  **Real-Time Chat System** Enables communication between users
-  **Notification System:** In-app alerts and Gmail notifications for important updates

---



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

### 4. Run the Flask App
python app.py

If successful, you should see:

Running on http://127.0.0.1:5001

Open this address in your browser to view the app.

## Tech Stack
Backend: Flask (Python)
Database: SQLite3
Frontend: HTML, CSS (custom), Jinja2 templates
Chat system: SMTP,SSL
payment system: Razorpay
Version Control: Git & GitHub