##ui/field_work_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox, QLineEdit, QHeaderView,
    QSizePolicy, QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from document_manager.document_manager import DocumentManagerDialog
FIELD_CATEGORIES = {
    "Подготовка почвы": ["Вспашка", "Боронование", "Культивация", "Известкование"],
    "Посевные работы": ["Посев", "Подсев"],
    "Уход за посевами": ["Прополка", "Окучивание", "Подкормка", "Полив"],
    "Защита растений": ["Обработка гербицидами", "Обработка инсектицидами", "Обработка фунгицидами"],
    "Уборка урожая": ["Комбайнирование", "Ручной сбор", "Транспортировка"],
    "Послеуборочная обработка": ["Уборка остатков", "Внесение удобрений", "Подготовка к зиме"],
    "Отдых": ["Отдых"]
}
CATEGORY_STATUS = {
    "Посевные работы": "Засеяно",
    "Подготовка почвы": "Вспахано",
    "Уборка урожая": "Готово к уборке",
    "Послеуборочная обработка": "Обработано",
    "Уход за посевами": "В процессе ухода",
    "Защита растений": "Обработано",
    "Отдых": "Свободно"
}

class FieldWorkTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_plot = None
        self.selected_task = None
        self.init_ui()
        self.load_plots()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QVBoxLayout()
        top_layout.addWidget(QLabel("<b>Участки</b>"))
        self.plots_table = QTableWidget()
        self.plots_table.setColumnCount(4)
        self.plots_table.setHorizontalHeaderLabels(["Название", "Площадь, га", "Чем засеяно", "Статус"])
        self.plots_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.plots_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.plots_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.plots_table.setMaximumHeight(130)
        self.plots_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.plots_table.cellClicked.connect(self.on_plot_select)
        top_layout.addWidget(self.plots_table)
        self.plot_info = QLabel("Выберите участок")
        top_layout.addWidget(self.plot_info)
        main_layout.addLayout(top_layout)
        btn_row = QHBoxLayout()
        self.add_task_btn = QPushButton("Добавить работу")
        self.start_task_btn = QPushButton("Взять в работу")
        self.finish_task_btn = QPushButton("Завершить работу")
        self.refresh_btn = QPushButton("Обновить")
        btn_row.addWidget(self.add_task_btn)
        btn_row.addWidget(self.start_task_btn)
        btn_row.addWidget(self.finish_task_btn)
        btn_row.addWidget(self.refresh_btn)
        main_layout.addLayout(btn_row)
        self.add_task_btn.clicked.connect(self.show_create_task_form)
        self.start_task_btn.clicked.connect(self.show_start_task_form)
        self.finish_task_btn.clicked.connect(self.show_finish_task_form)
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        main_layout.addWidget(QLabel("<b>Текущие работы</b>"))
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(9)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "Категория", "Тип", "Статус", "План дата", "Старт", "Техника", "Ответственные", "Документы"
        ])
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setMinimumHeight(100)
        self.tasks_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tasks_table.cellClicked.connect(self.on_task_select)
        main_layout.addWidget(self.tasks_table, stretch=2)
        self.work_form_group = QGroupBox("Работа с задачей")
        self.work_form_layout = QVBoxLayout(self.work_form_group)
        self.work_form_group.hide()
        main_layout.addWidget(self.work_form_group, stretch=0)
        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Поиск по названию, культуре, статусу, работнику или технике")
        self.search_date_from = QDateEdit()
        self.search_date_from.setDisplayFormat("yyyy-MM-dd")
        self.search_date_from.setCalendarPopup(True)
        self.search_date_from.setDate(QDate(2000,1,1))
        self.search_date_to = QDateEdit()
        self.search_date_to.setDisplayFormat("yyyy-MM-dd")
        self.search_date_to.setCalendarPopup(True)
        self.search_date_to.setDate(QDate.currentDate())
        search_row.addWidget(QLabel("C:"))
        search_row.addWidget(self.search_date_from)
        search_row.addWidget(QLabel("По:"))
        search_row.addWidget(self.search_date_to)
        search_row.addWidget(self.search_field)
        search_btn = QPushButton("Поиск")
        search_row.addWidget(search_btn)
        main_layout.addLayout(search_row)
        main_layout.addWidget(QLabel("<b>История работ</b>"))
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(10)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Категория", "Тип", "Статус", "План дата", "Старт", "Завершено", "Техника", "Ответственные", "Документы"
        ])
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSortingEnabled(True)
        self.history_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.history_table, stretch=5)
        self.setLayout(main_layout)
        search_btn.clicked.connect(self.refresh_history)
        self.search_field.returnPressed.connect(self.refresh_history)
        self.search_date_from.dateChanged.connect(self.refresh_history)
        self.search_date_to.dateChanged.connect(self.refresh_history)

    def load_plots(self):
        plots = self.db.fetch_all("SELECT * FROM plots ORDER BY name")
        self.plots_table.setRowCount(len(plots))
        for i, p in enumerate(plots):
            self.plots_table.setItem(i, 0, QTableWidgetItem(p["name"]))
            self.plots_table.setItem(i, 1, QTableWidgetItem(str(p["area"])))
            self.plots_table.setItem(i, 2, QTableWidgetItem(str(p.get("crop", "Не засеяно"))))
            self.plots_table.setItem(i, 3, QTableWidgetItem(str(p.get("status", "Не задан"))))
        if plots:
            self.on_plot_select(0, 0)

    def on_plot_select(self, row, _):
        item = self.plots_table.item(row, 0)
        if not item:
            self.selected_plot = None
            self.plot_info.setText("Выберите участок")
            self.tasks_table.setRowCount(0)
            self.history_table.setRowCount(0)
            return
        pid = item.text()
        self.selected_plot = self.db.fetch_one("SELECT * FROM plots WHERE name=?", (pid,))
        if not self.selected_plot:
            self.plot_info.setText("Участок не найден в базе")
            self.tasks_table.setRowCount(0)
            self.history_table.setRowCount(0)
            return
        status = self.selected_plot.get('status', 'Не задан')
        crop = self.selected_plot.get('crop', 'Не засеяно')
        self.plot_info.setText(
            f"<b>Участок:</b> {self.selected_plot['name']}, {self.selected_plot['area']} га<br>"
            f"<b>Статус:</b> {status} | <b>Культура:</b> {crop}"
        )
        self.refresh_tasks()
        self.refresh_history()

    def refresh_tasks(self):
        if not self.selected_plot:
            self.tasks_table.setRowCount(0)
            return
        plot_id = self.selected_plot["id"]
        tasks = self.db.fetch_all(
            "SELECT * FROM field_tasks WHERE field_id=? AND status != 'завершена' ORDER BY plan_date DESC, id DESC",
            (plot_id,)
        )
        self.tasks_table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.tasks_table.setItem(i, 0, QTableWidgetItem(str(t["id"])))
            self.tasks_table.setItem(i, 1, QTableWidgetItem(t["category"]))
            self.tasks_table.setItem(i, 2, QTableWidgetItem(t["task_type"]))
            self.tasks_table.setItem(i, 3, QTableWidgetItem(t["status"]))
            self.tasks_table.setItem(i, 4, QTableWidgetItem(str(t.get("plan_date") or "")))
            self.tasks_table.setItem(i, 5, QTableWidgetItem(str(t.get("start_date") or "")))
            tech_txt = ""
            if t.get("equipment_ids"):
                ids = t["equipment_ids"].split(",")
                techs = []
                for eid in ids:
                    if eid:
                        eq = self.db.fetch_one("SELECT name FROM equipment WHERE id=?", (eid,))
                        if eq:
                            techs.append(eq["name"])
                tech_txt = ", ".join(techs)
            self.tasks_table.setItem(i, 6, QTableWidgetItem(tech_txt))
            resp_txt = ""
            if t.get("responsible_ids"):
                ids = t["responsible_ids"].split(",")
                resps = []
                for rid in ids:
                    if rid:
                        wrk = self.db.fetch_one("SELECT name FROM workers WHERE id=?", (rid,))
                        if wrk:
                            resps.append(wrk["name"])
                resp_txt = ", ".join(resps)
            self.tasks_table.setItem(i, 7, QTableWidgetItem(resp_txt))
            doc_btn = QPushButton("Документы")
            def open_docs_for_task(task_id=t["id"]):
                dlg = DocumentManagerDialog(self, item_id=task_id, db_manager=self.db,
                                           table_name="field_task_documents", id_field="task_id")
                dlg.exec_()
            doc_btn.clicked.connect(open_docs_for_task)
            self.tasks_table.setCellWidget(i, 8, doc_btn)
        self.selected_task = None
        self.tasks_table.clearSelection()
        self.work_form_group.hide()

    def refresh_history(self):
        if not self.selected_plot:
            self.history_table.setRowCount(0)
            return
        plot_id = self.selected_plot["id"]
        query = "SELECT * FROM field_tasks WHERE field_id=?"
        params = [plot_id]
        date_from = self.search_date_from.date().toString("yyyy-MM-dd")
        date_to = self.search_date_to.date().toString("yyyy-MM-dd")
        if date_from and date_to:
            query += " AND (plan_date >= ? AND plan_date <= ?)"
            params.extend([date_from, date_to])
        search_text = self.search_field.text().lower()
        tasks = self.db.fetch_all(query + " ORDER BY id DESC", tuple(params))
        filtered = []
        for t in tasks:
            tech_txt, resp_txt = "", ""
            if t.get("equipment_ids"):
                ids = t["equipment_ids"].split(",")
                techs = []
                for eid in ids:
                    if eid:
                        eq = self.db.fetch_one("SELECT name FROM equipment WHERE id=?", (eid,))
                        if eq:
                            techs.append(eq["name"])
                tech_txt = ", ".join(techs)
            if t.get("responsible_ids"):
                ids = t["responsible_ids"].split(",")
                resps = []
                for rid in ids:
                    if rid:
                        wrk = self.db.fetch_one("SELECT name FROM workers WHERE id=?", (rid,))
                        if wrk:
                            resps.append(wrk["name"])
                resp_txt = ", ".join(resps)
            search_full = (
                f"{t['category']} {t['task_type']} {t.get('status','')} "
                f"{tech_txt} {resp_txt} {t.get('description','')} {t.get('comment','')}"
            ).lower()
            if search_text in search_full:
                filtered.append((t, tech_txt, resp_txt))
        self.history_table.setRowCount(len(filtered))
        for i, (t, tech_txt, resp_txt) in enumerate(filtered):
            self.history_table.setItem(i, 0, QTableWidgetItem(str(t["id"])))
            self.history_table.setItem(i, 1, QTableWidgetItem(t["category"]))
            self.history_table.setItem(i, 2, QTableWidgetItem(t["task_type"]))
            self.history_table.setItem(i, 3, QTableWidgetItem(t["status"]))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(t.get("plan_date") or "")))
            self.history_table.setItem(i, 5, QTableWidgetItem(str(t.get("start_date") or "")))
            self.history_table.setItem(i, 6, QTableWidgetItem(str(t.get("end_date") or "")))
            self.history_table.setItem(i, 7, QTableWidgetItem(tech_txt))
            self.history_table.setItem(i, 8, QTableWidgetItem(resp_txt))
            doc_btn = QPushButton("Документы")
            def open_docs_for_task(task_id=t["id"]):
                dlg = DocumentManagerDialog(self, item_id=task_id, db_manager=self.db,
                                           table_name="field_task_documents", id_field="task_id")
                dlg.exec_()
            doc_btn.clicked.connect(open_docs_for_task)
            self.history_table.setCellWidget(i, 9, doc_btn)
        self.history_table.setSortingEnabled(True)

    def on_task_select(self, row, _):
        tid = int(self.tasks_table.item(row, 0).text())
        self.selected_task = self.db.fetch_one("SELECT * FROM field_tasks WHERE id=?", (tid,))

    def show_multi_warehouse_item_form(self, op_type='outgoing', obj_type='fertilizer'):
        self.clear_work_form()
        layout = self.work_form_layout
        if obj_type == "crop":
            warehouse_type = "Зернохранилище"
            rus_name = "Культура"
            obj_table = "crops"
        else:
            warehouse_type = "Склад удобрений и гербицидов"
            rus_name = "Удобрение/гербицид"
            obj_table = "fertilizers"
        title = "Списание" if op_type == 'outgoing' else "Приход"
        layout.addWidget(QLabel(f"<b>{title} {rus_name.lower()} по складам</b>"))
        grid = QGridLayout()
        grid.addWidget(QLabel("Использовать"), 0, 0)
        grid.addWidget(QLabel("Склад"), 0, 1)
        grid.addWidget(QLabel(rus_name), 0, 2)
        grid.addWidget(QLabel("В наличии"), 0, 3)
        grid.addWidget(QLabel("Вместимость"), 0, 4)
        grid.addWidget(QLabel("Свободно"), 0, 5)
        grid.addWidget(QLabel("Кол-во"), 0, 6)
        self.warehouse_rows = []
        warehouses = self.db.fetch_all(
            "SELECT * FROM warehouses WHERE warehouse_type LIKE ?", (f"%{warehouse_type}%",)
        )
        all_objs = self.db.fetch_all(f"SELECT id, name FROM {obj_table}")
        row_num = 1
        for w in warehouses:
            stocks = self.db.fetch_all(
                "SELECT object_id, SUM(quantity) as qty FROM warehouse_operations "
                "WHERE warehouse_id=? AND object_type=? GROUP BY object_id HAVING qty > 0",
                (w["id"], obj_type)
            )
            drawn = set()
            for s in stocks:
                item = self.db.fetch_one(f"SELECT name FROM {obj_table} WHERE id=?", (s["object_id"],))
                item_name = item["name"] if item else "-"
                free = w["capacity"] - (s["qty"] or 0) if w["capacity"] is not None else '∞'
                cb = QCheckBox()
                have_lbl = QLabel(str(s["qty"]))
                cap_lbl = QLabel(str(w["capacity"]))
                free_lbl = QLabel(str(free))
                qty_spin = QDoubleSpinBox()
                qty_spin.setDecimals(2)
                qty_spin.setMaximum(s["qty"] if op_type == 'outgoing' else free)
                qty_spin.setEnabled(False)
                cb.toggled.connect(lambda checked, spin=qty_spin: spin.setEnabled(checked))
                grid.addWidget(cb, row_num, 0)
                grid.addWidget(QLabel(w['name']), row_num, 1)
                grid.addWidget(QLabel(item_name), row_num, 2)
                grid.addWidget(have_lbl, row_num, 3)
                grid.addWidget(cap_lbl, row_num, 4)
                grid.addWidget(free_lbl, row_num, 5)
                grid.addWidget(qty_spin, row_num, 6)
                self.warehouse_rows.append({
                    "cb": cb,
                    "warehouse_id": w["id"],
                    "object_id": s["object_id"],
                    "name": w["name"],
                    "item_name": item_name,
                    "have_lbl": have_lbl,
                    "free_lbl": free_lbl,
                    "qty_spin": qty_spin,
                    "have": s["qty"],
                    "capacity": w["capacity"]
                })
                drawn.add(s["object_id"])
                row_num += 1
            not_present = [o for o in all_objs if o["id"] not in drawn]
            if not_present:
                cb = QCheckBox()
                obj_combo = QComboBox()
                for o in not_present:
                    obj_combo.addItem(o["name"], o["id"])
                have_lbl = QLabel("0")
                cap_lbl = QLabel(str(w["capacity"]))
                stock_all = self.db.fetch_one(
                    "SELECT SUM(quantity) as qty FROM warehouse_operations WHERE warehouse_id=? AND object_type=?",
                    (w["id"], obj_type)
                )
                all_have = stock_all["qty"] or 0
                free_lbl = QLabel(str(w["capacity"] - all_have))
                qty_spin = QDoubleSpinBox()
                qty_spin.setDecimals(2)
                qty_spin.setMaximum(w["capacity"] - all_have)
                qty_spin.setEnabled(False)
                cb.toggled.connect(lambda checked, spin=qty_spin, combo=obj_combo: spin.setEnabled(checked) or combo.setEnabled(checked))
                obj_combo.setEnabled(False)
                grid.addWidget(cb, row_num, 0)
                grid.addWidget(QLabel(w['name']), row_num, 1)
                grid.addWidget(obj_combo, row_num, 2)
                grid.addWidget(have_lbl, row_num, 3)
                grid.addWidget(cap_lbl, row_num, 4)
                grid.addWidget(free_lbl, row_num, 5)
                grid.addWidget(qty_spin, row_num, 6)
                self.warehouse_rows.append({
                    "cb": cb,
                    "warehouse_id": w["id"],
                    "object_id_combo": obj_combo,
                    "name": w["name"],
                    "item_name": None,
                    "have_lbl": have_lbl,
                    "free_lbl": free_lbl,
                    "qty_spin": qty_spin,
                    "have": 0,
                    "capacity": w["capacity"]
                })
                row_num += 1
        layout.addLayout(grid)
        btns = QHBoxLayout()
        ok_btn = QPushButton("Провести")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.work_form_group.show()
        ok_btn.clicked.connect(lambda: self.handle_multi_warehouse_item(op_type, obj_type))
        cancel_btn.clicked.connect(self.clear_work_form)


    def handle_multi_warehouse_item(self, op_type, obj_type):
        rows = []
        for row in self.warehouse_rows:
            if row["cb"].isChecked():
                qty = row["qty_spin"].value()
                object_id = row.get("object_id")
                if not object_id and "object_id_combo" in row:
                    object_id = row["object_id_combo"].currentData()
                    item_name = row["object_id_combo"].currentText()
                else:
                    item_name = row.get("item_name", "-")
                if op_type == "outgoing" and qty > row.get("have", 0):
                    QMessageBox.warning(self, "Ошибка", f"На складе '{row['name']}' нет столько {item_name}!")
                    return
                if op_type == "incoming" and qty > float(row["free_lbl"].text()):
                    QMessageBox.warning(self, "Ошибка", f"На складе '{row['name']}' нет столько места для {item_name}!")
                    return
                if qty <= 0:
                    QMessageBox.warning(self, "Ошибка", "Количество должно быть больше 0!")
                    return
                rows.append((row["warehouse_id"], object_id, qty))
        if not rows:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одной позиции!")
            return
        for wh_id, obj_id, qty in rows:
            w = self.db.fetch_one("SELECT capacity_unit FROM warehouses WHERE id=?", (wh_id,))
            unit = w["capacity_unit"] if w and "capacity_unit" in w else ""
            self.db.execute(
                "INSERT INTO warehouse_operations (warehouse_id, operation_type, object_type, object_id, date, quantity, unit, plot_id) "
                "VALUES (?, ?, ?, ?, DATE('now'), ?, ?, ?)",
                (wh_id, op_type, obj_type, obj_id, qty, unit, self.selected_plot['id'])
            )
            if obj_type == "fertilizer" and op_type == "outgoing":
                fert = self.db.fetch_one("SELECT name FROM fertilizers WHERE id=?", (obj_id,))
                fert_name = fert["name"] if fert else ""
                self.db.execute(
                    "INSERT INTO fertilizer_use (field_id, name, date, quantity) VALUES (?, ?, DATE('now'), ?)",
                    (self.selected_plot['id'], fert_name, qty)
                )
            if obj_type == "crop" and op_type == "incoming":
                crop = self.db.fetch_one("SELECT name FROM crops WHERE id=?", (obj_id,))
                crop_name = crop["name"] if crop else ""
                self.db.execute(
                    "INSERT INTO harvests (plot_id, date, culture, amount) VALUES (?, DATE('now'), ?, ?)",
                    (self.selected_plot['id'], crop_name, qty)
                )
            if obj_type == "crop" and op_type == "outgoing":
                crop = self.db.fetch_one("SELECT name FROM crops WHERE id=?", (obj_id,))
                crop_name = crop["name"] if crop else ""
                self.db.execute(
                    "INSERT INTO sowing_use (field_id, name, date, quantity) VALUES (?, ?, DATE('now'), ?)",
                    (self.selected_plot['id'], crop_name, qty)
                )
                self.db.execute(
                    "UPDATE plots SET crop=? WHERE id=?",
                    (crop_name, self.selected_plot['id'])
                )
        if self.selected_task:
            self.db.execute(
                """
                UPDATE field_tasks SET
                   status='завершена',
                   end_date=DATE('now')
                WHERE id=?
                """,
                (self.selected_task["id"],)
            )
        self.clear_work_form()
        self.refresh_tasks()
        self.refresh_history()

    def show_create_task_form(self):
        self.clear_work_form()
        layout = self.work_form_layout
        layout.addWidget(QLabel("<b>Создание работы на поле</b>"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(FIELD_CATEGORIES.keys())
        layout.addWidget(QLabel("Категория:"))
        layout.addWidget(self.cat_combo)
        self.type_combo = QComboBox()
        layout.addWidget(QLabel("Тип работы:"))
        layout.addWidget(self.type_combo)
        self.cat_combo.currentTextChanged.connect(
            lambda: self.type_combo.clear() or self.type_combo.addItems(FIELD_CATEGORIES[self.cat_combo.currentText()])
        )
        self.cat_combo.setCurrentIndex(0)
        self.type_combo.addItems(FIELD_CATEGORIES[self.cat_combo.currentText()])
        self.plan_date = QDateEdit(QDate.currentDate())
        self.plan_date.setCalendarPopup(True)
        self.plan_date.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(QLabel("Плановая дата:"))
        layout.addWidget(self.plan_date)
        self.desc_edit = QLineEdit()
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.desc_edit)
        self.comment_edit = QTextEdit()
        layout.addWidget(QLabel("Комментарий:"))
        layout.addWidget(self.comment_edit)
        btns = QHBoxLayout()
        ok_btn = QPushButton("Создать")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        btns.addStretch()
        layout.addLayout(btns)
        self.work_form_group.show()
        ok_btn.clicked.connect(self.handle_create_task)
        cancel_btn.clicked.connect(self.clear_work_form)

    def handle_create_task(self):
        if not self.selected_plot:
            QMessageBox.warning(self, "Ошибка", "Не выбран участок.")
            return
        self.db.execute(
            """INSERT INTO field_tasks
               (field_id, category, task_type, status, plan_date, description, comment)
               VALUES (?, ?, ?, 'запланирована', ?, ?, ?)""",
            (
                self.selected_plot["id"],
                self.cat_combo.currentText(),
                self.type_combo.currentText(),
                self.plan_date.date().toString("yyyy-MM-dd"),
                self.desc_edit.text(),
                self.comment_edit.toPlainText()
            )
        )
        self.clear_work_form()
        self.refresh_tasks()
        self.refresh_history()

    def show_start_task_form(self):
        if not self.selected_task:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите задачу в списке.")
            return
        task = self.selected_task
        self.clear_work_form()
        layout = self.work_form_layout
        layout.addWidget(QLabel(f"<b>Взять в работу: {task['category']} / {task['task_type']}</b>"))
        layout.addWidget(QLabel("Ответственные:"))
        self.workers_list = QListWidget()
        self.workers_list.setSelectionMode(QListWidget.MultiSelection)
        workers = self.db.fetch_all("SELECT id, name FROM workers ORDER BY name")
        for w in workers:
            item = QListWidgetItem(w["name"])
            item.setData(Qt.UserRole, w["id"])
            self.workers_list.addItem(item)
        layout.addWidget(self.workers_list)
        layout.addWidget(QLabel("Техника:"))
        self.equip_list = QListWidget()
        self.equip_list.setSelectionMode(QListWidget.MultiSelection)
        equipment = self.db.fetch_all("SELECT id, name FROM equipment ORDER BY name")
        for e in equipment:
            item = QListWidgetItem(e["name"])
            item.setData(Qt.UserRole, e["id"])
            self.equip_list.addItem(item)
        layout.addWidget(self.equip_list)
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(QLabel("Дата начала:"))
        layout.addWidget(self.start_date)
        btns = QHBoxLayout()
        ok_btn = QPushButton("Старт")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        btns.addStretch()
        layout.addLayout(btns)
        self.work_form_group.show()
        ok_btn.clicked.connect(self.handle_start_task)
        cancel_btn.clicked.connect(self.clear_work_form)

    def handle_start_task(self):
        if not self.selected_task:
            QMessageBox.warning(self, "Ошибка", "Нет выбранной задачи.")
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
        start_d = self.start_date.date().toString("yyyy-MM-dd")
        new_status = CATEGORY_STATUS.get(self.selected_task["category"], "В работе")
        self.db.execute(
            "UPDATE plots SET status=? WHERE id=?",
            (new_status, self.selected_plot["id"])
        )
        self.db.execute(
            """
            UPDATE field_tasks SET
               status='в процессе',
               start_date=?,
               responsible_ids=?,
               equipment_ids=?
            WHERE id=?
            """,
            (
                start_d,
                ",".join(resp_ids),
                ",".join(equip_ids),
                self.selected_task["id"]
            )
        )
        self.clear_work_form()
        self.refresh_tasks()
        self.refresh_history()
        self.on_plot_select(self.plots_table.currentRow(), 0)

    def show_finish_task_form(self):
        if not self.selected_task:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите задачу в списке.")
            return
        task = self.selected_task
        if task["category"] == "Внесение удобрений":
            self.show_multi_warehouse_item_form(op_type='outgoing', obj_type='fertilizer')
            return
        if task["category"] == "Защита растений":
            self.show_multi_warehouse_item_form(op_type='outgoing', obj_type='herbicide')
            return
        if task["category"] == "Уборка урожая":
            self.show_multi_warehouse_item_form(op_type='incoming', obj_type='crop')
            return
        if task["category"] == "Посевные работы":
            self.show_multi_warehouse_item_form(op_type='outgoing', obj_type='crop')
            return
        self.clear_work_form()
        layout = self.work_form_layout
        layout.addWidget(QLabel(f"<b>Завершение работы: {task['category']} / {task['task_type']}</b>"))
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(QLabel("Дата завершения:"))
        layout.addWidget(self.end_date)
        self.result_comment = QTextEdit()
        layout.addWidget(QLabel("Комментарий к завершению:"))
        layout.addWidget(self.result_comment)
        btns = QHBoxLayout()
        ok_btn = QPushButton("Завершить")
        cancel_btn = QPushButton("Отмена")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        btns.addStretch()
        layout.addLayout(btns)
        self.work_form_group.show()
        ok_btn.clicked.connect(self.handle_finish_task)
        cancel_btn.clicked.connect(self.clear_work_form)

    def handle_finish_task(self):
        if not self.selected_task:
            QMessageBox.warning(self, "Ошибка", "Нет выбранной задачи.")
            return
        end_d = self.end_date.date().toString("yyyy-MM-dd")
        comment = self.result_comment.toPlainText()
        self.db.execute(
            """
            UPDATE field_tasks SET
               status='завершена',
               end_date=?,
               comment=?
            WHERE id=?
            """,
            (end_d, comment, self.selected_task["id"])
        )
        self.clear_work_form()
        self.refresh_tasks()
        self.refresh_history()
        self.on_plot_select(self.plots_table.currentRow(), 0)

    def clear_work_form(self):
        while self.work_form_layout.count():
            item = self.work_form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout = item.layout()
            if layout:
                self._delete_layout(layout)
        self.work_form_group.hide()

    def _delete_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout:
                self._delete_layout(child_layout)
