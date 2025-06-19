## db/database_manager.py
import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "full_data.db"):

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # -------------------------------------------------------------------
        # Таблица участков 
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
            rental_expiry_date TEXT,
            crop TEXT
        );
        """)

        # -------------------------------------------------------------------
        # Таблица документов по участку 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plot_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)

        # -------------------------------------------------------------------
        # Таблица работников 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT,
            contacts TEXT,
            photo BLOB,
            hire_date TEXT,
            fire_date TEXT,
            equipment TEXT,
            plots TEXT,
            warehouse_access TEXT,
            salary REAL,
            salary_type TEXT,
            payment_info TEXT,
            status TEXT,
            date_added TEXT,
            comment TEXT
        );
        """)

        # -------------------------------------------------------------------
        # Таблица культур 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            crop_type TEXT,
            variety TEXT,
            description TEXT,
            photo BLOB
        );
        """)

        # -------------------------------------------------------------------
        # Таблица удобрений и гербицидов 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fertilizers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            fertilizer_type TEXT,
            form TEXT,
            manufacturer TEXT,
            expiry_date TEXT,
            photo BLOB
        );
        """)

        # -------------------------------------------------------------------
        # Таблица складов 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            warehouse_type TEXT NOT NULL,
            storage_type TEXT NOT NULL,
            capacity REAL NOT NULL,
            capacity_unit TEXT NOT NULL
        );
        """)

        # -------------------------------------------------------------------
        # Таблица операций на складах 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            operation_type TEXT,
            object_type TEXT,
            object_id INTEGER,
            date TEXT,
            responsible_ids TEXT,
            quantity REAL,
            unit TEXT,
            reason TEXT,
            comment TEXT,
            document BLOB,
            plot_id INTEGER,
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE SET NULL
        );
        """)

        # -------------------------------------------------------------------
        # Таблица задач по полям 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            category TEXT,
            task_type TEXT,
            status TEXT,
            plan_date TEXT,
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            comment TEXT,
            responsible_ids TEXT,
            equipment_ids TEXT,
            warehouse_id INTEGER,
            crop_id INTEGER,
            fertilizer_id INTEGER,
            qty REAL,
            unit TEXT,
            FOREIGN KEY(field_id) REFERENCES plots(id) ON DELETE CASCADE,
            FOREIGN KEY(warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL,
            FOREIGN KEY(crop_id) REFERENCES crops(id) ON DELETE SET NULL,
            FOREIGN KEY(fertilizer_id) REFERENCES fertilizers(id) ON DELETE SET NULL
        );
        """)

        # -------------------------------------------------------------------
        # Таблица сборов урожая (для аналитики)
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

        # -------------------------------------------------------------------
        # Таблица техники
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

        # -------------------------------------------------------------------
        # Таблица документов по технике 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            document_subtype TEXT,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
        );
        """)

        # -------------------------------------------------------------------
        # Таблица справочных «fields» 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT,
            crop TEXT
        );
        """)

        # -------------------------------------------------------------------
        # Новая таблица: справочник типов неисправностей (чтобы их можно было динамически расширять)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS malfunction_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        """)

        # -------------------------------------------------------------------
        # Новая таблица: журнал событий техники (поломки + ТО)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_service (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            event_category TEXT NOT NULL,      
            event_type TEXT NOT NULL,          
            description TEXT,
            date_start TEXT NOT NULL,          
            date_end TEXT,                     
            priority TEXT,                     
            status TEXT NOT NULL,              
            responsible_id INTEGER,           
            odometer_hours TEXT,              
            service_center TEXT,               
            created_at TEXT NOT NULL, 
            updated_at TEXT NOT NULL,
            FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
            FOREIGN KEY(responsible_id) REFERENCES workers(id) ON DELETE SET NULL
        );
        """)

        # -------------------------------------------------------------------
        # Новая таблица: документы, прикреплённые к событиям 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_service_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_data BLOB NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY(service_id) REFERENCES equipment_service(id) ON DELETE CASCADE
        );
        """)

        # -------------------------------------------------------------------
        # Таблица расхода удобрений / СЗР
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fertilizer_use (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            name TEXT,
            date TEXT,
            quantity REAL,
            FOREIGN KEY(field_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)

        # -------------------------------------------------------------------
        # Таблица расхода культуры для посева (для аналитики)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sowing_use (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            name TEXT,
            date TEXT,
            quantity REAL,
            FOREIGN KEY(field_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)
        # Для культур
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crop_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_id INTEGER,
            file_name TEXT,
            file_data BLOB,
            file_type TEXT,
            upload_date TEXT,
            document_type TEXT,
            document_subtype TEXT,
            FOREIGN KEY(crop_id) REFERENCES crops(id) ON DELETE CASCADE
        );
        """)
        # Для удобрений и гербицидов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fertilizer_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fertilizer_id INTEGER,
            file_name TEXT,
            file_data BLOB,
            file_type TEXT,
            upload_date TEXT,
            document_type TEXT,
            document_subtype TEXT,
            FOREIGN KEY(fertilizer_id) REFERENCES fertilizers(id) ON DELETE CASCADE
        );
        """)
        # Для удобрений и гербицидов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_operation_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id INTEGER NOT NULL,
            document_type TEXT,
            document_subtype TEXT,
            file_name TEXT,
            file_data BLOB,
            file_type TEXT,
            upload_date TEXT,
            FOREIGN KEY(operation_id) REFERENCES warehouse_operations(id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_task_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            document_type TEXT,
            document_subtype TEXT,
            file_name TEXT,
            file_data BLOB,
            file_type TEXT,
            upload_date TEXT,
            FOREIGN KEY(task_id) REFERENCES field_tasks(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_table_structure(self):
        pass

    def close(self):
        self.conn.close()