##ui/warehouse_dialogs.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QPushButton
)
from PyQt5.QtCore import Qt
ALLOWED_UNITS = ["Тонны", "Мешки", "Ящики", "Бочки"]

class AddWarehouseDialog(QDialog):
    def __init__(self, parent=None, db=None, warehouse_data=None):
        super().__init__(parent)
        self.db = db
        self.warehouse_data = warehouse_data
        self.setWindowTitle("Добавить склад" if warehouse_data is None else "Редактировать склад")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Название склада:"))
        self.name_edit = QLineEdit(self.warehouse_data.get("name", "") if self.warehouse_data else "")
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Адрес:"))
        self.address_edit = QLineEdit(self.warehouse_data.get("address", "") if self.warehouse_data else "")
        layout.addWidget(self.address_edit)
        layout.addWidget(QLabel("Тип склада:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Зернохранилище", "Овощехранилище", "Склад удобрений и гербицидов"])
        if self.warehouse_data:
            current_type = self.warehouse_data.get("warehouse_type", "")
            idx = self.type_combo.findText(current_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("Тип хранения:"))
        self.storage_combo = QComboBox()
        self.storage_combo.addItems(["Навалом", "В контейнерах/ящиках", "Спецхранилища"])
        if self.warehouse_data:
            current_storage = self.warehouse_data.get("storage_type", "")
            idx2 = self.storage_combo.findText(current_storage)
            if idx2 >= 0:
                self.storage_combo.setCurrentIndex(idx2)
        layout.addWidget(self.storage_combo)
        cap_row = QHBoxLayout()
        layout.addWidget(QLabel("Вместимость:"))
        self.capacity_edit = QDoubleSpinBox()
        self.capacity_edit.setRange(0, 1_000_000)
        self.capacity_edit.setDecimals(2)
        if self.warehouse_data:
            self.capacity_edit.setValue(self.warehouse_data.get("capacity", 0.0))
        cap_row.addWidget(self.capacity_edit)
        self.unit_combo = QComboBox()
        cap_row.addWidget(self.unit_combo)
        layout.addLayout(cap_row)
        self.refresh_units()
        if self.warehouse_data:
            prev_unit = self.warehouse_data.get("capacity_unit", "")
            idxu = self.unit_combo.findText(prev_unit)
            if idxu >= 0:
                self.unit_combo.setCurrentIndex(idxu)
        self.storage_combo.currentIndexChanged.connect(self.refresh_units)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def refresh_units(self):
        self.unit_combo.clear()
        self.unit_combo.addItems(ALLOWED_UNITS)

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "warehouse_type": self.type_combo.currentText(),
            "storage_type": self.storage_combo.currentText(),
            "capacity": self.capacity_edit.value(),
            "capacity_unit": self.unit_combo.currentText()
        }
