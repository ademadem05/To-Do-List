import sqlite3
from datetime import datetime, timezone

DB_PATH = "todo.db"

def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
            )
        """
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,        
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)   
            )
        """)

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def create_user(name,email,password_hash):
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, now()),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def todo_to_dict(row):
    return{
        "id" : row["id"],
        "title" : row["title"],
        "description" : row["description"]
    }

def create_todo(user_id, title, description):
    timestamp = now()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (user_id, title, description, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, title, description, timestamp, timestamp),
            
        )
        todo_id = cursor.lastrowid
    return{
        "id" : todo_id,
        "title" : title,
        "description" : description
    }


def get_todo(todo_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return dict(row) if row else None

def update_todo(todo_id, title, description):
    with get_connection() as conn:
        conn.execute(
            "UPDATE todos SET title = ?, description = ?, updated_at = ? WHERE id = ?",
            (title, description, now(), todo_id)
        )
    return {"id": todo_id, "title": title, "description": description}

def delete_todo(todo_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM todos WHERE id =?", (todo_id,))

def get_todos (user_id, page, limit, term=None):
    offset = (page - 1) * limit  

    where = "WHERE user_id = ?"
    params = [user_id]

    # Arama terimi varsa koşula ekle
    if term:
        where += " AND (title LIKE ? OR description LIKE ?)"
        pattern = f"%{term}%"
        params += [pattern, pattern]

    
    with get_connection() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM todos {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM todos {where} ORDER BY id LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        
    return [todo_to_dict(row) for row in rows], total

def get_user_by_email(email):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def main():
    init_db()
    user_id = create_user("Test User", "test@example.com", "fake-hash")
    print("User id:", user_id)
    print("Same email again:", create_user("Other", "test@example.com", "x"))

    # Bu testi ikinci kez çalıştırırsan kullanıcı zaten var; o zaman onu bul
    if user_id is None:
        user_id = get_user_by_email("test@example.com")["id"]

    for i in range(1, 4):
        create_todo(user_id, f"Task {i}", f"Description {i}")

    todos, total = get_todos(user_id, page=1, limit=2)
    print("Page 1:", todos, "Total:", total)
    todos, total = get_todos(user_id, page=2, limit=2)
    print("Page 2:", todos, "Total:", total)




if __name__ == "__main__":
    main()
    