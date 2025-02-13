import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re
from dotenv import load_dotenv

app = Flask(__name__, template_folder="templates", static_folder="static")


load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# Define the correct database path
DB_PATH = r"E:\fudar\Karaval-Konkans-A\back-end\database.db"

# Print paths for debugging
print("Templates folder path:", os.path.abspath(app.template_folder))
print("Database path:", DB_PATH)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, /* Store hashed password */
        phone TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS family_details (
        family_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        nearest_city TEXT,
        details TEXT,
        num_children INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS interests (
        interest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        family_id INTEGER NOT NULL,
        interest TEXT NOT NULL,
        FOREIGN KEY (family_id) REFERENCES family_details(family_id) ON DELETE CASCADE
    );
    ''')

    conn.commit()
    conn.close()

# Ensure database is initialized before running the app
init_db()

# Function to add a new user to the database
def add_user(name, email, password, phone, city, details, num_children, interests):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hash password before storing
    hashed_password = generate_password_hash(password)

    # Insert user details
    cursor.execute('''
        INSERT INTO users (name, email, password, phone) 
        VALUES (?, ?, ?, ?)
    ''', (name, email, hashed_password, phone))
    
    user_id = cursor.lastrowid  # Get the user ID of the newly inserted user

    # Insert family details
    cursor.execute('''
        INSERT INTO family_details (user_id, nearest_city, details, num_children) 
        VALUES (?, ?, ?, ?)
    ''', (user_id, city, details, int(num_children or 0)))  # Ensure num_children is an integer

    family_id = cursor.lastrowid  # Get family ID

    # Insert interests
    if interests:
        for interest in interests.split(","):  # Assuming interests are comma-separated
            cursor.execute('''
                INSERT INTO interests (family_id, interest) 
                VALUES (?, ?)
            ''', (family_id, interest.strip()))

    conn.commit()
    conn.close()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/past-events')
def past_events():
    return render_template('Past_Events.html')

@app.route('/upcoming-events')
def upcoming_events():
    return render_template('upevents.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):  # Verify hashed password
            session['user_id'] = user[0]
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password!", "error")

    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        city = request.form['city']
        details = request.form.get('family_details', '')
        num_children = request.form.get('children_count', 0)
        interests = request.form.get('interests', '')

        # Check if the email already exists
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            flash("Email already exists! Please use a different email.", "danger")
            return redirect(url_for('register'))  # Redirect back to registration page

        # Add user to the database
        add_user(name, email, password, phone, city, details, num_children, interests)

        flash("Registration successful!", "success")
        return redirect(url_for('home'))  # Redirect to home after successful registration

    return render_template('JoinFamReg.html')

@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
    SELECT 
        u.user_id, u.name, u.email, u.phone,
        f.family_id, f.nearest_city, f.details, f.num_children,
        i.interest
    FROM users u
    LEFT JOIN family_details f ON u.user_id = f.user_id
    LEFT JOIN interests i ON f.family_id = i.family_id;
    '''
    
    cursor.execute(query)
    data = cursor.fetchall()
    

    conn.close()
    print("Fetched Registrations:", data)

    return render_template("admin.html", registrations=data)  # Pass combined data to frontend



# Forgot Password Route
@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
