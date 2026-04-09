import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="Test",   # default database
        user="postgres",
        password="Test@123"
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
