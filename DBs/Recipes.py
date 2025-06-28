import sqlite3 as sql

# establish connection to the database
conn = sql.connect('recipes.db')
cursor = conn.cursor()

# make necessary tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    name TEXT,
    ingredient TEXT,
    amount TEXT
)
''')

# Commit work and close the connection
conn.commit()
conn.close()
