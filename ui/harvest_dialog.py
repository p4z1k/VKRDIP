##harvest_dialog.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QDialogButtonBox, QDateEdit, QListWidget,
    QPushButton, QFormLayout
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator

class HarvestDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, plot_id=None, culture=None, warehouses=None):
        super().__init__(parent)
        self.db = db_manager
        self.plot_id = plot_id
        self.warehouses = warehouses or []
        self.setWindowTitle("Данные уборки урожая")
        self.setMinimumSize(400, 350)  # Увеличили минимальный размер
        self.init_ui(culture)
        
    def init_ui(self, default_culture=None):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        
        self.culture_combo = QComboBox()
        self.load_cultures(default_culture)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setValidator(QDoubleValidator(0, 9999, 2))
        self.amount_edit.setPlaceholderText("Количество в тоннах")
        
        # Добавляем выбор склада
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Не отправлять на склад", None)
        for warehouse in self.warehouses:
            self.warehouse_combo.addItem(warehouse['name'], warehouse['id'])
        
        form.addRow("Дата уборки:", self.date_edit)
        form.addRow("Культура:", self.culture_combo)
        form.addRow("Количество (тонн):", self.amount_edit)
        form.addRow("Склад для отправки:", self.warehouse_combo)  # Новая строка
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_cultures(self, default_culture=None):
        cultures = self.db.fetch_all("SELECT name FROM crops ORDER BY name")
        self.culture_combo.clear()
        
        default_index = 0
        for i, culture in enumerate(cultures):
            self.culture_combo.addItem(culture['name'])
            if default_culture and culture['name'] == default_culture:
                default_index = i
                
        if cultures:
            self.culture_combo.setCurrentIndex(default_index)

    def get_data(self):
        """Возвращает данные из формы"""
        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "culture": self.culture_combo.currentText(),
            "amount": float(self.amount_edit.text()) if self.amount_edit.text() else 0.0,
            "warehouse_id": self.warehouse_combo.currentData()  # Добавляем ID склада
        }