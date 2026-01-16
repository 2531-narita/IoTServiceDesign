import sqlite3

def init_db():
    conn = sqlite3.connect('focus_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores 
                      (timestamp TEXT, score INTEGER, category TEXT)''')
    conn.commit()
    conn.close()