from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = '1893'  # Replace with a secret key for your app

def create_connection():
    return sqlite3.connect('herdhelp.db')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with sqlite3.connect('herdhelp.db') as conn:
            con = conn.cursor()
            con.execute("INSERT INTO user (name, password) VALUES (?, ?)", (username, password))
            
        # Redirect to the signin page after successful signup
        return redirect(url_for('signin'))
    
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/how_to_use')
def how_to_use():
    return render_template('how_to_use.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE name=? AND password=?', (username, password))
        user = cursor.fetchone()
        
        conn.close()

        if user:
            # Authentication successful
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            # Authentication failed
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('signin'))
    
    return render_template('signin.html')

if __name__ == '__main__':
    app.run(debug=True)
