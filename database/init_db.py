"""
Helper script to initialize PostgreSQL database schema and seed data.
"""
import os
import sys
import json
import psycopg2

def load_config():
    try:
        from db_manager import get_config_path
        config_path = get_config_path()
    except Exception:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "db": {
            "host": "localhost",
            "port": 5432,
            "dbname": "postgres",
            "user": "postgres",
            "password": "superuser"
        }
    }

def init_database(db_config=None):
    if db_config is None:
        db_config = load_config().get("db", {})
    
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'database')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    schema_path = os.path.join(base_dir, 'schema.sql')
    if not os.path.exists(schema_path):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    seed_path = os.path.join(base_dir, 'seed_data.sql')

    print(f"Connecting to PostgreSQL at {db_config.get('host')}:{db_config.get('port')} DB: {db_config.get('dbname')}...")
    
    try:
        conn = psycopg2.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            dbname=db_config.get('dbname', 'postgres'),
            user=db_config.get('user', 'postgres'),
            password=db_config.get('password', 'superuser'),
            connect_timeout=5
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Exec schema
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                cur.execute(schema_sql)
                print("Schema created successfully.")

        # Exec seed
        if os.path.exists(seed_path):
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
                cur.execute(seed_sql)
                print("Seed data inserted successfully.")

        cur.close()
        conn.close()
        return True, "База данных успешно инициализирована!"
    except Exception as e:
        err_msg = f"Ошибка инициализации БД: {e}"
        print(err_msg)
        return False, err_msg

if __name__ == '__main__':
    success, msg = init_database()
    print(msg)
