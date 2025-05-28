##database_manager.py


import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "full_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            coordinates TEXT NOT NULL,
            area REAL NOT NULL,
            type TEXT DEFAULT 'Собственный',
            status TEXT DEFAULT '',  
            auto_status INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            cadastral_number TEXT,
            property_type TEXT,
            assignment_date TEXT,
            address TEXT,
            area_sqm REAL,
            land_category TEXT,
            land_use TEXT,
            cadastral_value REAL,
            owner_name TEXT,
            owner_contacts TEXT,
            rental_expiry_date TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER,
            date TEXT,
            culture TEXT,
            amount REAL,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plot_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            position TEXT,
            contact TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvest_workers (
            harvest_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            PRIMARY KEY (harvest_id, worker_id),
            FOREIGN KEY(harvest_id) REFERENCES harvests(id) ON DELETE CASCADE,
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            description TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_stocks (
            warehouse_id INTEGER NOT NULL,
            culture TEXT NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (warehouse_id, culture),
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            work_type TEXT NOT NULL,
            work_date TEXT NOT NULL,
            status TEXT NOT NULL,
            worker TEXT,
            equipment TEXT,
            description TEXT,
            notes TEXT,
            culture TEXT,  
            fertilizer TEXT,  
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            operation_date TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Планируется',
            worker_id INTEGER,
            equipment TEXT,
            notes TEXT,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE,
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE SET NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            subtype TEXT,
            name TEXT NOT NULL,
            year TEXT,
            reg_number TEXT,
            status TEXT DEFAULT 'Рабочая',
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            operation_type TEXT NOT NULL,
            culture TEXT NOT NULL,
            amount REAL NOT NULL,
            operation_date TEXT NOT NULL,
            source TEXT,
            reason TEXT,
            harvest_id INTEGER,
            plot_id INTEGER,
            notes TEXT,
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
            FOREIGN KEY(harvest_id) REFERENCES harvests(id) ON DELETE SET NULL,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE SET NULL
        );
        """)

        self.conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_table_structure(self):
        """Обновляет структуру таблиц при необходимости"""
        cursor = self.conn.cursor()
    
        # Проверяем существование столбца status в таблице plots
        cursor.execute("PRAGMA table_info(plots)")
        columns = [column[1] for column in cursor.fetchall()]
    
        if 'status' not in columns:
            cursor.execute("ALTER TABLE plots ADD COLUMN status TEXT DEFAULT ''")
    
        self.conn.commit()


    def close(self):
        self.conn.close()