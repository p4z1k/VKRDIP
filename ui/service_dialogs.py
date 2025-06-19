##ui/service_dialogs.py
import os
import sys
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QTextEdit, QDateEdit, QSpinBox, QPushButton, QMessageBox, QListWidget,
    QListWidgetItem, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QAbstractItemView, QInputDialog
)
from PyQt5.QtCore import Qt, QDate
from document_manager.document_manager import DocumentManagerDialog
class ServiceEventDialog(QDialog):
    def __init__(self, parent=None, db=None, equipment_id=None):
        super().__init__(parent)
        self.db = db
        self.equipment_id = equipment_id
        self.setWindowTitle("Новое событие: Поломка / ТО")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Поломка", "Техническое обслуживание"])
        self.category_combo.currentTextChanged.connect(self.update_form_by_category)
        cat_layout.addWidget(self.category_combo)
        self.layout.addLayout(cat_layout)
        self.breakdown_widget = self.init_breakdown_widget()
        self.maintenance_widget = self.init_maintenance_widget()
        self.layout.addWidget(self.breakdown_widget)
        self.layout.addWidget(self.maintenance_widget)
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)
        self.update_form_by_category(self.category_combo.currentText())

    def init_breakdown_widget(self):
        from PyQt5.QtWidgets import QWidget, QFormLayout
        widget = QWidget()
        form = QFormLayout(widget)
        self.malfunction_type_combo = QComboBox()
        self.load_malfunction_types()
        add_type_btn = QPushButton("Добавить тип неисправности")
        add_type_btn.clicked.connect(self.add_new_malfunction_type)
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.malfunction_type_combo)
        type_layout.addWidget(add_type_btn)
        form.addRow("Тип неисправности:", type_layout)
        self.break_desc = QTextEdit()
        form.addRow("Описание:", self.break_desc)
        self.break_date = QDateEdit(QDate.currentDate())
        self.break_date.setCalendarPopup(True)
        self.break_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Дата обнаружения:", self.break_date)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["срочный", "средний", "низкий"])
        form.addRow("Приоритет:", self.priority_combo)
        return widget

    def init_maintenance_widget(self):
        from PyQt5.QtWidgets import QWidget, QFormLayout
        widget = QWidget()
        form = QFormLayout(widget)
        self.maint_type_combo = QComboBox()
        self.maint_type_combo.addItems(["плановое", "внеплановое", "сезонное"])
        form.addRow("Тип ТО:", self.maint_type_combo)
        self.maint_date = QDateEdit(QDate.currentDate())
        self.maint_date.setCalendarPopup(True)
        self.maint_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Дата проведения:", self.maint_date)
        self.odometer_edit = QLineEdit()
        self.odometer_edit.setPlaceholderText("напр., 12345 км или 250 моточасов")
        form.addRow("Пробег / моточасы:", self.odometer_edit)
        self.service_center_edit = QLineEdit()
        form.addRow("Сервисный центр:", self.service_center_edit)
        self.attach_btn = QPushButton("Прикрепить чек/документ")
        self.attach_btn.clicked.connect(self.attach_maintenance_document)
        self.attached_list = QListWidget()
        form.addRow(self.attach_btn, self.attached_list)
        return widget

    def update_form_by_category(self, text: str):
        if text == "Поломка":
            self.breakdown_widget.show()
            self.maintenance_widget.hide()
        else:
            self.breakdown_widget.hide()
            self.maintenance_widget.show()

    def load_malfunction_types(self):
        self.malfunction_type_combo.clear()
        rows = self.db.fetch_all("SELECT name FROM malfunction_types ORDER BY name")
        for r in rows:
            self.malfunction_type_combo.addItem(r["name"])

    def add_new_malfunction_type(self):
        text, ok = QInputDialog.getText(self, "Новый тип неисправности", "Введите название:")
        if not ok or not text.strip():
            return
        name = text.strip()
        try:
            self.db.execute("INSERT OR IGNORE INTO malfunction_types (name) VALUES (?)", (name,))
            self.load_malfunction_types()
            idx = self.malfunction_type_combo.findText(name)
            if idx >= 0:
                self.malfunction_type_combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить тип: {e}")

    def attach_maintenance_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для прикрепления",
            "",
            "Все файлы (*.*);;PDF (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        fname = os.path.basename(file_path)
        item = QListWidgetItem(fname)
        item.setData(Qt.UserRole, file_path)
        self.attached_list.addItem(item)

    def get_data(self) -> dict:
        res = {}
        cat = self.category_combo.currentText()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if cat == "Поломка":
            res["category"] = "breakdown"
            res["event_type"] = self.malfunction_type_combo.currentText()
            res["description"] = self.break_desc.toPlainText()
            res["date_start"] = self.break_date.date().toString("yyyy-MM-dd")
            res["priority"] = self.priority_combo.currentText()
            res["status"] = "New"
            res["date_end"] = None
            res["responsible_id"] = None
            res["odometer_hours"] = None
            res["service_center"] = None
            res["attached_paths"] = []
        else:
            res["category"] = "maintenance"
            res["event_type"] = self.maint_type_combo.currentText()
            res["description"] = ""  
            res["date_start"] = self.maint_date.date().toString("yyyy-MM-dd")
            res["priority"] = None
            res["status"] = "New"
            res["responsible_id"] = None
            res["date_end"] = None
            res["odometer_hours"] = self.odometer_edit.text().strip()
            res["service_center"] = self.service_center_edit.text().strip()
            paths = []
            for i in range(self.attached_list.count()):
                item = self.attached_list.item(i)
                path = item.data(Qt.UserRole)
                paths.append(path)
            res["attached_paths"] = paths
        return res

    def accept(self):
        data = self.get_data()
        eq_id = self.equipment_id
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if data["category"] == "breakdown":
            query = """
                INSERT INTO equipment_service
                  (equipment_id, event_category, event_type, description, date_start,
                   priority, status, responsible_id, odometer_hours, service_center,
                   created_at, updated_at)
                VALUES (?, 'breakdown', ?, ?, ?, ?, 'New', NULL, NULL, NULL, ?, ?)
            """
            params = (
                eq_id,
                data["event_type"],
                data["description"],
                data["date_start"],
                data["priority"],
                now_ts,
                now_ts
            )
            cur = self.db.execute(query, params)
            service_id = cur.lastrowid
        else:
            query = """
                INSERT INTO equipment_service
                  (equipment_id, event_category, event_type, description, date_start,
                   priority, status, responsible_id, odometer_hours, service_center,
                   created_at, updated_at)
                VALUES (?, 'maintenance', ?, ?, ?, NULL, 'New', NULL, ?, ?, ?, ?)
            """
            params = (
                eq_id,
                data["event_type"],
                "",
                data["date_start"],
                data["odometer_hours"],
                data["service_center"],
                now_ts,
                now_ts
            )
            cur = self.db.execute(query, params)
            service_id = cur.lastrowid
            for path in data["attached_paths"]:
                if not os.path.isfile(path):
                    continue
                fname = os.path.basename(path)
                file_ext = os.path.splitext(fname)[1].lower()
                try:
                    with open(path, "rb") as f:
                        blob = f.read()
                except Exception as e:
                    continue
                file_type = file_ext.lstrip(".").lower()
                self.db.execute(
                    """
                    INSERT INTO equipment_service_documents
                      (service_id, file_name, file_data, file_type, upload_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (service_id, fname, blob, file_type, now_ts)
                )
        super().accept()

class TakeToWorkDialog(QDialog):
    def __init__(self, parent=None, db=None, service_id=None):
        super().__init__(parent)
        self.db = db
        self.service_id = service_id
        self.setWindowTitle("Взять поломку в работу")
        self.setMinimumSize(400, 200)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.worker_combo = QComboBox()
        rows = self.db.fetch_all("SELECT id, name FROM workers ORDER BY name")
        self.workers = rows
        for w in rows:
            self.worker_combo.addItem(w["name"], w["id"])
        self.layout.addWidget(QLabel("Выберите ответственного:"))
        self.layout.addWidget(self.worker_combo)
        btn_layout = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok)
        btn_layout.addWidget(cancel)
        self.layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        rid = self.worker_combo.currentData()
        date_now = QDate.currentDate().toString("yyyy-MM-dd")
        return {"responsible_id": rid, "date_start_work": date_now}

    def accept(self):
        if self.worker_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите ответственного.")
            return
        super().accept()

class FinishRepairDialog(QDialog):
    def __init__(self, parent=None, db=None, service_id=None):
        super().__init__(parent)
        self.db = db
        self.service_id = service_id
        self.setWindowTitle("Завершить ремонт")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Дата окончания:"))
        date_layout.addWidget(self.end_date)
        self.layout.addLayout(date_layout)
        self.finish_desc = QTextEdit()
        self.finish_desc.setPlaceholderText("Описание выполненных работ")
        self.layout.addWidget(QLabel("Описание:"))
        self.layout.addWidget(self.finish_desc)
        self.attach_btn = QPushButton("Прикрепить чек/документ")
        self.attach_btn.clicked.connect(self.attach_file)
        self.attached_list = QListWidget()
        self.layout.addWidget(self.attach_btn)
        self.layout.addWidget(self.attached_list)
        btn_layout = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok)
        btn_layout.addWidget(cancel)
        self.layout.addLayout(btn_layout)

    def attach_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для прикрепления",
            "",
            "Все файлы (*.*);;PDF (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.UserRole, file_path)
        self.attached_list.addItem(item)

    def get_data(self) -> dict:
        """
        Возвращает:
          {
            'date_end': <yyyy-MM-dd>,
            'finish_description': <text>,
            'attached_paths': [<file_path1>, <file_path2>, ...]
          }
        """
        res = {
            'date_end': self.end_date.date().toString("yyyy-MM-dd"),
            'finish_description': self.finish_desc.toPlainText().strip(),
            'attached_paths': []
        }
        for i in range(self.attached_list.count()):
            item = self.attached_list.item(i)
            path = item.data(Qt.UserRole)
            res['attached_paths'].append(path)
        return res

    def accept(self):
        if not self.end_date.date().isValid():
            QMessageBox.warning(self, "Ошибка", "Неверная дата.")
            return
        super().accept()
