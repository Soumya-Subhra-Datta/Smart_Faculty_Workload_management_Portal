"""
Database connection pool module.
Provides a connection pool for MySQL database access.
"""
import mysql.connector
from mysql.connector import pooling
from config import Config


# Create a connection pool
_pool = None


def get_pool():
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="faculty_pool",
            pool_size=10,
            pool_reset_session=True,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    return _pool


def get_connection():
    """Get a connection from the pool."""
    return get_pool().get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a query with automatic connection management.
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit the transaction
    
    Returns:
        Query result or lastrowid for INSERT operations
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            conn.commit()
            result = cursor.lastrowid
        else:
            conn.commit()
            result = cursor.rowcount
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_many(query, data_list, commit=True):
    """Execute a query for multiple data sets."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data_list)
        if commit:
            conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
