import sqlite3

conn = sqlite3.connect('herdhelp.db')
c = conn.cursor()

#creating admin table

c.execute('''CREATE TABLE IF NOT EXISTS user
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              password TEXT NOT NULL)''')

# Check if the table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
table_exists = c.fetchone()

if table_exists:
    print("user table created successfully")
else:
    print("failed to create user table")    
#c.execute("INSERT INTO admin (name, password) VALUES (?, ?)", ('ahmed', '0000'))

c.execute("SELECT * FROM user")
rows = c.fetchall()
print(rows)