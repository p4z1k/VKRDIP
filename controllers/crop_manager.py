##crop_manager.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QDialogButtonBox, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt
from db.database_manager import DatabaseManager

class CropManagerDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Управление культурами")
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_crops()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.crop_table = QTableWidget()
        self.crop_table.setColumnCount(2)
        self.crop_table.setHorizontalHeaderLabels(["Культура", "Описание"])
        self.crop_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.crop_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_crop)
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_crop)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_crop)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        layout.addWidget(self.crop_table)
        layout.addLayout(btn_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_crops(self):
        crops = self.db.fetch_all("SELECT * FROM crops ORDER BY name")
        self.crop_table.setRowCount(len(crops))
        
        for row, crop in enumerate(crops):
            self.crop_table.setItem(row, 0, QTableWidgetItem(crop['name']))
            self.crop_table.setItem(row, 1, QTableWidgetItem(crop.get('description', '')))

    def add_crop(self):
        dialog = CropEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.execute(
                "INSERT INTO crops (name, description) VALUES (?, ?)",
                (data['name'], data['description'])
            )
            self.load_crops()

    def edit_crop(self):
        row = self.crop_table.currentRow()
        if row >= 0:
            name = self.crop_table.item(row, 0).text()
            description = self.crop_table.item(row, 1).text()
            
            dialog = CropEditDialog(self, name, description)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                self.db.execute(
                    "UPDATE crops SET name=?, description=? WHERE name=?",
                    (data['name'], data['description'], name)
                )
                self.load_crops()

    def delete_crop(self):
        row = self.crop_table.currentRow()
        if row >= 0:
            name = self.crop_table.item(row, 0).text()
            self.db.execute("DELETE FROM crops WHERE name=?", (name,))
            self.load_crops()

class CropEditDialog(QDialog):
    def __init__(self, parent=None, name="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Добавление культуры" if not name else "Редактирование культуры")
        self.init_ui(name, description)

    def init_ui(self, name, description):
        layout = QVBoxLayout()
        
        self.name_edit = QLineEdit(name)
        self.desc_edit = QLineEdit(description)
        
        layout.addWidget(QLabel("Название культуры:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.desc_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "description": self.desc_edit.text()
        }