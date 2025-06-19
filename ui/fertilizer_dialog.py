##ui/fertilizer_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
class FertilizerDialog(QDialog):
    def __init__(self, parent=None, fertilizer=None):
        super().__init__(parent)
        self.setWindowTitle("Удобрение/Гербицид")
        self.fertilizer = fertilizer or {}
        self.photo_bytes = self.fertilizer.get("photo", None)
        self.init_ui()
        if fertilizer:
            self.load_data(fertilizer)

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Удобрение", "Гербицид"])
        self.form_edit = QLineEdit()
        self.manufacturer_edit = QLineEdit()
        self.photo_label = QLabel("Нет фото")
        self.photo_label.setMinimumHeight(100)
        self.photo_label.setAlignment(Qt.AlignCenter)
        load_photo_btn = QPushButton("Загрузить фото")
        load_photo_btn.clicked.connect(self.load_photo)
        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Тип:"))
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("Форма:"))
        layout.addWidget(self.form_edit)
        layout.addWidget(QLabel("Производитель:"))
        layout.addWidget(self.manufacturer_edit)
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

    def load_data(self, fert):
        self.name_edit.setText(fert.get("name", ""))
        idx = self.type_combo.findText(fert.get("fertilizer_type", ""), Qt.MatchExactly)
        self.type_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.form_edit.setText(fert.get("form", ""))
        self.manufacturer_edit.setText(fert.get("manufacturer", ""))
        if fert.get("photo"):
            pixmap = QPixmap()
            pixmap.loadFromData(fert["photo"])
            self.photo_label.setPixmap(pixmap.scaledToWidth(120))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "fertilizer_type": self.type_combo.currentText(),
            "form": self.form_edit.text().strip(),
            "manufacturer": self.manufacturer_edit.text().strip(),
            "photo": self.photo_bytes
        }
