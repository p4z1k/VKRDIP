##warehouse_dialogs.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QDialogButtonBox, QFormLayout, QComboBox,
    QDateEdit, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator

class WarehouseDialog(QDialog):
    def __init__(self, parent=None, warehouse=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить склад" if not warehouse else "Редактировать склад")
        self.setMinimumSize(400, 300)
        self.init_ui(warehouse)

    def init_ui(self, warehouse):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        
        form.addRow("Название:", self.name_edit)
        form.addRow("Адрес:", self.address_edit)
        form.addRow("Описание:", self.desc_edit)
        
        if warehouse:
            self.name_edit.setText(warehouse.get('name', ''))
            self.address_edit.setText(warehouse.get('address', ''))
            self.desc_edit.setText(warehouse.get('description', ''))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "address": self.address_edit.text(),
            "description": self.desc_edit.text()
        }

class StockOperationDialog(QDialog):
    def __init__(self, parent=None, operation_type="incoming", cultures=[], warehouse_id=None):
        super().__init__(parent)
        self.operation_type = operation_type
        self.setWindowTitle("Добавление на склад" if operation_type == "incoming" else "Отгрузка со склада")
        self.setMinimumSize(400, 300)
        self.init_ui(cultures, warehouse_id)

    def init_ui(self, cultures, warehouse_id):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.culture_combo = QComboBox()
        self.culture_combo.addItems(cultures)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator(0, 999999, 2))
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        
        if self.operation_type == "incoming":
            self.source_edit = QLineEdit()
            form.addRow("Источник:", self.source_edit)
        else:
            self.reason_combo = QComboBox()
            self.reason_combo.addItems(["Продажа", "Перемещение", "Списание", "Другое"])
            form.addRow("Причина:", self.reason_combo)
        
        form.addRow("Культура:", self.culture_combo)
        form.addRow("Количество (т):", self.amount_edit)
        form.addRow("Дата:", self.date_edit)
        
        self.notes_edit = QLineEdit()
        form.addRow("Примечания:", self.notes_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        data = {
            "culture": self.culture_combo.currentText(),
            "amount": float(self.amount_edit.text()),
            "operation_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "notes": self.notes_edit.text()
        }
        
        if self.operation_type == "incoming":
            data["source"] = self.source_edit.text()
        else:
            data["reason"] = self.reason_combo.currentText()
        
        return data

class WarehouseHistoryDialog(QDialog):
    def __init__(self, parent=None, warehouse_id=None, db_manager=None):
        super().__init__(parent)
        self.setWindowTitle("История операций")
        self.setMinimumSize(800, 600)
        self.warehouse_id = warehouse_id
        self.db = db_manager
        self.init_ui()
        self.load_operations()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Фильтры
        filter_layout = QHBoxLayout()
        
        self.culture_filter = QComboBox()
        self.culture_filter.addItem("Все культуры")
        cultures = self.db.fetch_all(
            "SELECT DISTINCT culture FROM warehouse_operations WHERE warehouse_id=?",
            (self.warehouse_id,)
        )
        for culture in cultures:
            self.culture_filter.addItem(culture['culture'])
        self.culture_filter.currentTextChanged.connect(self.load_operations)
        
        self.type_filter = QComboBox()
        self.type_filter.addItem("Все операции")
        self.type_filter.addItem("Приход")
        self.type_filter.addItem("Расход")
        self.type_filter.currentTextChanged.connect(self.load_operations)
        
        self.date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.dateChanged.connect(self.load_operations)
        
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.dateChanged.connect(self.load_operations)
        
        filter_layout.addWidget(QLabel("Культура:"))
        filter_layout.addWidget(self.culture_filter)
        filter_layout.addWidget(QLabel("Тип:"))
        filter_layout.addWidget(self.type_filter)
        filter_layout.addWidget(QLabel("С:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("По:"))
        filter_layout.addWidget(self.date_to)
        
        # Таблица операций
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(8)
        self.operations_table.setHorizontalHeaderLabels([
            "Дата", "Тип", "Культура", "Количество", "Источник/Причина", 
            "Участок", "Сбор урожая", "Примечания"
        ])
        self.operations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.operations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.operations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.operations_table)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_operations(self):
        filters = {}
        
        culture = self.culture_filter.currentText()
        if culture != "Все культуры":
            filters['culture'] = culture
            
        op_type = self.type_filter.currentText()
        if op_type == "Приход":
            filters['operation_type'] = 'incoming'
        elif op_type == "Расход":
            filters['operation_type'] = 'outgoing'
            
        filters['date_from'] = self.date_from.date().toString("yyyy-MM-dd")
        filters['date_to'] = self.date_to.date().toString("yyyy-MM-dd")
        
        operations = self.db.fetch_all(
            """SELECT wo.*, p.name as plot_name 
               FROM warehouse_operations wo
               LEFT JOIN plots p ON wo.plot_id = p.id
               WHERE wo.warehouse_id=?""", 
            (self.warehouse_id,)
        )
        
        self.operations_table.setRowCount(len(operations))
        for row, op in enumerate(operations):
            self.operations_table.setItem(row, 0, QTableWidgetItem(op['operation_date'][:10]))
            self.operations_table.setItem(row, 1, QTableWidgetItem(
                "Приход" if op['operation_type'] == 'incoming' else 'Расход'))
            self.operations_table.setItem(row, 2, QTableWidgetItem(op['culture']))
            self.operations_table.setItem(row, 3, QTableWidgetItem(f"{op['amount']:.2f}"))
            
            source_reason = op['source'] if op['operation_type'] == 'incoming' else op['reason']
            self.operations_table.setItem(row, 4, QTableWidgetItem(source_reason or ''))
            
            self.operations_table.setItem(row, 5, QTableWidgetItem(op.get('plot_name', '')))
            self.operations_table.setItem(row, 6, QTableWidgetItem(
                str(op['harvest_id']) if op['harvest_id'] else ''))
            self.operations_table.setItem(row, 7, QTableWidgetItem(op.get('notes', '')))