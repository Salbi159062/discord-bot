import sqlite3
from config import DATABASE


class DB_Manager:
    def __init__(self, database):
        self.database = database

    # ---------- BASIC DATABASE HELPERS ----------

    def __execute(self, sql, data=()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.executemany(sql, data)
            conn.commit()

    def __select_data(self, sql, data=()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    # ---------- TABLE CREATION ----------

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    channel_id INTEGER UNIQUE,
                    title TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'open'
                )
            """)
            conn.commit()

    # ---------- TICKET FUNCTIONS ----------

    def create_ticket(self, user_id, channel_id, title, description):
        sql = """
            INSERT INTO tickets (user_id, channel_id, title, description)
            VALUES (?, ?, ?, ?)
        """
        self.__execute(sql, (user_id, channel_id, title, description))

    def get_user_tickets(self, user_id):
        sql = """
            SELECT channel_id, title
            FROM tickets
            WHERE user_id = ? AND status = 'open'
        """
        return self.__select_data(sql, (user_id,))

    def get_ticket_by_channel(self, channel_id):
        sql = """
            SELECT user_id, title, description, status
            FROM tickets
            WHERE channel_id = ?
        """
        return self.__select_data(sql, (channel_id,))

    def close_ticket(self, channel_id):
        sql = """
            UPDATE tickets
            SET status = 'closed'
            WHERE channel_id = ?
        """
        self.__execute(sql, (channel_id,))

    def delete_ticket(self, channel_id):
        sql = "DELETE FROM tickets WHERE channel_id = ?"
        self.__execute(sql, (channel_id,))


# ---------- FIRST TIME RUN SETUP ----------

if __name__ == "__main__":
    manager = DB_Manager(DATABASE)
    manager.create_tables()
    print("Ticket database successfully created!")
