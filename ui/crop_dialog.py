##ui/crop_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QTextEdit, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
class CropDialog(QDialog):
    def __init__(self, parent=None, crop=None):
        super().__init__(parent)
        self.setWindowTitle("Культура")
        self.crop = crop or {}
        self.photo_bytes = self.crop.get("photo", None)
        self.init_ui()
        if crop:
            self.load_data(crop)
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.name_edit = QLineEdit()
        self.category_edit = QLineEdit()
        self.type_edit = QLineEdit()
        self.variety_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        self.photo_label = QLabel("Нет фото")
        self.photo_label.setMinimumHeight(100)
        self.photo_label.setAlignment(Qt.AlignCenter)
        load_photo_btn = QPushButton("Загрузить фото")
        load_photo_btn.clicked.connect(self.load_photo)
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Категория:"))
        layout.addWidget(self.category_edit)
        layout.addWidget(QLabel("Тип:"))
        layout.addWidget(self.type_edit)
        layout.addWidget(QLabel("Сорт:"))
        layout.addWidget(self.variety_edit)
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.desc_edit)
        layout.addWidget(QLabel("Фото:"))
        layout.addWidget(self.photo_label)
        layout.addWidget(load_photo_btn)
        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def load_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбрать фото", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            pixmap = QPixmap(file_name).scaledToWidth(120)
            self.photo_label.setPixmap(pixmap)
            with open(file_name, "rb") as f:
                self.photo_bytes = f.read()

    def load_data(self, crop):
        self.name_edit.setText(crop.get("name", ""))
        self.category_edit.setText(crop.get("category", ""))
        self.type_edit.setText(crop.get("crop_type", ""))
        self.variety_edit.setText(crop.get("variety", ""))
        self.desc_edit.setText(crop.get("description", ""))
        if crop.get("photo"):
            pixmap = QPixmap()
            pixmap.loadFromData(crop["photo"])
            self.photo_label.setPixmap(pixmap.scaledToWidth(120))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "crop_type": self.type_edit.text().strip(),
            "variety": self.variety_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "photo": self.photo_bytes
        }
