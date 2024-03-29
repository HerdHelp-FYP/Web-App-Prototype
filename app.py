import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import requests
import googletrans
import os
import soundfile as sf
import numpy as np
from io import BytesIO
from flask import jsonify
import re

# RAG Libs
import pinecone
from torch import cuda
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone

# RAG Setup
pinecone.init(
    api_key=os.environ.get('8827e1fc-4c19-46f2-97b9-c622b5488a3f') or '8827e1fc-4c19-46f2-97b9-c622b5488a3f',
    environment=os.environ.get('gcp-starter') or 'gcp-starter'
)

embed_model_id = 'sentence-transformers/all-MiniLM-L6-v2'

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

embed_model = HuggingFaceEmbeddings(
    model_name=embed_model_id,
    model_kwargs={'device': device},
    encode_kwargs={'device': device, 'batch_size': 50}
)

index_name = 'herdhelp-rag'
index = pinecone.Index(index_name)

text_field = 'text'  # field in metadata that contains text content

vectorstore = Pinecone(
    index, embed_model.embed_query, text_field
)
# RAG setup end


API_URL = "https://api-inference.huggingface.co/models/ahmed807762/gemma-2b-vetdataset-finetuned"
headers = {"Authorization": "Bearer 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"}

API_URL1 = "https://api-inference.huggingface.co/models/ihanif/whisper-medium-urdu"
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
            session['just_signed_in'] = True  # Set the session variable to indicate that the user has just signed in
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
    if 'just_signed_in' in session:
        # Show the loading modal only if the user has just signed in
        show_loading_modal = True
        # Remove the session variable after displaying the loading modal
        session.pop('just_signed_in', None)
    else:
        show_loading_modal = False
    
    if request.method == 'POST':
        prompt = request.form['prompt']
        print("Prompt from user: ", prompt)
        
        sys_prompt = "As a Pakistani veterinarian, you provide expertise on livestock health and farming, assisting users with relevant queries."
        
        user_prompt = prompt
        prompt =  prompt
        
        #complete prompt translation
        Translator= googletrans.Translator()
        translation = Translator.translate(prompt, src='ur', dest='en')
        prompttr = translation.text
        
        #User's prompt translation
        Translator= googletrans.Translator()
        translation = Translator.translate(user_prompt, src='ur', dest='en')
        prompttr_user = translation.text
        
        print("Prompt after translation: ", prompttr)
        
        # RAG context retrival
        
        quer = prompttr_user
        res = vectorstore.similarity_search(
            quer,  # the search query
            k=1  # returns top 3 most relevant chunks of text
        )
        
        print("Context result = ", res)
        
        concatenated_content = ""

        for document in res:
            concatenated_content += document.page_content + ' '
            
        print("Cleaned context = ", concatenated_content)
        
        # "inputs": " question: " +prompttr_user+" answer: "
        # "inputs": sys_prompt+ " Here is some relevant context: "+concatenated_content+" question: " +prompttr_user+" Now generate answer: "
        output = query({                                
            "inputs": sys_prompt+ " Here is some relevant context, "+concatenated_content+" question " +prompttr_user+" Now generate answer : ",
            "parameters": {"max_new_tokens": 250, "repetition_penalty": 7.0},
            "options": {"wait_for_model": True}
        })
        
        # Assuming 'output' contains the model's response
        output = output[0]['generated_text']
        
        print("Output from model: ", output)   

        # Use regex to find the text after the asterisk (*)
        match = re.search(r':(.*)', output)
        
        if match:
            output = match.group(1)
            print("Response after asterisk:", output)
        
        print("Output from model after regex: ", output)        
        
        
        translation = Translator.translate(output, src='en', dest='ur')
        response = translation.text
        print("Response after translation: ", response)
        
        # Save the prompt and response to the database
        conn = create_connection()
        cursor = conn.cursor()
        user_id = session['user_id']
        print("User id in chat: ", user_id)
        cursor.execute("INSERT INTO prompts (user_id, prompt) VALUES (?, ?)", (user_id, user_prompt))
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
    
    return render_template('chat.html', chat_current=chat_current, show_loading_modal=show_loading_modal)

def query1(filename):
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL1, headers=headers1, data=data)
    return response.json()

def query2(data):
    data = BytesIO(data.getvalue())  # Convert the Stream to BytesIO
    response = requests.post(API_URL1, headers=headers1, data=data)
    return response.json()

@app.route('/load_models')
def load_models():
    
    print("Model loading began")
    
    translation_success = False
    while not translation_success:
        print("before sample query")
        # Make the sample audio query
        audio_response = query1('user_audio/sampleaudio.wav')
        
        print("Gonna Try")
        
        try:
            # temporarily
            # translation_success = True  # Translation succeeded, exit loop
            # ...
            print("audio response b4 cleaning: ", audio_response)
            audio_response = audio_response.get('text')
            print("audio response: ", audio_response)
            Translator = googletrans.Translator()
            translation = Translator.translate(audio_response, src='ur', dest='en')
            response = translation.text
            print("Response after translation: ", response)
            translation_success = True  # Translation succeeded, exit loop
        except TypeError as e:
            print("Translation failed:", e)
            print("Retrying translation.")
            print("After Trying")
    
    print("Here is sample audio response: ", audio_response)

    # Make the sample text query
    text_response = query({
        "inputs": 'Sample text query',
        "options": {"wait_for_model": True}
        })
    
    print("Here is sample text response: ", text_response)

    # You can perform any additional tasks here if needed
    
    print("Models are loaded successfully")

    return jsonify({'status': 'Models loaded successfully'})

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    request_id = request.headers.get('X-Request-ID', 'No ID')
    print(f"Processing request {request_id}")

    if 'audio' not in request.files:
        return {'error': 'No audio file provided'},  400

    audio_file = request.files['audio']
    print("audio file = ", audio_file)
    
    # Assign user_id after checking for the presence of the 'audio' file
    user_id = session.get('user_id')
    if user_id is None:
        return {'error': 'User not authenticated'}, 401

    # Generate a unique filename for the user's audio in the user_audio folder
    user_audio_folder = os.path.join(os.path.dirname(__file__), 'user_audio')
    os.makedirs(user_audio_folder, exist_ok=True)  # Create the user_audio folder if it doesn't exist
    temp_flac_path = os.path.join(user_audio_folder, f'useraudio_{user_id}.flac')
    audio_file.save(temp_flac_path)


    translation_success = False
    while not translation_success:
        print("before query")
        # Perform the inference using the query function
        prompt = query1(temp_flac_path)
        print("after query")
        print("promptdict = ", prompt)
        prompt = prompt.get('text')
        print("prompt = ", prompt)

        try:            
            sys_prompt = "As a Pakistani veterinarian, you provide expertise on livestock health and farming, assisting users with relevant queries."

            user_prompt = prompt
            prompt = prompt
            
            # Perform translation if needed
            Translator= googletrans.Translator()
            translation = Translator.translate(prompt, src='ur', dest='en')
            prompttr = translation.text
            print("Prompt after translation: ", prompttr)
            
            #User's prompt translation
            Translator= googletrans.Translator()
            translation = Translator.translate(user_prompt, src='ur', dest='en')
            prompttr_user = translation.text

             # RAG context retrival
        
            quer = prompttr_user
            res = vectorstore.similarity_search(
                quer,  # the search query
                k=1  # returns top 3 most relevant chunks of text
            )
            
            print("Context result = ", res)
            
            concatenated_content = ""

            for document in res:
                concatenated_content += document.page_content + ' '
                
            print("Cleaned context = ", concatenated_content)
            
            output = query({
                 "inputs": sys_prompt+ " Here is some relevant context, "+concatenated_content+" question " +prompttr_user+" Now generate answer : ",
                "parameters": {"max_new_tokens": 250, "repetition_penalty": 7.0},
                "options": {"wait_for_model": True}
            })
            
            # Assuming 'output' contains the model's response
            output = output[0]['generated_text']
            
            print("Output from model: ", output)   

            # Use regex to find the text after the asterisk (*)
            match = re.search(r':(.*?)(?:\s*\n(.*))?$', output)
            
            if match:
                output = match.group(1)
                print("Response after asterisk:", output)
            
            print("Output from model after regex: ", output) 

            Translator = googletrans.Translator()
            translation = Translator.translate(output, src='en', dest='ur')
            response = translation.text
            print("Response after translation: ", response)
            translation_success = True  # Translation succeeded, exit loop
        except TypeError as e:
            print("Translation failed:", e)
            print("Retrying translation.")

    # Save the prompt and response to the database
    conn = create_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    print("User id in chat: ", user_id)
    cursor.execute("INSERT INTO prompts (user_id, prompt) VALUES (?, ?)", (user_id, user_prompt))
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

    return render_template('chat.html', chat_current=chat_current, show_loading_modal=False)

@app.route('/fetch_chat')
def fetch_chat():
    # Fetch chat history from the database
    conn = create_connection()
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute(
        "SELECT prompts.prompt, responses.response FROM prompts JOIN responses ON prompts.id = responses.prompt_id WHERE prompts.user_id = ? ORDER BY prompts.timestamp ASC",
        (user_id,))
    chat_current = cursor.fetchall()
    conn.close()

    # Render the chat HTML and send it as JSON
    chat_html = render_template('partials/chat_partial.html', chat_current=chat_current)
    return jsonify({'chatHTML': chat_html})

@app.route('/logout')
def logout():
    # Clear the user_id from the session, effectively logging the user out
    session.pop('user_id', None)
    # Redirect to the home page after logout
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)