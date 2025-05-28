##warehouse_manager.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QDialogButtonBox,
    QHeaderView, QAbstractItemView, QComboBox, QDateEdit,
    QFormLayout, QGroupBox, QMessageBox
)
from datetime import datetime
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from db.database_manager import DatabaseManager

class WarehouseManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_all_warehouses(self):
        return self.db.fetch_all("SELECT * FROM warehouses ORDER BY name")

    def add_warehouse(self, name, address, description):
        now = datetime.now().isoformat()
        self.db.execute(
            "INSERT INTO warehouses (name, address, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (name, address, description, now, now)
        )
        return True

    def update_warehouse(self, warehouse_id, name, address, description):
        now = datetime.now().isoformat()
        self.db.execute(
            "UPDATE warehouses SET name=?, address=?, description=?, updated_at=? WHERE id=?",
            (name, address, description, now, warehouse_id)
        )
        return True

    def delete_warehouse(self, warehouse_id):
        self.db.execute("DELETE FROM warehouses WHERE id=?", (warehouse_id,))
        return True

    def get_warehouse_stocks(self, warehouse_id):
        return self.db.fetch_all(
            "SELECT culture, amount FROM warehouse_stocks WHERE warehouse_id=?",
            (warehouse_id,)
        )

    def add_stock(self, warehouse_id, culture, amount, operation_data):
        # Добавляем или обновляем запас
        current = self.db.fetch_one(
            "SELECT amount FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
            (warehouse_id, culture)
        )
        
        if current:
            new_amount = current['amount'] + amount
            self.db.execute(
                "UPDATE warehouse_stocks SET amount=? WHERE warehouse_id=? AND culture=?",
                (new_amount, warehouse_id, culture)
            )
        else:
            self.db.execute(
                "INSERT INTO warehouse_stocks (warehouse_id, culture, amount) VALUES (?, ?, ?)",
                (warehouse_id, culture, amount)
            )
        
        # Добавляем запись в историю операций
        self.db.execute(
            """INSERT INTO warehouse_operations 
            (warehouse_id, operation_type, culture, amount, operation_date, 
             source, reason, harvest_id, plot_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                warehouse_id,
                'incoming',
                culture,
                amount,
                operation_data.get('operation_date', datetime.now().isoformat()),
                operation_data.get('source'),
                operation_data.get('reason'),
                operation_data.get('harvest_id'),
                operation_data.get('plot_id'),
                operation_data.get('notes')
            )
        )
        return True

    def remove_stock(self, warehouse_id, culture, amount, operation_data):
        current = self.db.fetch_one(
            "SELECT amount FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
            (warehouse_id, culture)
        )
        
        if not current:
            return False
        
        if current['amount'] < amount:
            return False
        
        new_amount = current['amount'] - amount
        
        if new_amount <= 0:
            self.db.execute(
                "DELETE FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
                (warehouse_id, culture)
            )
        else:
            self.db.execute(
                "UPDATE warehouse_stocks SET amount=? WHERE warehouse_id=? AND culture=?",
                (new_amount, warehouse_id, culture)
            )
        
        # Добавляем запись в историю операций
        self.db.execute(
            """INSERT INTO warehouse_operations 
            (warehouse_id, operation_type, culture, amount, operation_date, 
             source, reason, harvest_id, plot_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                warehouse_id,
                'outgoing',
                culture,
                amount,
                operation_data.get('operation_date', datetime.now().isoformat()),
                operation_data.get('source'),
                operation_data.get('reason'),
                operation_data.get('harvest_id'),
                operation_data.get('plot_id'),
                operation_data.get('notes')
            )
        )
        return True

    def get_warehouse_operations(self, warehouse_id, filters=None):
        query = "SELECT * FROM warehouse_operations WHERE warehouse_id=?"
        params = [warehouse_id]
        
        if filters:
            if filters.get('culture'):
                query += " AND culture=?"
                params.append(filters['culture'])
            if filters.get('date_from'):
                query += " AND operation_date >= ?"
                params.append(filters['date_from'])
            if filters.get('date_to'):
                query += " AND operation_date <= ?"
                params.append(filters['date_to'])
            if filters.get('operation_type'):
                query += " AND operation_type=?"
                params.append(filters['operation_type'])
        
        query += " ORDER BY operation_date DESC"
        return self.db.fetch_all(query, tuple(params))