##harvest_with_warehouse_dialog.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QDialogButtonBox, QDateEdit, QListWidget,
    QPushButton, QFormLayout
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator

class HarvestWithWarehouseDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, warehouses=None):
        super().__init__(parent)
        self.db = db_manager
        self.warehouses = warehouses
        self.setWindowTitle("Добавление сбора урожая")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.culture_combo = QComboBox()
        self.load_cultures()
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Количество в тоннах")
        self.amount_edit.setValidator(QDoubleValidator(0, 9999, 2))
        
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Не отправлять на склад", None)
        for warehouse in self.warehouses:
            self.warehouse_combo.addItem(warehouse['name'], warehouse['id'])
        
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Дополнительная информация")
        
        # Список рабочих
        self.worker_list = QListWidget()
        self.worker_list.setSelectionMode(QListWidget.MultiSelection)
        self.load_workers()
        
        form.addRow("Дата сбора:", self.date_edit)
        form.addRow("Культура:", self.culture_combo)
        form.addRow("Количество (тонн):", self.amount_edit)
        form.addRow("Склад:", self.warehouse_combo)
        form.addRow("Примечания:", self.notes_edit)
        form.addRow("Рабочие:", self.worker_list)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def load_cultures(self):
        cultures = self.db.fetch_all("SELECT name FROM crops ORDER BY name")
        self.culture_combo.clear()
        for culture in cultures:
            self.culture_combo.addItem(culture['name'])

    def load_workers(self):
        workers = self.db.fetch_all("SELECT id, name, position FROM workers ORDER BY name")
        self.worker_list.clear()
        for worker in workers:
            self.worker_list.addItem(f"{worker['name']} ({worker['position']})")
            self.worker_list.item(self.worker_list.count()-1).setData(Qt.UserRole, worker['id'])

    def get_data(self):
        worker_ids = []
        for item in self.worker_list.selectedItems():
            worker_ids.append(item.data(Qt.UserRole))
        
        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "culture": self.culture_combo.currentText(),
            "amount": float(self.amount_edit.text()) if self.amount_edit.text() else 0.0,
            "warehouse_id": self.warehouse_combo.currentData(),
            "worker_ids": worker_ids,
            "notes": self.notes_edit.text()
        }