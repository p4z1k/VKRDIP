##workers_window.py


from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLineEdit, QLabel,
                            QDialogButtonBox, QHeaderView, QAbstractItemView)

class WorkersWindow(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Управление рабочими")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_workers()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Таблица рабочих
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ФИО", "Должность", "Контакт"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Панель управления
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
        
        # Кнопки 
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

    def load_workers(self):
        workers = self.db.fetch_all("SELECT * FROM workers ORDER BY name")
        self.table.setRowCount(len(workers))
        
        for row, worker in enumerate(workers):
            self.table.setItem(row, 0, QTableWidgetItem(worker['name']))
            self.table.setItem(row, 1, QTableWidgetItem(worker['position']))
            self.table.setItem(row, 2, QTableWidgetItem(worker.get('contact', '')))

    def add_worker(self):
        dialog = WorkerEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, position, contact = dialog.get_data()
            self.db.execute(
                "INSERT INTO workers (name, position, contact) VALUES (?, ?, ?)",
                (name, position, contact)
            )
            self.load_workers()

    def edit_worker(self):
        row = self.table.currentRow()
        if row >= 0:
            name = self.table.item(row, 0).text()
            position = self.table.item(row, 1).text()
            contact = self.table.item(row, 2).text()
            
            dialog = WorkerEditDialog(self, name, position, contact)
            if dialog.exec_() == QDialog.Accepted:
                new_name, new_pos, new_contact = dialog.get_data()
                self.db.execute(
                    "UPDATE workers SET name=?, position=?, contact=? WHERE name=?",
                    (new_name, new_pos, new_contact, name)
                )
                self.load_workers()

    def delete_worker(self):
        row = self.table.currentRow()
        if row >= 0:
            name = self.table.item(row, 0).text()
            self.db.execute("DELETE FROM workers WHERE name=?", (name,))
            self.load_workers()

class WorkerEditDialog(QDialog):
    def __init__(self, parent=None, name="", position="", contact=""):
        super().__init__(parent)
        self.setWindowTitle("Добавить рабочего" if not name else "Редактировать рабочего")
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
        return self.name_edit.text(), self.position_edit.text(), self.contact_edit.text()