import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import requests
import googletrans
import os
import soundfile as sf
import numpy as np

API_URL = "https://api-inference.huggingface.co/models/ahmed807762/flan-t5-base-veterinaryQA_data-v2"
headers = {"Authorization": "Bearer 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"}

API_URL1 = "https://api-inference.huggingface.co/models/ahmed807762/whisper_urdu_tiny"
headers1 = {"Authorization": "Bearer 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"}

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

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        prompt = request.form['prompt']
        print("Prompt from user: ", prompt)
        
        Translator= googletrans.Translator()
        translation = Translator.translate(prompt, src='ur', dest='en')
        prompttr = translation.text
        print("Prompt after translation: ", prompttr)
        
        output = query({
            "inputs": "question: " +prompttr+ "? answer: ",
            "parameters": {"max_new_tokens": 250, "repetition_penalty": 7.0},
            "options": {"wait_for_model": True}
        })
        print("Output from model: ", output)
        
        translation = Translator.translate(output[0]['generated_text'], src='en', dest='ur')
        response = translation.text
        print("Response after translation: ", response)
        
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
    chat_current = cursor.fetchall()
    conn.close()
    
    return render_template('chat.html', chat_current=chat_current)

def convert_to_flac(temp_wav_path, temp_flac_path):
    print("wav: ", temp_wav_path)
    print("flac: ", temp_flac_path)
    # Read the WAV file
    data, sample_rate = sf.read(temp_wav_path)

    # Export as FLAC
    sf.write(temp_flac_path, data, sample_rate, format='FLAC')

def query1(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL1, headers=headers1, data=data)
    return response.json()

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    print("here in upload_audio")
    if 'audio' not in request.files:
        return {'error': 'No audio file provided'}, 400

    audio_file = request.files['audio']

    # Save the audio data as a temporary WAV file
    print("opening flac file")
    temp_flac_path = os.path.join(tempfile.gettempdir(), 'useraudio.flac')
    audio_file.save(temp_flac_path)

    # Convert the WAV file to FLAC
    #temp_flac_path = os.path.join(tempfile.gettempdir(), 'useraudio.flac')
    #convert_to_flac(temp_wav_path, temp_flac_path)

    print("before query")
    # Perform the inference using the query function
    prompt = query1(temp_flac_path)

    print("after query")
    print("promptdict = ", prompt)
    prompt = prompt.get('text')
    print("prompt = ", prompt)
    # Perform translation if needed
    Translator= googletrans.Translator()
    translation = Translator.translate(prompt, src='ur', dest='en')
    prompttr = translation.text
    print("Prompt after translation: ", prompttr)

    output = query({
        "inputs": "question: " + prompttr + "? answer: ",
        "parameters": {"max_new_tokens": 250, "repetition_penalty": 7.0},
        "options": {"wait_for_model": True}
    })
    print("Output from model: ", output)

    Translator = googletrans.Translator()
    translation = Translator.translate(output[0]['generated_text'], src='en', dest='ur')
    response = translation.text
    print("Response after translation: ", response)

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

    print("about to delete temp files")
    # Clean up temporary files
    #os.remove(temp_wav_path)
    #os.remove(temp_flac_path)

    # Fetch chat history from the database
    conn = create_connection()
    cursor = conn.cursor()
    user_id = session['user_id']  # Retrieve user ID from the session
    cursor.execute(
        "SELECT prompts.prompt, responses.response FROM prompts JOIN responses ON prompts.id = responses.prompt_id WHERE prompts.user_id = ? ORDER BY prompts.timestamp ASC",
        (user_id,))
    chat_current = cursor.fetchall()
    conn.close()

    return render_template('chat.html', chat_current=chat_current)

@app.route('/logout')
def logout():
    # Clear the user_id from the session, effectively logging the user out
    session.pop('user_id', None)
    # Redirect to the home page after logout
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
