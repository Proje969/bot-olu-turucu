import sqlite3
from datetime import datetime

class TwitterDatabase:
    def __init__(self, db_name='twitter_bot.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.create_tables()

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.connect()
        
        # Hesaplar tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            api_key TEXT,
            api_secret TEXT,
            access_token TEXT,
            access_token_secret TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP
        )
        ''')

        # Proxy listesi tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            port TEXT NOT NULL,
            username TEXT,
            password TEXT,
            status TEXT DEFAULT 'active',
            last_used TIMESTAMP
        )
        ''')

        # İşlem geçmişi tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            action_type TEXT NOT NULL,
            target_user TEXT,
            target_tweet_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')

        # Hedef hesaplar tablosu
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tweet_id TEXT,
            action_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        self.conn.commit()
        self.disconnect()

    def add_account(self, username, password, email, api_key=None, api_secret=None, 
                   access_token=None, access_token_secret=None):
        self.connect()
        try:
            self.cursor.execute('''
            INSERT INTO accounts (username, password, email, api_key, api_secret, 
                                access_token, access_token_secret)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, email, api_key, api_secret, 
                 access_token, access_token_secret))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            self.disconnect()

    def add_proxy(self, ip, port, username=None, password=None):
        self.connect()
        try:
            self.cursor.execute('''
            INSERT INTO proxies (ip, port, username, password)
            VALUES (?, ?, ?, ?)
            ''', (ip, port, username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            self.disconnect()

    def add_target(self, username, action_type, tweet_id=None):
        self.connect()
        try:
            self.cursor.execute('''
            INSERT INTO targets (username, tweet_id, action_type)
            VALUES (?, ?, ?)
            ''', (username, tweet_id, action_type))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            self.disconnect()

    def log_action(self, account_id, action_type, target_user=None, target_tweet_id=None, status="completed"):
        self.connect()
        try:
            self.cursor.execute('''
            INSERT INTO actions (account_id, action_type, target_user, target_tweet_id, status)
            VALUES (?, ?, ?, ?, ?)
            ''', (account_id, action_type, target_user, target_tweet_id, status))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            self.disconnect()

    def get_active_accounts(self):
        self.connect()
        self.cursor.execute('SELECT * FROM accounts WHERE status = "active"')
        accounts = self.cursor.fetchall()
        self.disconnect()
        return accounts

    def get_available_proxy(self):
        self.connect()
        self.cursor.execute('''
        SELECT * FROM proxies 
        WHERE status = "active" 
        ORDER BY last_used ASC NULLS FIRST 
        LIMIT 1
        ''')
        proxy = self.cursor.fetchone()
        if proxy:
            self.cursor.execute('''
            UPDATE proxies 
            SET last_used = ? 
            WHERE id = ?
            ''', (datetime.now(), proxy[0]))
            self.conn.commit()
        self.disconnect()
        return proxy

    def update_account_status(self, account_id, status):
        self.connect()
        self.cursor.execute('''
        UPDATE accounts 
        SET status = ?, last_used = ? 
        WHERE id = ?
        ''', (status, datetime.now(), account_id))
        self.conn.commit()
        self.disconnect() 

    def get_account_by_id(self, account_id):
        """Belirli bir ID'ye sahip hesabın bilgilerini getirir"""
        self.connect()
        self.cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = self.cursor.fetchone()
        self.disconnect()
        return account 