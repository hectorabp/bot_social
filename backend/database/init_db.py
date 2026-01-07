import mysql.connector
import os
from pathlib import Path
import sys

def load_env():
    base_dir = Path(r"c:/Users/hecto/OneDrive/Desktop/Emprendimientos/Proyectos/Platcom/bot_social")
    env_path = base_dir / ".env"
    
    print(f"Loading .env from {env_path}")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    v = v.strip().strip('"').strip("'")
                    os.environ[k] = v

def main():
    load_env()
    
    # Force 127.0.0.1 to avoid IPv6 issues commonly seen with 'localhost' on Windows
    host = os.environ.get('MYSQL_HOST', '127.0.0.1')
    if host == 'localhost':
        host = '127.0.0.1'
        
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_ROOT_PASSWORD', '')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    database = os.environ.get('MYSQL_DATABASE', 'db_generate_bot')
    
    print(f"Connecting to MySQL at {host}:{port} as {user}...")
    
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        
        cursor = conn.cursor()
        
        print(f"Creating database '{database}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        
        print(f"Selecting database '{database}'...")
        conn.database = database
        
        current_dir = Path(__file__).parent
        sql_file = current_dir / "db_backend.sql"
        
        if not sql_file.exists():
            print(f"Error: SQL file not found at {sql_file}")
            return
            
        print(f"Reading SQL file: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        print("Executing SQL script...")
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                result.fetchall()
                
        print("Database initialized successfully!")
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    main()
