##crops_window.py


from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLineEdit, QLabel, 
                            QDialogButtonBox, QHeaderView, QAbstractItemView)

class CropsWindow(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Управление культурами")
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_crops()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Таблица культур
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Культура", "Описание"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Панель управления
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
        
        # Кнопки OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

    def load_crops(self):
        crops = self.db.fetch_all("SELECT * FROM crops ORDER BY name")
        self.table.setRowCount(len(crops))
        
        for row, crop in enumerate(crops):
            self.table.setItem(row, 0, QTableWidgetItem(crop['name']))
            self.table.setItem(row, 1, QTableWidgetItem(crop.get('description', '')))

    def add_crop(self):
        dialog = CropEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, description = dialog.get_data()
            self.db.execute(
                "INSERT INTO crops (name, description) VALUES (?, ?)",
                (name, description)
            )
            self.load_crops()

    def edit_crop(self):
        row = self.table.currentRow()
        if row >= 0:
            name = self.table.item(row, 0).text()
            description = self.table.item(row, 1).text()
            
            dialog = CropEditDialog(self, name, description)
            if dialog.exec_() == QDialog.Accepted:
                new_name, new_desc = dialog.get_data()
                self.db.execute(
                    "UPDATE crops SET name=?, description=? WHERE name=?",
                    (new_name, new_desc, name)
                )
                self.load_crops()

    def delete_crop(self):
        row = self.table.currentRow()
        if row >= 0:
            name = self.table.item(row, 0).text()
            self.db.execute("DELETE FROM crops WHERE name=?", (name,))
            self.load_crops()

class CropEditDialog(QDialog):
    def __init__(self, parent=None, name="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Добавить культуру" if not name else "Редактировать культуру")
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
        return self.name_edit.text(), self.desc_edit.text()