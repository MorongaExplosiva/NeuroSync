import sqlite3

conn = sqlite3.connect("neurosync.db")
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(tablas)