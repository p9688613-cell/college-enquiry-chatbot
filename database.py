"""
database.py - SQLite Database Management Module
==================================================
Handles all database operations for the College Enquiry Chatbot:
- FAQ storage, updates, and searches
- Student query logging and analytics
- Unanswered query tracking for college administrators
"""

import sqlite3
import os
import json

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'college_chatbot.db')
FAQS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faqs.json')


def get_connection():
    """Establish and return a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and seed initial FAQs if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. FAQs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Query Logs Table (tracks student queries, confidence, and fallbacks)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            matched_intent TEXT,
            confidence REAL,
            is_fallback INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Check if FAQs table is empty, and seed from faqs.json
    cursor.execute("SELECT COUNT(*) AS count FROM faqs")
    count = cursor.fetchone()['count']

    if count == 0 and os.path.exists(FAQS_JSON):
        try:
            with open(FAQS_JSON, 'r', encoding='utf-8') as f:
                seed_faqs = json.load(f)
                for item in seed_faqs:
                    cursor.execute('''
                        INSERT INTO faqs (category, question, answer, keywords)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        item.get('category', 'General'),
                        item.get('question', ''),
                        item.get('answer', ''),
                        item.get('keywords', '')
                    ))
            conn.commit()
            print(f"[Database] Successfully initialized with {len(seed_faqs)} FAQs.")
        except Exception as e:
            print(f"[Database] Error seeding FAQs: {e}")

    conn.close()


def get_all_faqs():
    """Fetch all FAQs ordered by category and ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs ORDER BY category, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_faq_by_id(faq_id):
    """Retrieve a single FAQ by its primary key ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_faq(category, question, answer, keywords=""):
    """Insert a new FAQ into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO faqs (category, question, answer, keywords)
        VALUES (?, ?, ?, ?)
    ''', (category.strip(), question.strip(), answer.strip(), keywords.strip()))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_faq(faq_id, category, question, answer, keywords=""):
    """Update an existing FAQ in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE faqs
        SET category = ?, question = ?, answer = ?, keywords = ?
        WHERE id = ?
    ''', (category.strip(), question.strip(), answer.strip(), keywords.strip(), faq_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_faq(faq_id):
    """Delete an FAQ by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def search_faqs(keyword):
    """Search FAQs by matching question, answer, or keywords."""
    conn = get_connection()
    cursor = conn.cursor()
    term = f"%{keyword.strip()}%"
    cursor.execute('''
        SELECT * FROM faqs 
        WHERE question LIKE ? OR answer LIKE ? OR keywords LIKE ?
        ORDER BY id ASC
    ''', (term, term, term))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def log_query(user_query, matched_intent, confidence, is_fallback=0):
    """Log student queries for performance evaluation and auditing."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO query_logs (user_query, matched_intent, confidence, is_fallback)
        VALUES (?, ?, ?, ?)
    ''', (user_query[:500], matched_intent, float(confidence), 1 if is_fallback else 0))
    conn.commit()
    conn.close()


def get_query_logs(limit=50):
    """Fetch the most recent student queries."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM query_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_unanswered_queries(limit=50):
    """Fetch queries that triggered the fallback response so administrators can review them."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM query_logs WHERE is_fallback = 1 ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    """Return summary statistics for the admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total_faqs FROM faqs")
    total_faqs = cursor.fetchone()['total_faqs']

    cursor.execute("SELECT COUNT(*) AS total_queries FROM query_logs")
    total_queries = cursor.fetchone()['total_queries']

    cursor.execute("SELECT COUNT(*) AS total_fallbacks FROM query_logs WHERE is_fallback = 1")
    total_fallbacks = cursor.fetchone()['total_fallbacks']

    conn.close()
    return {
        "total_faqs": total_faqs,
        "total_queries": total_queries,
        "total_fallbacks": total_fallbacks
    }


if __name__ == '__main__':
    # When executed directly, initialize the database
    init_db()
    print("[Database] Initialization test complete.")

