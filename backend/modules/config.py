# modules/config.py
import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()


class Database:
    """Gestor de conexiones a MySQL.

    Esta versión usa un pool de conexiones para mejorar el rendimiento bajo
    concurrencia. El pool se inicializa una vez por proceso y las conexiones
    se obtienen con `get_connection()` y se devuelven al cerrar la conexión.

    Variables de entorno relevantes:
    - MYSQL_HOST
    - MYSQL_PORT
    - MYSQL_USER
    - MYSQL_ROOT_PASSWORD
    - MYSQL_DATABASE
    - MYSQL_POOL_SIZE (opcional, por defecto 5)
    """

    _pool = None

    def __init__(self):
        self.host = os.getenv('MYSQL_HOST')
        self.port = os.getenv('MYSQL_PORT')
        self.user = os.getenv('MYSQL_USER')
        self.password = os.getenv('MYSQL_ROOT_PASSWORD')
        self.database = os.getenv('MYSQL_DATABASE')
        self.connection = None
        self.cursor = None

    def _init_pool(self):
        if Database._pool is None:
            try:
                # Fix localhost resolution on Windows
                host = self.host
                if host == 'localhost':
                    host = '127.0.0.1'

                # Verify/Create database
                try:
                    conn = mysql.connector.connect(
                        host=host,
                        user=self.user,
                        password=self.password,
                        port=int(self.port) if self.port else 3306
                    )
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                    
                    # Check if empty
                    conn.database = self.database
                    cursor.execute("SHOW TABLES")
                    if not cursor.fetchall():
                        print("[INFO] Database empty. Seeding from db_backend.sql...")
                        from pathlib import Path
                        sql_path = Path(__file__).resolve().parent.parent / 'database' / 'db_backend.sql'
                        if sql_path.exists():
                            with open(sql_path, 'r', encoding='utf-8') as f:
                                sql_script = f.read()
                            for _ in cursor.execute(sql_script, multi=True):
                                pass
                            print("[INFO] Seeding completed.")
                    
                    cursor.close()
                    conn.close()
                except Error as e:
                    print(f"[WARNING] Auto-creation of DB failed: {e}")

                pool_size = int(os.getenv('MYSQL_POOL_SIZE', 5))
            except Exception:
                pool_size = 5
            
            cfg = {
                'host': host,
                'port': int(self.port) if self.port else None,
                'user': self.user,
                'password': self.password,
                'database': self.database,
            }
            # Remove None values
            cfg = {k: v for k, v in cfg.items() if v is not None}
            try:
                Database._pool = MySQLConnectionPool(pool_name="db_pool", pool_size=pool_size, **cfg)
            except Error as e:
                print("[ERROR_INIT_POOL]:", str(e))
                raise Exception(f"Error al inicializar el pool de conexiones: {e}")

    def connect_bd(self):
        try:
            self._init_pool()
            self.connection = Database._pool.get_connection()
            self.cursor = self.connection.cursor(dictionary=True)
        except Error as e:
            print("[ERROR_CONNECT_BD]: ", str(e))
            raise Exception(f"Error al conectar a la base de datos: {e}")

    def query(self, query, params=None):
        try:
            if self.connection is None or not getattr(self.connection, 'is_connected', lambda: True)():
                self.connect_bd()
            self.cursor.execute(query, params or ())
            if isinstance(query, str) and query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Error as e:
            if self.connection is not None:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            raise Exception(f"Error al ejecutar la consulta: {e}")
        finally:
            self.close()

    def insert_query(self, query, params=None):
        """Ejecuta una consulta de inserción y devuelve el ID del registro insertado."""
        try:
            if self.connection is None or not getattr(self.connection, 'is_connected', lambda: True)():
                self.connect_bd()
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            if self.connection is not None:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            print("[ERROR_INSERT_QUERY]: ", str(e))
            raise Exception(f"Error al ejecutar la consulta de inserción: {e}")
        finally:
            self.close()

    def bulk_query(self, query, params_list):
        """
        Ejecuta una consulta en lote (bulk insert/update) utilizando `executemany`.

        Parámetros:
        ----------
        query : str
            Consulta SQL con placeholders (%s).
        params_list : list
            Lista de tuplas con los parámetros para cada ejecución.

        Retorna:
        --------
        int : Cantidad de filas afectadas.
        """
        try:
            if self.connection is None or not getattr(self.connection, 'is_connected', lambda: True)():
                self.connect_bd()
            self.cursor.executemany(query, params_list)
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            if self.connection is not None:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
            raise Exception(f"Error al ejecutar la consulta en lote: {e}")
        finally:
            self.close()

    def start_transaction(self):
        """Inicia una transacción."""
        if self.connection is None or not getattr(self.connection, 'is_connected', lambda: True)():
            self.connect_bd()
        self.connection.start_transaction()

    def commit(self):
        """Confirma la transacción actual."""
        if self.connection is not None:
            self.connection.commit()

    def rollback(self):
        """Revierte la transacción actual."""
        if self.connection is not None:
            self.connection.rollback()

    def close(self):
        if self.cursor is not None:
            try:
                self.cursor.close()
            except Exception:
                pass
            self.cursor = None
        if self.connection is not None:
            try:
                # En un pool, cerrar la conexión la devuelve al pool
                self.connection.close()
            except Exception:
                pass
            self.connection = None