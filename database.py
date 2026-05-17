import sqlite3
from datetime import datetime

DB_NAME = "mama_pima.db"

def init_db():
    """Create all tables if they don't exist"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Transactions table (income & expenses)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')

    # Daily summary table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            date TEXT NOT NULL,
            total_income REAL DEFAULT 0,
            total_expenses REAL DEFAULT 0,
            profit REAL DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def save_transaction(client_id, type, description, amount):
    """Save income or expense to database"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    c.execute('''
        INSERT INTO transactions (client_id, type, description, amount, date, time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        client_id,
        type,
        description,
        amount,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_today_transactions(client_id):
    """Get all transactions for today"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        SELECT type, description, amount, time 
        FROM transactions 
        WHERE client_id = ? AND date = ?
        ORDER BY time ASC
    ''', (client_id, today))
    rows = c.fetchall()
    conn.close()
    return rows

def get_summary(client_id, date):
    """Get income, expenses and profit for a specific date"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT 
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expenses
        FROM transactions
        WHERE client_id = ? AND date = ?
    ''', (client_id, date))
    row = c.fetchone()
    conn.close()
    income = row[0] or 0
    expenses = row[1] or 0
    profit = income - expenses
    return {
        "income": income,
        "expenses": expenses,
        "profit": profit
    }

def get_monthly_transactions(client_id, year, month):
    """Get all transactions for a specific month"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT type, description, amount, date, time
        FROM transactions
        WHERE client_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ORDER BY date ASC, time ASC
    ''', (client_id, str(year), str(month).zfill(2)))
    rows = c.fetchall()
    conn.close()
    return rows

# Initialize database when this file is run
init_db()
