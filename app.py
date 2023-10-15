from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = '1893'  # Replace with a secret key for your app

# This function creates a connection to a database. The database is stored in a file named "herdhelp.db".
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
    """
    Handles user sign-in. 
    If the request method is POST, verifies user credentials and redirects accordingly.
    If the request method is GET, renders the sign-in form.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE name=? AND password=?', (username, password))
        user = cursor.fetchone()

        if user:
            # Authentication successful
            user_id = user[0]  # Get the user_id from the database result
            session['user_id'] = user_id  # Store the user_id in the session
            print("User id in signin: ", session['user_id'])
            conn.close()
            #flash('Login successful!', 'success')
            return redirect(url_for('chat'))
        else:
            # Authentication failed
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('signin'))
    
    return render_template('signin.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        prompt = request.form['prompt']
        
        # Here, you should use your NLP model to generate a response based on the prompt.
        # For now, I'll provide a hardcoded response.
        response = "آپ کی گائے کے علاج میں اینٹی بائیوٹکس اور خون کی منتقلی شامل ہے."
        
        # Save the prompt and response to the database
        conn = create_connection()
        cursor = conn.cursor()
        user_id = session['user_id']
        print("User id in chat: ", user_id)
        cursor.execute("INSERT INTO prompts (user_id, prompt) VALUES (?, ?)", (user_id, prompt))
        prompt_id = cursor.lastrowid
        cursor.execute("INSERT INTO responses (prompt_id, response) VALUES (?, ?)", (prompt_id, response))
        conn.commit()
        conn.close()
    
    # Fetch chat history from the database
    conn = create_connection()
    cursor = conn.cursor()
    user_id = session['user_id']  # Retrieve user ID from the session
    cursor.execute("SELECT prompts.prompt, responses.response FROM prompts JOIN responses ON prompts.id = responses.prompt_id WHERE prompts.user_id = ? ORDER BY prompts.timestamp ASC", (user_id,))
    chat_history = cursor.fetchall()
    conn.close()
    
    return render_template('chat.html', chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)
