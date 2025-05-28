## warehouse_tab.py


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QAbstractItemView, QHeaderView, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt
from .warehouse_dialogs import WarehouseDialog, StockOperationDialog, WarehouseHistoryDialog

class WarehouseTab(QWidget):
    def __init__(self, parent=None, plot_manager=None):
        super().__init__(parent)
        self.plot_manager = plot_manager
        self.selected_warehouse = None
        self.init_ui()
        self.update_warehouses_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Панель управления складами
        control_panel = QHBoxLayout()
        
        self.add_warehouse_btn = QPushButton("Добавить склад")
        self.add_warehouse_btn.clicked.connect(self.add_warehouse)
        
        self.refresh_warehouses_btn = QPushButton("Обновить")
        self.refresh_warehouses_btn.clicked.connect(self.update_warehouses_list)
        
        control_panel.addWidget(self.add_warehouse_btn)
        control_panel.addWidget(self.refresh_warehouses_btn)
        control_panel.addStretch()
        
        # Таблица складов
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(4)
        self.warehouses_table.setHorizontalHeaderLabels(["Название", "Адрес", "Описание", "Действия"])
        self.warehouses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.warehouses_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.warehouses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Группа для запасов на складе
        self.stocks_group = QGroupBox("Запасы на складе")
        self.stocks_group.setEnabled(False)
        stocks_layout = QVBoxLayout()
        
        # Таблица запасов
        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(3)
        self.stocks_table.setHorizontalHeaderLabels(["Культура", "Количество (т)", "Действия"])
        self.stocks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stocks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.stocks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Панель кнопок для работы с запасами
        stocks_btn_layout = QHBoxLayout()
        
        self.add_stock_btn = QPushButton("Добавить запасы")
        self.add_stock_btn.clicked.connect(self.add_stock)
        self.add_stock_btn.setEnabled(False)
        
        self.remove_stock_btn = QPushButton("Отгрузить")
        self.remove_stock_btn.clicked.connect(self.remove_stock)
        self.remove_stock_btn.setEnabled(False)
        
        self.history_btn = QPushButton("История операций")
        self.history_btn.clicked.connect(self.show_warehouse_history)
        self.history_btn.setEnabled(False)
        
        stocks_btn_layout.addWidget(self.add_stock_btn)
        stocks_btn_layout.addWidget(self.remove_stock_btn)
        stocks_btn_layout.addWidget(self.history_btn)
        stocks_btn_layout.addStretch()
        
        stocks_layout.addWidget(self.stocks_table)
        stocks_layout.addLayout(stocks_btn_layout)
        self.stocks_group.setLayout(stocks_layout)
        
        layout.addLayout(control_panel)
        layout.addWidget(self.warehouses_table)
        layout.addWidget(self.stocks_group)

    def update_warehouses_list(self):
        warehouses = self.plot_manager.db.fetch_all("SELECT * FROM warehouses ORDER BY name")
        self.warehouses_table.setRowCount(len(warehouses))
    
        for row, warehouse in enumerate(warehouses):
            self.warehouses_table.setItem(row, 0, QTableWidgetItem(warehouse['name']))
            self.warehouses_table.setItem(row, 1, QTableWidgetItem(warehouse.get('address', '')))
            self.warehouses_table.setItem(row, 2, QTableWidgetItem(warehouse.get('description', '')))
        
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
        
            edit_btn = QPushButton("✏️")
            edit_btn.clicked.connect(self.create_edit_warehouse_handler(warehouse))
        
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(self.create_delete_warehouse_handler(warehouse))
        
            select_btn = QPushButton("Выбрать")
            select_btn.clicked.connect(self.create_select_warehouse_handler(warehouse))
        
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addWidget(select_btn)
        
            self.warehouses_table.setCellWidget(row, 3, action_widget)

    def create_edit_warehouse_handler(self, warehouse):
        def handler():
            self.edit_warehouse(warehouse)
        return handler

    def create_delete_warehouse_handler(self, warehouse):
        def handler():
            self.delete_warehouse(warehouse)
        return handler

    def create_select_warehouse_handler(self, warehouse):
        def handler():
            self.select_warehouse(warehouse)
        return handler

    def add_warehouse(self):
        dialog = WarehouseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.plot_manager.db.execute(
                "INSERT INTO warehouses (name, address, description) VALUES (?, ?, ?)",
                (data['name'], data['address'], data['description'])
            )
            self.update_warehouses_list()

    def edit_warehouse(self, warehouse):
        dialog = WarehouseDialog(self, warehouse)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.plot_manager.db.execute(
                "UPDATE warehouses SET name=?, address=?, description=? WHERE id=?",
                (data['name'], data['address'], data['description'], warehouse['id'])
            )
            self.update_warehouses_list()

    def delete_warehouse(self, warehouse):
        if QMessageBox.question(
            self, 
            "Удаление склада", 
            f"Вы уверены, что хотите удалить склад '{warehouse['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.plot_manager.db.execute("DELETE FROM warehouses WHERE id=?", (warehouse['id'],))
            self.update_warehouses_list()
            if hasattr(self, 'selected_warehouse') and self.selected_warehouse['id'] == warehouse['id']:
                self.stocks_group.setEnabled(False)
                self.add_stock_btn.setEnabled(False)
                self.remove_stock_btn.setEnabled(False)
                self.history_btn.setEnabled(False)

    def select_warehouse(self, warehouse):
        self.selected_warehouse = warehouse
        self.stocks_group.setEnabled(True)
        self.add_stock_btn.setEnabled(True)
        self.remove_stock_btn.setEnabled(True)
        self.history_btn.setEnabled(True)
        self.update_stocks_table(warehouse['id'])

    def update_stocks_table(self, warehouse_id):
        stocks = self.plot_manager.db.fetch_all(
            "SELECT culture, amount FROM warehouse_stocks WHERE warehouse_id=?",
            (warehouse_id,)
        )
    
        self.stocks_table.setRowCount(len(stocks))
    
        for row, stock in enumerate(stocks):
            self.stocks_table.setItem(row, 0, QTableWidgetItem(stock['culture']))
            self.stocks_table.setItem(row, 1, QTableWidgetItem(f"{stock['amount']:.2f}"))
        
            history_btn = QPushButton("История")
            history_btn.clicked.connect(self.create_culture_history_handler(
                warehouse_id, stock['culture']))
        
            self.stocks_table.setCellWidget(row, 2, history_btn)

    def create_culture_history_handler(self, warehouse_id, culture):
        def handler():
            self.show_warehouse_history(warehouse_id, culture)
        return handler

    def add_stock(self):
        if not hasattr(self, 'selected_warehouse'):
            return
    
        cultures = self.plot_manager.db.fetch_all("SELECT name FROM crops ORDER BY name")
        culture_names = [c['name'] for c in cultures]
    
        dialog = StockOperationDialog(self, "incoming", culture_names)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.plot_manager.db.execute(
                """INSERT INTO warehouse_operations 
                (warehouse_id, operation_type, culture, amount, operation_date, source, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.selected_warehouse['id'],
                    'incoming',
                    data['culture'],
                    data['amount'],
                    data['operation_date'],
                    data['source'],
                    data['notes']
                )
            )
        
            current = self.plot_manager.db.fetch_one(
                "SELECT amount FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
                (self.selected_warehouse['id'], data['culture'])
            )
        
            if current:
                new_amount = current['amount'] + data['amount']
                self.plot_manager.db.execute(
                    "UPDATE warehouse_stocks SET amount=? WHERE warehouse_id=? AND culture=?",
                    (new_amount, self.selected_warehouse['id'], data['culture'])
                )
            else:
                self.plot_manager.db.execute(
                    "INSERT INTO warehouse_stocks (warehouse_id, culture, amount) VALUES (?, ?, ?)",
                    (self.selected_warehouse['id'], data['culture'], data['amount'])
                )
        
            self.update_stocks_table(self.selected_warehouse['id'])

    def remove_stock(self):
        if not hasattr(self, 'selected_warehouse'):
            return
    
        stocks = self.plot_manager.db.fetch_all(
            "SELECT culture FROM warehouse_stocks WHERE warehouse_id=?",
            (self.selected_warehouse['id'],)
        )
    
        if not stocks:
            QMessageBox.warning(self, "Ошибка", "На складе нет запасов для отгрузки")
            return
    
        culture_names = [s['culture'] for s in stocks]
    
        dialog = StockOperationDialog(self, "outgoing", culture_names)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
        
            current = self.plot_manager.db.fetch_one(
                "SELECT amount FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
                (self.selected_warehouse['id'], data['culture'])
            )
        
            if not current or current['amount'] < data['amount']:
                QMessageBox.warning(self, "Ошибка", "Недостаточное количество на складе")
                return
        
            self.plot_manager.db.execute(
                """INSERT INTO warehouse_operations 
                (warehouse_id, operation_type, culture, amount, operation_date, reason, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.selected_warehouse['id'],
                    'outgoing',
                    data['culture'],
                    data['amount'],
                    data['operation_date'],
                    data['reason'],
                    data['notes']
                )
            )
        
            new_amount = current['amount'] - data['amount']
            if new_amount <= 0:
                self.plot_manager.db.execute(
                    "DELETE FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
                    (self.selected_warehouse['id'], data['culture'])
                )
            else:
                self.plot_manager.db.execute(
                    "UPDATE warehouse_stocks SET amount=? WHERE warehouse_id=? AND culture=?",
                    (new_amount, self.selected_warehouse['id'], data['culture'])
                )
        
            self.update_stocks_table(self.selected_warehouse['id'])

    def show_warehouse_history(self, warehouse_id=None, culture=None):
        if not warehouse_id and hasattr(self, 'selected_warehouse'):
            warehouse_id = self.selected_warehouse['id']
    
        if not warehouse_id:
            return
    
        dialog = WarehouseHistoryDialog(self, warehouse_id, self.plot_manager.db)
        if culture:
            dialog.culture_filter.setCurrentText(culture)
        dialog.exec_()