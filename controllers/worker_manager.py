##worker_manager.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QDialogButtonBox,
    QAbstractItemView, QHeaderView
)
from PyQt5.QtCore import Qt
from db.database_manager import DatabaseManager

class WorkerManagerDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Управление рабочими")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_workers()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.worker_table = QTableWidget()
        self.worker_table.setColumnCount(3)
        self.worker_table.setHorizontalHeaderLabels(["ФИО", "Должность", "Контакт"])
        self.worker_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.worker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_worker)
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_worker)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_worker)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        layout.addWidget(self.worker_table)
        layout.addLayout(btn_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_workers(self):
        workers = self.db.fetch_all("SELECT * FROM workers ORDER BY name")
        self.worker_table.setRowCount(len(workers))
        
        for row, worker in enumerate(workers):
            self.worker_table.setItem(row, 0, QTableWidgetItem(worker['name']))
            self.worker_table.setItem(row, 1, QTableWidgetItem(worker['position']))
            self.worker_table.setItem(row, 2, QTableWidgetItem(worker.get('contact', '')))

    def add_worker(self):
        dialog = WorkerEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.execute(
                "INSERT INTO workers (name, position, contact) VALUES (?, ?, ?)",
                (data['name'], data['position'], data['contact'])
            )
            self.load_workers()

    def edit_worker(self):
        row = self.worker_table.currentRow()
        if row >= 0:
            name = self.worker_table.item(row, 0).text()
            position = self.worker_table.item(row, 1).text()
            contact = self.worker_table.item(row, 2).text()
            
            dialog = WorkerEditDialog(self, name, position, contact)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                self.db.execute(
                    "UPDATE workers SET name=?, position=?, contact=? WHERE name=?",
                    (data['name'], data['position'], data['contact'], name)
                )
                self.load_workers()

    def delete_worker(self):
        row = self.worker_table.currentRow()
        if row >= 0:
            name = self.worker_table.item(row, 0).text()
            self.db.execute("DELETE FROM workers WHERE name=?", (name,))
            self.load_workers()

class WorkerEditDialog(QDialog):
    def __init__(self, parent=None, name="", position="", contact=""):
        super().__init__(parent)
        self.setWindowTitle("Добавление рабочего" if not name else "Редактирование рабочего")
        self.init_ui(name, position, contact)

    def init_ui(self, name, position, contact):
        layout = QVBoxLayout()
        
        self.name_edit = QLineEdit(name)
        self.position_edit = QLineEdit(position)
        self.contact_edit = QLineEdit(contact)
        
        layout.addWidget(QLabel("ФИО рабочего:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Должность:"))
        layout.addWidget(self.position_edit)
        layout.addWidget(QLabel("Контактная информация:"))
        layout.addWidget(self.contact_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "position": self.position_edit.text(),
            "contact": self.contact_edit.text()
        }