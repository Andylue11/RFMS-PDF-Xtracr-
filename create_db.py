# === WATCHER HEADER START ===
# File: create_db.py
# Managed by file watcher
# === WATCHER HEADER END ===
from app import app, db

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables first to avoid any conflicts
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database tables created successfully") 
