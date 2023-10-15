import sqlite3

conn = sqlite3.connect('herdhelp.db')
c = conn.cursor()

#creating admin table

#c.execute('''CREATE TABLE IF NOT EXISTS user
#             (id INTEGER PRIMARY KEY AUTOINCREMENT,
#              name TEXT NOT NULL,
#              password TEXT NOT NULL)''')

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
table_exists = c.fetchone()

#if table_exists:
#    print("user table created successfully")
#else:
#    print("failed to create user table")    
#c.execute("INSERT INTO admin (name, password) VALUES (?, ?)", ('ahmed', '0000'))

#c.execute("SELECT * FROM user")
#rows = c.fetchall()
#print(rows)

# Creating a table to store chat prompts
c.execute('''CREATE TABLE IF NOT EXISTS prompts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              prompt TEXT NOT NULL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Creating a table to store chat responses
c.execute('''CREATE TABLE IF NOT EXISTS responses
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              prompt_id INTEGER,
              response TEXT NOT NULL,
              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

c.execute("SELECT prompts.prompt, responses.response FROM prompts JOIN responses ON prompts.id = responses.prompt_id WHERE prompts.user_id = ? ORDER BY prompts.timestamp DESC", (2,))
rows = c.fetchall()
print(rows)

conn.commit()
conn.close()