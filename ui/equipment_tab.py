##ui/equipment_tab.py
import os
from datetime import *
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLineEdit, QHeaderView, QAbstractItemView,
    QMessageBox, QLabel, QTabWidget, QDateEdit, QDialog
)
from PyQt5.QtCore import Qt, QDate
from ui.service_dialogs import ServiceEventDialog, TakeToWorkDialog, FinishRepairDialog

class EquipmentTab(QWidget):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.current_equipment_id = None
        self.init_ui()
        self.update_equipment_list()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        control_panel = QHBoxLayout()
        self.add_btn = QPushButton("Добавить технику")
        self.add_btn.clicked.connect(self.add_equipment)
        control_panel.addWidget(self.add_btn)
        self.manage_btn = QPushButton("Управление техникой")
        self.manage_btn.setEnabled(False)
        self.manage_btn.clicked.connect(self.manage_equipment)
        control_panel.addWidget(self.manage_btn)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_equipment)
        control_panel.addWidget(self.delete_btn)
        self.repair_btn = QPushButton("Ремонт/ТО")
        self.repair_btn.setEnabled(False)
        self.repair_btn.clicked.connect(self.open_service_dialog)
        control_panel.addWidget(self.repair_btn)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Все категории",
            "Почвообрабатывающая",
            "Посевная",
            "Удобрительные",
            "Уборочная",
            "Транспортная",
            "Специализированная"
        ])
        self.filter_combo.currentTextChanged.connect(self.update_equipment_list)
        control_panel.addWidget(QLabel("Фильтр:"))
        control_panel.addWidget(self.filter_combo)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию...")
        self.search_edit.textChanged.connect(self.update_equipment_list)
        control_panel.addWidget(self.search_edit)
        main_layout.addLayout(control_panel)
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(7)
        self.equipment_table.setHorizontalHeaderLabels([
            "ID", "Категория", "Вид", "Подвид", "Название", "Состояние", "Рег. номер"
        ])
        self.equipment_table.hideColumn(0)
        self.equipment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equipment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.equipment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.equipment_table.itemSelectionChanged.connect(self.on_selection_changed)
        main_layout.addWidget(self.equipment_table)
        self.tabs = QTabWidget()
        self.history_tab = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.history_tab, "История обслуживания")
        self.breakdown_tab = QWidget()
        self.init_breakdown_tab()
        self.tabs.addTab(self.breakdown_tab, "Поломки")
        main_layout.addWidget(self.tabs)

    def init_history_tab(self):
        from PyQt5.QtWidgets import QGridLayout, QPushButton, QDateEdit
        layout = QVBoxLayout(self.history_tab)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Дата от:"))
        self.hist_date_from = QDateEdit()
        self.hist_date_from.setCalendarPopup(True)
        self.hist_date_from.setDisplayFormat("yyyy-MM-dd")
        self.hist_date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.hist_date_from)
        filter_layout.addWidget(QLabel("Дата до:"))
        self.hist_date_to = QDateEdit()
        self.hist_date_to.setCalendarPopup(True)
        self.hist_date_to.setDisplayFormat("yyyy-MM-dd")
        self.hist_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hist_date_to)
        filter_layout.addWidget(QLabel("Категория:"))
        self.hist_cat_combo = QComboBox()
        self.hist_cat_combo.addItems(["Все", "Поломка", "Техническое обслуживание"])
        filter_layout.addWidget(self.hist_cat_combo)
        filter_layout.addWidget(QLabel("Статус:"))
        self.hist_status_combo = QComboBox()
        self.hist_status_combo.addItems(["Все", "New", "In Progress", "Completed"])
        filter_layout.addWidget(self.hist_status_combo)
        self.hist_filter_btn = QPushButton("Фильтровать")
        self.hist_filter_btn.clicked.connect(self.update_history_table)
        filter_layout.addWidget(self.hist_filter_btn)
        layout.addLayout(filter_layout)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Дата начала", "Дата окончания", "Категория", "Тип",
            "Статус", "Описание", "Ответственный", "Сервисный центр"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.verticalHeader().setDefaultSectionSize(30)
        layout.addWidget(self.history_table)

    def init_breakdown_tab(self):
        layout = QVBoxLayout(self.breakdown_tab)
        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(6)
        self.breakdown_table.setHorizontalHeaderLabels([
            "ID", "Дата обнаружения", "Тип неисправности", "Приоритет", "Статус", "Ответственный"
        ])
        self.breakdown_table.hideColumn(0)
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.breakdown_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.breakdown_table)
        btn_layout = QHBoxLayout()
        self.take_work_btn = QPushButton("Взять в работу")
        self.take_work_btn.clicked.connect(self.take_breakdown_to_work)
        btn_layout.addWidget(self.take_work_btn)
        self.finish_repair_btn = QPushButton("Закончить ремонт")
        self.finish_repair_btn.clicked.connect(self.finish_repair)
        btn_layout.addWidget(self.finish_repair_btn)
        layout.addLayout(btn_layout)

    def update_equipment_list(self):
        category_filter = self.filter_combo.currentText()
        search_text = self.search_edit.text().lower()
        base_query = "SELECT * FROM equipment"
        params = []
        conditions = []
        if category_filter != "Все категории":
            conditions.append("category LIKE ?")
            params.append(f"%{category_filter}%")
        if search_text:
            conditions.append("LOWER(name) LIKE ?")
            params.append(f"%{search_text}%")
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY category, type, name"
        equipment_list = self.db.fetch_all(base_query, tuple(params))
        self.equipment_table.setRowCount(len(equipment_list))
        for row, eq in enumerate(equipment_list):
            self.equipment_table.setItem(row, 0, QTableWidgetItem(str(eq['id'])))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(eq['category']))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(eq['type']))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(eq.get('subtype', '-')))
            self.equipment_table.setItem(row, 4, QTableWidgetItem(eq['name']))
            status_item = QTableWidgetItem(eq.get('status', 'Рабочая'))
            status = eq.get('status', 'Рабочая')
            if status == "На ремонте":
                status_item.setBackground(Qt.red)
            elif status == "ТО":
                status_item.setBackground(Qt.yellow)
            else:
                status_item.setBackground(Qt.green)
            self.equipment_table.setItem(row, 5, status_item)
            self.equipment_table.setItem(row, 6, QTableWidgetItem(eq.get('reg_number', '-')))
        self.current_equipment_id = None
        self.manage_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.repair_btn.setEnabled(False)
        self.history_table.setRowCount(0)
        self.breakdown_table.setRowCount(0)

    def on_selection_changed(self):

        selected = self.equipment_table.selectionModel().hasSelection()
        if not selected:
            self.current_equipment_id = None
            self.manage_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.repair_btn.setEnabled(False)
            self.history_table.setRowCount(0)
            self.breakdown_table.setRowCount(0)
            return
        row = self.equipment_table.currentRow()
        eq_id_item = self.equipment_table.item(row, 0)
        if not eq_id_item:
            return
        eq_id = int(eq_id_item.text())
        self.current_equipment_id = eq_id
        self.manage_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.repair_btn.setEnabled(True)
        self.update_history_table()
        self.update_breakdowns_table()

    def add_equipment(self):
        from .equipment_wizard import EquipmentWizard
        dialog = EquipmentWizard(self, self.db)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                """
                INSERT INTO equipment 
                  (category, type, subtype, name, year, reg_number, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'Рабочая', ?, ?, ?)
                """,
                (
                    data['category'],
                    data['type'],
                    data['subtype'],
                    data['name'],
                    data['year'],
                    data['reg_number'],
                    data['notes'],
                    now,
                    now
                )
            )
            self.update_equipment_list()

    def manage_equipment(self):
        from ui.equipment_wizard import EquipmentWizard
        if not self.current_equipment_id:
            return
        dialog = EquipmentWizard(self, self.db, self.current_equipment_id)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                """
                UPDATE equipment SET
                  category=?, type=?, subtype=?, name=?, 
                  year=?, reg_number=?, status='Рабочая', notes=?, updated_at=?
                WHERE id=?
                """,
                (
                    data['category'],
                    data['type'],
                    data['subtype'],
                    data['name'],
                    data['year'],
                    data['reg_number'],
                    data['notes'],
                    now,
                    self.current_equipment_id
                )
            )
            self.update_equipment_list()

    def delete_equipment(self):
        if not self.current_equipment_id:
            return
        if QMessageBox.question(
            self, "Удаление техники",
            "Вы уверены, что хотите удалить эту технику?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.db.execute("DELETE FROM equipment WHERE id=?", (self.current_equipment_id,))
            self.update_equipment_list()

    def open_service_dialog(self):
        if not self.current_equipment_id:
            return
        dialog = ServiceEventDialog(self, self.db, self.current_equipment_id)
        if dialog.exec_() == QDialog.Accepted:
            self.update_history_table()
            self.update_breakdowns_table()

    def update_history_table(self):
        if not self.current_equipment_id:
            self.history_table.setRowCount(0)
            return
        date_from = self.hist_date_from.date().toString("yyyy-MM-dd")
        date_to = self.hist_date_to.date().toString("yyyy-MM-dd")
        cat = self.hist_cat_combo.currentText()
        status = self.hist_status_combo.currentText()
        query = """
            SELECT es.id, es.date_start, es.date_end, es.event_category, es.event_type,
                   es.status, es.description, w.name as worker_name, es.service_center
            FROM equipment_service es
            LEFT JOIN workers w ON es.responsible_id = w.id
            WHERE es.equipment_id = ?
              AND es.date_start BETWEEN ? AND ?
        """
        params = [self.current_equipment_id, date_from, date_to]
        if cat != "Все":
            if cat == "Поломка":
                query += " AND es.event_category = 'breakdown'"
            else:
                query += " AND es.event_category = 'maintenance'"
        if status != "Все":
            query += " AND es.status = ?"
            params.append(status)
        query += " ORDER BY es.date_start DESC"
        rows = self.db.fetch_all(query, tuple(params))
        self.history_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.history_table.setItem(i, 0, QTableWidgetItem(r["date_start"]))
            self.history_table.setItem(i, 1, QTableWidgetItem(r["date_end"] or ""))
            cat_text = "Поломка" if r["event_category"] == "breakdown" else "ТО"
            self.history_table.setItem(i, 2, QTableWidgetItem(cat_text))
            self.history_table.setItem(i, 3, QTableWidgetItem(r["event_type"]))
            self.history_table.setItem(i, 4, QTableWidgetItem(r["status"]))
            self.history_table.setItem(i, 5, QTableWidgetItem(r["description"] or ""))
            self.history_table.setItem(i, 6, QTableWidgetItem(r["worker_name"] or ""))
            self.history_table.setItem(i, 7, QTableWidgetItem(r["service_center"] or ""))

    def update_breakdowns_table(self):
        if not self.current_equipment_id:
            self.breakdown_table.setRowCount(0)
            return
        rows = self.db.fetch_all(
            """
            SELECT es.id, es.date_start, es.event_type, es.priority, es.status, w.name as worker_name
            FROM equipment_service es
            LEFT JOIN workers w ON es.responsible_id = w.id
            WHERE es.equipment_id = ? AND es.event_category = 'breakdown'
            ORDER BY 
              CASE es.priority
                WHEN 'срочный' THEN 1
                WHEN 'средний' THEN 2
                WHEN 'низкий' THEN 3
                ELSE 4
              END,
              es.date_start DESC
            """,
            (self.current_equipment_id,)
        )
        self.breakdown_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.breakdown_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.breakdown_table.setItem(i, 1, QTableWidgetItem(r["date_start"]))
            self.breakdown_table.setItem(i, 2, QTableWidgetItem(r["event_type"]))
            self.breakdown_table.setItem(i, 3, QTableWidgetItem(r["priority"]))
            self.breakdown_table.setItem(i, 4, QTableWidgetItem(r["status"]))
            self.breakdown_table.setItem(i, 5, QTableWidgetItem(r["worker_name"] or ""))
        self.breakdown_table.verticalHeader().setDefaultSectionSize(30)

    def get_selected_breakdown_id(self) -> int:
        row = self.breakdown_table.currentRow()
        if row < 0:
            return None
        item = self.breakdown_table.item(row, 0)
        return int(item.text()) if item else None

    def take_breakdown_to_work(self):
        service_id = self.get_selected_breakdown_id()
        if not service_id:
            QMessageBox.information(self, "Ошибка", "Сначала выберите поломку.")
            return
        rec = self.db.fetch_one("SELECT status FROM equipment_service WHERE id=?", (service_id,))
        if not rec or rec["status"] != "New":
            QMessageBox.warning(self, "Ошибка", "Можно взять в работу только поломку со статусом 'New'.")
            return
        dlg = TakeToWorkDialog(self, self.db, service_id)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                """
                UPDATE equipment_service SET
                  status = 'In Progress',
                  responsible_id = ?,
                  updated_at = ?
                WHERE id = ?
                """,
                (data["responsible_id"], now_ts, service_id)
            )
            self.update_breakdowns_table()
            self.update_history_table()

    def finish_repair(self):
        service_id = self.get_selected_breakdown_id()
        if not service_id:
            QMessageBox.information(self, "Ошибка", "Сначала выберите поломку.")
            return
        rec = self.db.fetch_one("SELECT status FROM equipment_service WHERE id=?", (service_id,))
        if not rec or rec["status"] != "In Progress":
            QMessageBox.warning(self, "Ошибка", "Закончить можно только поломки со статусом 'In Progress'.")
            return
        dlg = FinishRepairDialog(self, self.db, service_id)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                """
                UPDATE equipment_service SET
                  status = 'Completed',
                  date_end = ?,
                  description = description || '\n\n[Завершение:] ' || ?,
                  updated_at = ?
                WHERE id = ?
                """,
                (data['date_end'], data['finish_description'], now_ts, service_id)
            )
            for path in data['attached_paths']:
                if not os.path.isfile(path):
                    continue
                fname = os.path.basename(path)
                file_ext = os.path.splitext(fname)[1].lower()
                try:
                    with open(path, "rb") as f:
                        blob = f.read()
                except Exception:
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
            self.update_breakdowns_table()
            self.update_history_table()
