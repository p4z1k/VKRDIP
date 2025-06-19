# ui/field_work_wizard.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QDoubleSpinBox, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from document_manager.document_manager import DocumentManagerDialog

class FieldWorkWizard(QDialog):
    CATEGORIES = {
        "Подготовка почвы": ["Вспашка", "Боронование", "Культивация", "Известкование"],
        "Посевные работы": ["Посев", "Подсев"],
        "Уход за посевами": ["Прополка", "Окучивание", "Подкормка", "Полив"],
        "Защита растений": ["Обработка гербицидами", "Обработка инсектицидами", "Обработка фунгицидами"],
        "Уборка урожая": ["Комбайнирование", "Ручной сбор", "Транспортировка"],
        "Послеуборочная обработка": ["Уборка остатков", "Внесение удобрений", "Подготовка к зиме"],
        "Отдых": ["Отдых"]
    }
    def __init__(self, db, plot, task_id=None, mode="create", parent=None):
        super().__init__(parent)
        self.db = db
        self.plot = plot            
        self.task_id = task_id
        self.mode = mode            
        self.setWindowTitle("Работа с участком")
        self.resize(500, 350)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        if self.mode == "create":
            self.add_create_fields()
        elif self.mode == "inprogress":
            self.add_inprogress_fields()
        elif self.mode == "finish":
            self.add_finish_fields()
        btn_row = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.handle_accept)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_row)

    def add_create_fields(self):
        self.layout.addWidget(QLabel("Запланированная дата:"))
        self.plan_date = QDateEdit(QDate.currentDate())
        self.plan_date.setCalendarPopup(True)
        self.plan_date.setDisplayFormat("yyyy-MM-dd")
        self.layout.addWidget(self.plan_date)
        self.layout.addWidget(QLabel("Категория:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.CATEGORIES.keys()))
        self.category_combo.currentTextChanged.connect(self.update_types)
        self.layout.addWidget(self.category_combo)
        self.layout.addWidget(QLabel("Тип работы:"))
        self.type_combo = QComboBox()
        self.update_types()
        self.layout.addWidget(self.type_combo)
        self.layout.addWidget(QLabel("Описание:"))
        self.desc_edit = QLineEdit()
        self.layout.addWidget(self.desc_edit)
        self.layout.addWidget(QLabel("Комментарий:"))
        self.comment_edit = QTextEdit()
        self.layout.addWidget(self.comment_edit)

    def handle_accept(self):
        if self.mode == "create":
            plan_date = self.plan_date.date().toString("yyyy-MM-dd")
            category = self.category_combo.currentText()
            task_type = self.type_combo.currentText()
            description = self.desc_edit.text()
            comment = self.comment_edit.toPlainText()
            cur = self.db.execute(
                """
                INSERT INTO field_tasks
                   (field_id, category, task_type, status, plan_date, description, comment)
                VALUES (?, ?, ?, 'запланирована', ?, ?, ?)
                """,
                (
                    self.plot["id"],
                    category,
                    task_type,
                    plan_date,
                    description,
                    comment
                )
            )
            task_id = cur.lastrowid
            dlg = DocumentManagerDialog(self, item_id=task_id, db_manager=self.db,
                                       table_name="field_task_documents", id_field="task_id")
            dlg.exec_()
            self.accept()
            return

    def add_inprogress_fields(self):
        task = self.db.fetch_one("SELECT * FROM field_tasks WHERE id=?", (self.task_id,))
        if not task:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти задачу в базе.")
            self.reject()
            return
        self.layout.addWidget(QLabel(f"<b>{task['category']}: {task['task_type']}</b>"))
        self.layout.addWidget(QLabel(f"Описание: {task.get('description','')}"))
        cat = task.get("category", "").strip()
        typ = task.get("task_type", "").strip()
        if (cat == "Защита растений") or (cat == "Послеуборочная обработка" and typ == "Внесение удобрений"):
            from .warehouse_dialogs import AddToWarehouseDialog
            existing_resp = task.get("responsible_ids", "")
            wh_id = task.get("warehouse_id")
            wh = None
            if wh_id:
                wh = self.db.fetch_one("SELECT * FROM warehouses WHERE id=?", (wh_id,))
            dlg = AddToWarehouseDialog(self.db, wh, 'fertilizer_out', parent=self)
            dlg.date_edit.setDate(QDate.currentDate())
            if existing_resp:
                for rid in existing_resp.split(","):
                    for i in range(dlg.resp_list.count()):
                        item = dlg.resp_list.item(i)
                        if str(item.data(Qt.UserRole)) == rid:
                            item.setSelected(True)
            for i in range(dlg.plot_combo.count()):
                if dlg.plot_combo.itemData(i) == self.plot["id"]:
                    dlg.plot_combo.setCurrentIndex(i)
                    break
            if wh:
                for i in range(dlg.wh_combo.count()):
                    if dlg.wh_combo.itemData(i) == wh["id"]:
                        dlg.wh_combo.setCurrentIndex(i)
                        break
            if dlg.exec_() == QDialog.Accepted:
                data = dlg.get_data()
                if not data:
                    QMessageBox.warning(self, "Ошибка", "Не получены данные для операции со складом.")
                    return
                self.db.execute(
                    """
                    INSERT INTO warehouse_operations
                      (warehouse_id, operation_type, object_type, object_id, date,
                       responsible_ids, quantity, unit, reason, comment, document, plot_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["warehouse_id"],
                        "outgoing",
                        "fertilizer",
                        data["object_id"],
                        data["date"],
                        data["responsible_ids"],
                        data["quantity"],
                        data["unit"],
                        data.get("reason", ""),
                        data.get("comment", ""),
                        data.get("document", None),
                        data["plot_id"]
                    )
                )
                start_date = QDate.currentDate().toString("yyyy-MM-dd")
                self.db.execute(
                    """
                    UPDATE field_tasks SET
                       status='в процессе',
                       start_date=?,
                       responsible_ids=?,
                       warehouse_id=?,
                       fertilizer_id=?
                    WHERE id=?
                    """,
                    (
                        start_date,
                        existing_resp,
                        data["warehouse_id"],
                        data["object_id"],
                        self.task_id
                    )
                )
                self.accept()
            else:
                self.reject()
            return
        self.layout.addWidget(QLabel("Выбор ответственных:"))
        self.workers_list = QListWidget()
        self.workers_list.setSelectionMode(QListWidget.MultiSelection)
        for w in self.db.fetch_all("SELECT id, name FROM workers ORDER BY name"):
            item = QListWidgetItem(w["name"])
            item.setData(Qt.UserRole, w["id"])
            self.workers_list.addItem(item)
        self.layout.addWidget(self.workers_list)
        self.layout.addWidget(QLabel("Выбор техники:"))
        self.equip_list = QListWidget()
        self.equip_list.setSelectionMode(QListWidget.MultiSelection)
        for e in self.db.fetch_all("SELECT id, name FROM equipment ORDER BY name"):
            item = QListWidgetItem(e["name"])
            item.setData(Qt.UserRole, e["id"])
            self.equip_list.addItem(item)
        self.layout.addWidget(self.equip_list)
        self.layout.addWidget(QLabel("Дата начала выполнения:"))
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.layout.addWidget(self.start_date)
        if task["category"] == "Посевные работы":
            self.layout.addWidget(QLabel("Склад:"))
            self.warehouse_combo = QComboBox()
            whs = self.db.fetch_all(
                "SELECT * FROM warehouses WHERE warehouse_type IN ('Зернохранилище', 'Овощехранилище')"
            )
            self.wh_list = whs
            self.warehouse_combo.addItems([w["name"] for w in whs])
            self.layout.addWidget(self.warehouse_combo)
            self.layout.addWidget(QLabel("Культура:"))
            self.crop_combo = QComboBox()
            self.layout.addWidget(self.crop_combo)
            self.warehouse_combo.currentIndexChanged.connect(self.update_crops)
            self.update_crops()
            self.layout.addWidget(QLabel("Количество:"))
            self.qty_edit = QDoubleSpinBox()
            self.qty_edit.setRange(0, 1_000_000)
            self.qty_edit.setDecimals(2)
            self.layout.addWidget(self.qty_edit)
            self.layout.addWidget(QLabel("Ед.:"))
            self.unit_combo = QComboBox()
            self.unit_combo.addItems(["т", "м³", "бушели", "мешки", "ящики", "шт."])
            self.layout.addWidget(self.unit_combo)

    def add_finish_fields(self):
        task = self.db.fetch_one("SELECT * FROM field_tasks WHERE id=?", (self.task_id,))
        if not task:
            QMessageBox.critical(self, "Ошибка", "Не удалось найти задачу в базе.")
            self.reject()
            return
        self.layout.addWidget(QLabel(f"<b>{task['category']}: {task['task_type']}</b>"))
        self.layout.addWidget(QLabel(f"Описание: {task.get('description','')}"))
        self.layout.addWidget(QLabel("Дата завершения:"))
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.layout.addWidget(self.end_date)
        if task["category"] == "Уборка урожая" and "Транспортировка" in task["task_type"]:
            self.layout.addWidget(QLabel("После ОК откроется окно «Добавить культуру на склад»."))

    def update_types(self):
        cat = self.category_combo.currentText()
        self.type_combo.clear()
        self.type_combo.addItems(self.CATEGORIES.get(cat, []))

    def update_crops(self):
        wh_idx = self.warehouse_combo.currentIndex()
        if wh_idx < 0:
            return
        wh_id = self.wh_list[wh_idx]["id"]
        stocks = self.db.fetch_all("""
            SELECT crops.name FROM warehouse_operations
            JOIN crops ON crops.id = warehouse_operations.object_id
            WHERE warehouse_id=? AND object_type='crop' AND quantity>0
            GROUP BY crops.name
        """, (wh_id,))
        self.crop_combo.clear()
        self.crop_combo.addItems([s["name"] for s in stocks])

    def handle_accept(self):
        if self.mode == "create":
            plan_date = self.plan_date.date().toString("yyyy-MM-dd")
            category = self.category_combo.currentText()
            task_type = self.type_combo.currentText()
            description = self.desc_edit.text()
            comment = self.comment_edit.toPlainText()
            self.db.execute(
                """
                INSERT INTO field_tasks
                   (field_id, category, task_type, status, plan_date, description, comment)
                VALUES (?, ?, ?, 'запланирована', ?, ?, ?)
                """,
                (
                    self.plot["id"],
                    category,
                    task_type,
                    plan_date,
                    description,
                    comment
                )
            )
            self.accept()
            return
        if self.mode == "inprogress":
            task = self.db.fetch_one("SELECT * FROM field_tasks WHERE id=?", (self.task_id,))
            if not task:
                QMessageBox.critical(self, "Ошибка", "Не удалось найти задачу в базе.")
                self.reject()
                return
            if task["status"] == "в процессе":
                return
            resp_ids = [
                str(self.workers_list.item(i).data(Qt.UserRole))
                for i in range(self.workers_list.count())
                if self.workers_list.item(i).isSelected()
            ]
            equip_ids = [
                str(self.equip_list.item(i).data(Qt.UserRole))
                for i in range(self.equip_list.count())
                if self.equip_list.item(i).isSelected()
            ]
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            crop_id = None
            warehouse_id = None
            qty = None
            unit = None
            if task["category"] == "Посевные работы":
                wh_idx = self.warehouse_combo.currentIndex()
                warehouse_id = self.wh_list[wh_idx]["id"]
                crop_name = self.crop_combo.currentText()
                cr = self.db.fetch_one("SELECT id FROM crops WHERE name=?", (crop_name,))
                crop_id = cr["id"] if cr else None
                qty = self.qty_edit.value()
                unit = self.unit_combo.currentText()
                self.db.execute(
                    """
                    INSERT INTO warehouse_operations
                      (warehouse_id, operation_type, object_type, object_id, date, quantity, unit, plot_id)
                    VALUES (?, 'outgoing', 'crop', ?, ?, ?, ?, ?)
                    """,
                    (warehouse_id, crop_id, start_date, qty, unit, self.plot["id"])
                )
            self.db.execute(
                """
                UPDATE field_tasks SET
                   status='в процессе',
                   start_date=?,
                   responsible_ids=?,
                   equipment_ids=?,
                   warehouse_id=?,
                   crop_id=?, qty=?, unit=?
                WHERE id=?
                """,
                (
                    start_date,
                    ",".join(resp_ids),
                    ",".join(equip_ids),
                    warehouse_id,
                    crop_id,
                    qty,
                    unit,
                    self.task_id
                )
            )
            self.accept()
            return
        if self.mode == "finish":
            task = self.db.fetch_one("SELECT * FROM field_tasks WHERE id=?", (self.task_id,))
            if not task:
                QMessageBox.critical(self, "Ошибка", "Не удалось найти задачу в базе.")
                self.reject()
                return
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            if task["category"] == "Уборка урожая" and "Транспортировка" in task["task_type"]:
                from .warehouse_dialogs import AddToWarehouseDialog
                self.db.execute("UPDATE field_tasks SET status='в процессе' WHERE id=?", (self.task_id,))
                existing_resp = task.get("responsible_ids", "")
                wh_id = task.get("warehouse_id")
                wh = None
                if wh_id:
                    wh = self.db.fetch_one("SELECT * FROM warehouses WHERE id=?", (wh_id,))
                dlg = AddToWarehouseDialog(self.db, wh, 'crop_in', parent=self, field_id=self.plot['id'])
                dlg.date_edit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
                if existing_resp:
                    for rid in existing_resp.split(","):
                        for i in range(dlg.resp_list.count()):
                            item = dlg.resp_list.item(i)
                            if str(item.data(Qt.UserRole)) == rid:
                                item.setSelected(True)
                for i in range(dlg.plot_combo.count()):
                    if dlg.plot_combo.itemData(i) == self.plot["id"]:
                        dlg.plot_combo.setCurrentIndex(i)
                        break
                if task.get("crop_id"):
                    cr = self.db.fetch_one("SELECT name FROM crops WHERE id=?", (task["crop_id"],))
                    if cr:
                        cname = cr["name"]
                        idx = dlg.obj_combo.findText(cname)
                        if idx >= 0:
                            dlg.obj_combo.setCurrentIndex(idx)
                if wh:
                    for i in range(dlg.wh_combo.count()):
                        if dlg.wh_combo.itemData(i) == wh["id"]:
                            dlg.wh_combo.setCurrentIndex(i)
                            break
                if dlg.exec_() == QDialog.Accepted:
                    data = dlg.get_data()
                    if not data:
                        QMessageBox.warning(self, "Ошибка", "Не получены данные для операции со складом.")
                        return
                    self.db.execute(
                        """
                        INSERT INTO warehouse_operations
                          (warehouse_id, operation_type, object_type, object_id, date,
                           responsible_ids, quantity, unit, reason, comment, document, plot_id)
                        VALUES (?, 'incoming', 'crop', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            data["warehouse_id"],
                            data["object_id"],
                            data["date"],
                            data["responsible_ids"],
                            data["quantity"],
                            data["unit"],
                            data.get("reason", ""),
                            data.get("comment", ""),
                            data.get("document", None),
                            data["plot_id"]
                        )
                    )
                    cr = self.db.fetch_one("SELECT name FROM crops WHERE id=?", (data["object_id"],))
                    culture_name = cr["name"] if cr else ""
                    self.db.execute(
                        """
                        INSERT INTO harvests
                          (plot_id, date, culture, amount)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            self.plot["id"],
                            data["date"],
                            culture_name,
                            data["quantity"]
                        )
                    )
                    self.db.execute(
                        "UPDATE field_tasks SET status='завершена', end_date=? WHERE id=?",
                        (end_date, self.task_id)
                    )
                self.accept()
                return
            self.db.execute(
                "UPDATE field_tasks SET status='завершена', end_date=? WHERE id=?",
                (end_date, self.task_id)
            )
            self.accept()

    def get_plot_status(self, category: str, task_type: str) -> str:
        cat = category.lower()
        typ = task_type.lower()
        if cat == "подготовка почвы":
            if typ == "вспашка":
                return "вспахано"
            if typ == "культивация":
                return "культивировано"
            return "подготовлено"
        if cat == "посевные работы":
            return "засеяно"
        if cat == "защита растений":
            return "обработано"
        if cat == "уборка урожая":
            return "убрано"
        if cat == "уход за посевами":
            return "уход"
        if cat == "послеуборочная обработка":
            return "обработано после уборки"
        return "обработано"