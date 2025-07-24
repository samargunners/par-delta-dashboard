from sqlalchemy import create_engine, text  # <-- Add text here
import os

# Database connection parameters


# Full SQLAlchemy DB URL
db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW();"))  # <-- Wrap with text()
        print("✅ Connected successfully!")
        for row in result:
            print("🕒 DB Time:", row[0])
except Exception as e:
    print("❌ Connection failed.")
    print("📄 Error:", e)
