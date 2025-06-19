##ui/workers_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLabel, QLineEdit, QComboBox, QTextEdit,QSpacerItem,
    QFileDialog, QMessageBox, QHeaderView, QAbstractItemView, QDateEdit,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
class WorkerDialog(QDialog):
    def __init__(self, db, parent=None, worker=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить работника" if worker is None else "Редактировать работника")
        self.db = db
        self.worker = worker or {}
        self.photo_bytes = None
        self.init_ui()
        if worker:
            self.load_data(worker)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        row = 0
        grid.addWidget(QLabel("ФИО:"), row, 0, Qt.AlignRight)
        self.name_edit = QLineEdit()
        grid.addWidget(self.name_edit, row, 1)
        grid.addWidget(QLabel("Должность:"), row+1, 0, Qt.AlignRight)
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "Тракторист", "Агроном", "Разнорабочий", "Бригадир", "Водитель", "Механик", "Другое"
        ])
        grid.addWidget(self.position_combo, row+1, 1)
        grid.addWidget(QLabel("Контакты:"), row+2, 0, Qt.AlignRight)
        self.contacts_edit = QLineEdit()
        grid.addWidget(self.contacts_edit, row+2, 1)
        grid.addWidget(QLabel("Дата приёма:"), row+3, 0, Qt.AlignRight)
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        grid.addWidget(self.hire_date_edit, row+3, 1)
        grid.addWidget(QLabel("Дата окончания:"), row+4, 0, Qt.AlignRight)
        self.fire_date_edit = QDateEdit()
        self.fire_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.fire_date_edit.setCalendarPopup(True)
        self.fire_date_edit.setSpecialValueText("Не указано")
        self.fire_date_edit.setDate(QDate(2000, 1, 1))
        grid.addWidget(self.fire_date_edit, row+4, 1)
        grid.addWidget(QLabel("Статус:"), row+5, 0, Qt.AlignRight)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Активен", "Уволен", "В отпуске", "На больничном"])
        grid.addWidget(self.status_combo, row+5, 1)
        grid.addWidget(QLabel("Дата добавления:"), row+6, 0, Qt.AlignRight)
        self.date_added_edit = QDateEdit()
        self.date_added_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_added_edit.setCalendarPopup(True)
        self.date_added_edit.setDate(QDate.currentDate())
        grid.addWidget(self.date_added_edit, row+6, 1)
        col2 = 2
        grid.addWidget(QLabel("Фото:"), row, col2, Qt.AlignRight)
        v_photo = QVBoxLayout()
        self.photo_label = QLabel("Нет фото")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(120, 120)
        self.load_photo_btn = QPushButton("Загрузить фото")
        self.load_photo_btn.clicked.connect(self.load_photo)
        v_photo.addWidget(self.photo_label)
        v_photo.addWidget(self.load_photo_btn)
        grid.addLayout(v_photo, row, col2+1, 2, 1)
        grid.addWidget(QLabel("Закреплённая техника:"), row+2, col2, Qt.AlignRight)
        self.equipment_list = QListWidget()
        self.equipment_list.setSelectionMode(QListWidget.MultiSelection)
        for eq in self.db.fetch_all("SELECT name FROM equipment ORDER BY name"):
            item = QListWidgetItem(eq["name"])
            self.equipment_list.addItem(item)
        grid.addWidget(self.equipment_list, row+2, col2+1)
        grid.addWidget(QLabel("Закреплённые участки:"), row+3, col2, Qt.AlignRight)
        self.plots_list = QListWidget()
        self.plots_list.setSelectionMode(QListWidget.MultiSelection)
        for p in self.db.fetch_all("SELECT name FROM plots ORDER BY name"):
            item = QListWidgetItem(p["name"])
            self.plots_list.addItem(item)
        grid.addWidget(self.plots_list, row+3, col2+1)
        grid.addWidget(QLabel("Доступ к складам:"), row+4, col2, Qt.AlignRight)
        self.warehouse_list = QListWidget()
        self.warehouse_list.setSelectionMode(QListWidget.MultiSelection)
        for w in self.db.fetch_all("SELECT name FROM warehouses ORDER BY name"):
            item = QListWidgetItem(w["name"])
            self.warehouse_list.addItem(item)
        grid.addWidget(self.warehouse_list, row+4, col2+1)
        grid.addWidget(QLabel("Оклад/ставка:"), row+5, col2, Qt.AlignRight)
        salary_row = QHBoxLayout()
        self.salary_edit = QDoubleSpinBox()
        self.salary_edit.setRange(0, 1000000)
        self.salary_edit.setDecimals(2)
        self.salary_type_combo = QComboBox()
        self.salary_type_combo.addItems(["час", "день", "месяц"])
        salary_row.addWidget(self.salary_edit)
        salary_row.addWidget(self.salary_type_combo)
        grid.addLayout(salary_row, row+5, col2+1)
        grid.addWidget(QLabel("Реквизиты для выплат:"), row+6, col2, Qt.AlignRight)
        self.payment_info_edit = QLineEdit()
        grid.addWidget(self.payment_info_edit, row+6, col2+1)
        grid.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding), row+7, 0, 1, 4)
        main_layout.addLayout(grid)
        main_layout.addWidget(QLabel("Комментарии:"))
        self.comment_edit = QTextEdit()
        main_layout.addWidget(self.comment_edit)
        btns = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        main_layout.addLayout(btns)

    def load_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выбрать фото", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            pixmap = QPixmap(file_name).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(pixmap)
            with open(file_name, 'rb') as f:
                self.photo_bytes = f.read()

    def load_data(self, worker):
        self.name_edit.setText(worker.get("name", ""))
        idx = self.position_combo.findText(worker.get("position", ""), Qt.MatchExactly)
        self.position_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.contacts_edit.setText(worker.get("contacts", ""))
        if worker.get("photo"):
            pixmap = QPixmap()
            pixmap.loadFromData(worker["photo"])
            self.photo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.photo_bytes = worker["photo"]
        if worker.get("hire_date"):
            self.hire_date_edit.setDate(QDate.fromString(worker["hire_date"], "yyyy-MM-dd"))
        if worker.get("fire_date"):
            self.fire_date_edit.setDate(QDate.fromString(worker["fire_date"], "yyyy-MM-dd"))
        eq_set = set((worker.get("equipment") or "").split(", "))
        for i in range(self.equipment_list.count()):
            item = self.equipment_list.item(i)
            if item.text() in eq_set:
                item.setSelected(True)
        pl_set = set((worker.get("plots") or "").split(", "))
        for i in range(self.plots_list.count()):
            item = self.plots_list.item(i)
            if item.text() in pl_set:
                item.setSelected(True)
        wh_set = set((worker.get("warehouse_access") or "").split(", "))
        for i in range(self.warehouse_list.count()):
            item = self.warehouse_list.item(i)
            if item.text() in wh_set:
                item.setSelected(True)
        if worker.get("salary") is not None:
            self.salary_edit.setValue(float(worker["salary"]))
        idx = self.salary_type_combo.findText(worker.get("salary_type", ""), Qt.MatchExactly)
        self.salary_type_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.payment_info_edit.setText(worker.get("payment_info", ""))
        idx = self.status_combo.findText(worker.get("status", ""), Qt.MatchExactly)
        self.status_combo.setCurrentIndex(idx if idx >= 0 else 0)
        if worker.get("date_added"):
            self.date_added_edit.setDate(QDate.fromString(worker["date_added"], "yyyy-MM-dd"))
        self.comment_edit.setText(worker.get("comment", ""))

    def get_data(self):
        equipment = [self.equipment_list.item(i).text()
                     for i in range(self.equipment_list.count())
                     if self.equipment_list.item(i).isSelected()]
        plots = [self.plots_list.item(i).text()
                 for i in range(self.plots_list.count())
                 if self.plots_list.item(i).isSelected()]
        warehouses = [self.warehouse_list.item(i).text()
                      for i in range(self.warehouse_list.count())
                      if self.warehouse_list.item(i).isSelected()]
        return {
            "name": self.name_edit.text().strip(),
            "position": self.position_combo.currentText(),
            "contacts": self.contacts_edit.text().strip(),
            "photo": self.photo_bytes,
            "hire_date": self.hire_date_edit.date().toString("yyyy-MM-dd"),
            "fire_date": self.fire_date_edit.date().toString("yyyy-MM-dd"),
            "equipment": ", ".join(equipment),
            "plots": ", ".join(plots),
            "warehouse_access": ", ".join(warehouses),
            "salary": self.salary_edit.value(),
            "salary_type": self.salary_type_combo.currentText(),
            "payment_info": self.payment_info_edit.text().strip(),
            "status": self.status_combo.currentText(),
            "date_added": self.date_added_edit.date().toString("yyyy-MM-dd"),
            "comment": self.comment_edit.toPlainText().strip()
        }

class WorkersTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.update_workers_table()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.workers_table = QTableWidget()
        self.workers_table.setColumnCount(8)
        self.workers_table.setHorizontalHeaderLabels([
            "ФИО", "Должность", "Контакты", "Фото", "Дата приема", "Статус", "Техника/Участки", "Действия"
        ])
        self.workers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.workers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.workers_table.verticalHeader().setDefaultSectionSize(160)
        layout.addWidget(self.workers_table)
        btns = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_worker)
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_worker)
        del_btn = QPushButton("Удалить")
        del_btn.clicked.connect(self.delete_worker)
        btns.addWidget(add_btn)
        btns.addWidget(edit_btn)
        btns.addWidget(del_btn)
        btns.addStretch()
        layout.addLayout(btns)

    def update_workers_table(self):
        workers = self.db.fetch_all("SELECT * FROM workers ORDER BY name")
        self.workers_table.setRowCount(len(workers))
        for row, w in enumerate(workers):
            self.workers_table.setItem(row, 0, QTableWidgetItem(w.get("name", "")))
            self.workers_table.setItem(row, 1, QTableWidgetItem(w.get("position", "")))
            self.workers_table.setItem(row, 2, QTableWidgetItem(w.get("contacts", "")))
            photo_item = QLabel()
            photo_item.setAlignment(Qt.AlignCenter)
            if w.get("photo"):
                pixmap = QPixmap()
                pixmap.loadFromData(w["photo"])
                w_col = self.workers_table.columnWidth(3) or 160
                h_row = self.workers_table.verticalHeader().sectionSize(row) or 160
                pixmap = pixmap.scaled(w_col, h_row, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                photo_item.setPixmap(pixmap)
            self.workers_table.setCellWidget(row, 3, photo_item)
            self.workers_table.setItem(row, 4, QTableWidgetItem(w.get("hire_date", "")))
            self.workers_table.setItem(row, 5, QTableWidgetItem(w.get("status", "")))
            summary = []
            if w.get("equipment"):
                summary.append("Техника: " + w["equipment"])
            if w.get("plots"):
                summary.append("Участки: " + w["plots"])
            if w.get("warehouse_access"):
                summary.append("Склады: " + w["warehouse_access"])
            self.workers_table.setItem(row, 6, QTableWidgetItem("; ".join(summary)))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton("✏️")
            edit_btn.clicked.connect(self.create_edit_worker_handler(w))
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(self.create_delete_worker_handler(w))
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_widget.setLayout(action_layout)
            self.workers_table.setCellWidget(row, 7, action_widget)

    def create_edit_worker_handler(self, worker):
        def handler():
            self.edit_worker(worker)
        return handler

    def create_delete_worker_handler(self, worker):
        def handler():
            self.delete_worker(worker)
        return handler

    def add_worker(self):
        dialog = WorkerDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.execute(
                "INSERT INTO workers "
                "(name, position, contacts, photo, hire_date, fire_date, equipment, plots, warehouse_access, "
                "salary, salary_type, payment_info, status, date_added, comment) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    data["name"], data["position"], data["contacts"], data["photo"],
                    data["hire_date"], data["fire_date"], data["equipment"], data["plots"], data["warehouse_access"],
                    data["salary"], data["salary_type"], data["payment_info"], data["status"], data["date_added"], data["comment"]
                )
            )
            self.update_workers_table()

    def edit_worker(self, worker=None):
        row = self.workers_table.currentRow()
        if worker is None:
            if row < 0:
                return
            worker = self.db.fetch_one("SELECT * FROM workers ORDER BY name LIMIT 1 OFFSET ?", (row,))
        dialog = WorkerDialog(self.db, self, worker)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.execute(
                "UPDATE workers SET "
                "name=?, position=?, contacts=?, photo=?, hire_date=?, fire_date=?, equipment=?, plots=?, warehouse_access=?, "
                "salary=?, salary_type=?, payment_info=?, status=?, date_added=?, comment=? WHERE id=?",
                (
                    data["name"], data["position"], data["contacts"], data["photo"],
                    data["hire_date"], data["fire_date"], data["equipment"], data["plots"], data["warehouse_access"],
                    data["salary"], data["salary_type"], data["payment_info"], data["status"], data["date_added"], data["comment"], worker["id"]
                )
            )
            self.update_workers_table()

    def delete_worker(self, worker=None):
        row = self.workers_table.currentRow()
        if worker is None:
            if row < 0:
                return
            worker = self.db.fetch_one("SELECT * FROM workers ORDER BY name LIMIT 1 OFFSET ?", (row,))
        if QMessageBox.question(self, "Удалить работника?", f"Удалить работника '{worker['name']}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute("DELETE FROM workers WHERE id=?", (worker["id"],))
            self.update_workers_table()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_workers_table()
