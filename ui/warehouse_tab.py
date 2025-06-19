##ui/warehouse_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QDateEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
from .warehouse_dialogs import AddWarehouseDialog
from document_manager.document_manager import DocumentManagerDialog
class WarehouseTab(QWidget):
    def __init__(self, parent=None, plot_manager=None):
        super().__init__(parent)
        self.plot_manager = plot_manager
        self.db = plot_manager.db
        self.selected_warehouse = None
        self.init_ui()
        self.update_warehouses_list()

    def init_ui(self):
        layout = QHBoxLayout(self)
        left_box = QVBoxLayout()
        self.add_warehouse_btn = QPushButton("Добавить склад")
        self.add_warehouse_btn.clicked.connect(self.add_warehouse)
        left_box.addWidget(self.add_warehouse_btn)
        sort_row = QHBoxLayout()
        sort_row.addWidget(QLabel("Сортировка:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["По названию", "По типу", "По вместимости"])
        self.sort_combo.currentIndexChanged.connect(self.update_warehouses_list)
        sort_row.addWidget(self.sort_combo)
        left_box.addLayout(sort_row)
        self.warehouses_table = QTableWidget()
        self.warehouses_table.setColumnCount(4)
        self.warehouses_table.setHorizontalHeaderLabels(["Название", "Тип", "Вместимость", "Ед."])
        self.warehouses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.warehouses_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.warehouses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.warehouses_table.verticalHeader().setDefaultSectionSize(38)
        self.warehouses_table.cellClicked.connect(self.select_warehouse)
        left_box.addWidget(self.warehouses_table, 2)
        layout.addLayout(left_box, 1)
        right_box = QVBoxLayout()
        btn_row = QHBoxLayout()
        self.add_crop_btn = QPushButton("Приход культуры")
        self.ship_crop_btn = QPushButton("Расход культуры")
        self.add_fert_btn = QPushButton("Приход удобрения")
        self.ship_fert_btn = QPushButton("Расход удобрения")
        btn_row.addWidget(self.add_crop_btn)
        btn_row.addWidget(self.ship_crop_btn)
        btn_row.addWidget(self.add_fert_btn)
        btn_row.addWidget(self.ship_fert_btn)
        right_box.addLayout(btn_row)
        self.crop_in_form  = self.create_input_form(object_type='crop', op_type='incoming')
        self.crop_out_form = self.create_input_form(object_type='crop', op_type='outgoing')
        self.fert_in_form  = self.create_input_form(object_type='fertilizer', op_type='incoming')
        self.fert_out_form = self.create_input_form(object_type='fertilizer', op_type='outgoing')
        right_box.addWidget(self.crop_in_form["widget"])
        right_box.addWidget(self.crop_out_form["widget"])
        right_box.addWidget(self.fert_in_form["widget"])
        right_box.addWidget(self.fert_out_form["widget"])
        self.add_crop_btn.clicked.connect(lambda: self.show_form('crop_in'))
        self.ship_crop_btn.clicked.connect(lambda: self.show_form('crop_out'))
        self.add_fert_btn.clicked.connect(lambda: self.show_form('fert_in'))
        self.ship_fert_btn.clicked.connect(lambda: self.show_form('fert_out'))
        self.show_form(None)
        stock_sort_row = QHBoxLayout()
        stock_sort_row.addWidget(QLabel("Сортировка запасов:"))
        self.stock_sort_combo = QComboBox()
        self.stock_sort_combo.addItems(["По названию", "По количеству"])
        self.stock_sort_combo.currentIndexChanged.connect(self.update_stocks_table)
        stock_sort_row.addWidget(self.stock_sort_combo)
        right_box.addLayout(stock_sort_row)
        self.stocks_table = QTableWidget()
        self.stocks_table.setColumnCount(5)
        self.stocks_table.setHorizontalHeaderLabels(["Название", "Категория/Тип", "Количество", "Ед.", "Фото"])
        self.stocks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stocks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stocks_table.verticalHeader().setDefaultSectionSize(64)
        right_box.addWidget(self.stocks_table, 2)
        hist_sort_row = QHBoxLayout()
        hist_sort_row.addWidget(QLabel("Сортировка истории:"))
        self.hist_sort_combo = QComboBox()
        self.hist_sort_combo.addItems(["По дате", "По типу", "По объекту"])
        self.hist_sort_combo.currentIndexChanged.connect(self.update_history_table)
        hist_sort_row.addWidget(self.hist_sort_combo)
        right_box.addLayout(hist_sort_row)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "Дата", "Операция", "Тип", "Поле", "Название", "Количество", "Ед.", "Ответственные", "Документ"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSortingEnabled(True)
        self.history_table.horizontalHeader().setSortIndicatorShown(True)
        self.history_table.setSortingEnabled(True)
        self.history_table.verticalHeader().setDefaultSectionSize(38)
        right_box.addWidget(self.history_table, 3)
        layout.addLayout(right_box, 3)
        self.last_op_id = None

    def show_form(self, which):
        self.crop_in_form["widget"].setVisible(which == 'crop_in')
        self.crop_out_form["widget"].setVisible(which == 'crop_out')
        self.fert_in_form["widget"].setVisible(which == 'fert_in')
        self.fert_out_form["widget"].setVisible(which == 'fert_out')

    def create_input_form(self, object_type='crop', op_type='incoming'):
        form_widget = QWidget()
        form_widget.setVisible(False)
        layout = QHBoxLayout(form_widget)
        obj_label = QLabel("Культура:" if object_type == 'crop' else "Удобрение:")
        obj_combo = QComboBox()
        obj_combo.setMinimumWidth(120)
        objs = self.db.fetch_all(
            "SELECT id, name FROM crops ORDER BY name" if object_type == 'crop'
            else "SELECT id, name FROM fertilizers ORDER BY name"
        )
        for obj in objs:
            obj_combo.addItem(obj["name"], obj["id"])
        layout.addWidget(obj_label)
        layout.addWidget(obj_combo)
        qty_label = QLabel("Количество:")
        qty_edit = QDoubleSpinBox()
        qty_edit.setRange(0.01, 1000000)
        qty_edit.setDecimals(2)
        unit_label = QLabel("Ед.:")
        unit_value = QLabel("")
        unit_value.setMinimumWidth(60)
        layout.addWidget(qty_label)
        layout.addWidget(qty_edit)
        layout.addWidget(unit_label)
        layout.addWidget(unit_value)
        date_label = QLabel("Дата:")
        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(date_label)
        layout.addWidget(date_edit)
        plot_label = QLabel("Поле:")
        plot_combo = QComboBox()
        plots = self.db.fetch_all("SELECT id, name FROM plots ORDER BY name")
        plot_combo.addItem("Без участка", None)
        for p in plots:
            plot_combo.addItem(p["name"], p["id"])
        layout.addWidget(plot_label)
        layout.addWidget(plot_combo)
        resp_label = QLabel("Ответственные:")
        resp_combo = QComboBox()
        resp_combo.setEditable(True)
        workers = self.db.fetch_all("SELECT id, name FROM workers ORDER BY name")
        resp_combo.addItem("—", "")
        for w in workers:
            resp_combo.addItem(w["name"], w["id"])
        layout.addWidget(resp_label)
        layout.addWidget(resp_combo)
        doc_btn = QPushButton("Управлять документами операции")
        layout.addWidget(doc_btn)
        form_widget.last_op_id = None
        add_btn = QPushButton("Добавить" if op_type == 'incoming' else "Отгрузить")
        layout.addWidget(add_btn)
        def process_object():
            if not self.selected_warehouse:
                QMessageBox.warning(self, "Ошибка", "Не выбран склад!")
                return
            obj_id = obj_combo.currentData()
            quantity = qty_edit.value()
            unit = unit_value.text()
            date = date_edit.date().toString("yyyy-MM-dd")
            plot_id = plot_combo.currentData()
            resp_id = resp_combo.currentData()
            wh_id = self.selected_warehouse["id"]
            wh_cap = self.selected_warehouse["capacity"]
            wh_unit = self.selected_warehouse["capacity_unit"]
            if not obj_id or quantity <= 0:
                QMessageBox.warning(self, "Ошибка", "Выберите объект и количество больше 0.")
                return
            if op_type == 'incoming':
                res = self.db.fetch_one(
                    "SELECT COALESCE(SUM(CASE WHEN operation_type='incoming' THEN quantity ELSE -quantity END),0) AS total "
                    "FROM warehouse_operations WHERE warehouse_id=?", (wh_id,))
                cur_total = res["total"] or 0
                if (cur_total + quantity) > wh_cap:
                    QMessageBox.warning(self, "Ошибка", f"Склад переполнен! Максимум: {wh_cap} {wh_unit}")
                    return
            else:
                res = self.db.fetch_one(
                    """SELECT COALESCE(SUM(CASE WHEN operation_type='incoming' THEN quantity ELSE -quantity END),0) AS total
                       FROM warehouse_operations WHERE warehouse_id=? AND object_type=? AND object_id=?""",
                    (wh_id, object_type, obj_id)
                )
                cur_obj_total = res["total"] or 0
                if quantity > cur_obj_total:
                    QMessageBox.warning(self, "Ошибка", f"На складе нет такого количества! Остаток: {cur_obj_total}")
                    return
            cur = self.db.execute(
                """
                INSERT INTO warehouse_operations
                  (warehouse_id, operation_type, object_type, object_id, date,
                   responsible_ids, quantity, unit, plot_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    wh_id,
                    "incoming" if op_type == 'incoming' else "outgoing",
                    object_type,
                    obj_id,
                    date,
                    str(resp_id) if resp_id else "",
                    quantity,
                    unit,
                    plot_id if plot_id else None
                )
            )
            op_id = cur.lastrowid
            self.last_op_id = op_id
            form_widget.last_op_id = op_id
            QMessageBox.information(self, "Успешно", "Операция выполнена!")
            qty_edit.setValue(0.0)
            self.update_stocks_table()
            self.update_history_table()
        add_btn.clicked.connect(process_object)
        def open_doc_manager():
            op_id = form_widget.last_op_id
            if op_id is None:
                QMessageBox.information(self, "Документы", "Сначала проведите операцию (добавьте приход/расход), чтобы прикрепить документы.")
                return
            dlg = DocumentManagerDialog(self, item_id=op_id, db_manager=self.db,
                                       table_name="warehouse_operation_documents",
                                       id_field="operation_id")
            dlg.exec_()
        doc_btn.clicked.connect(open_doc_manager)
        return {
            "widget": form_widget,
            "obj_combo": obj_combo,
            "qty_edit": qty_edit,
            "unit_value": unit_value,
            "date_edit": date_edit,
            "plot_combo": plot_combo,
            "resp_combo": resp_combo,
        }

    def add_warehouse(self):
        dialog = AddWarehouseDialog(parent=self, db=self.db, warehouse_data=None)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"] or not data["address"]:
                QMessageBox.warning(self, "Ошибка", "Название и адрес склада обязательны!")
                return
            self.db.execute(
                """
                INSERT INTO warehouses
                  (name, address, warehouse_type, storage_type, capacity, capacity_unit)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data["address"],
                    data["warehouse_type"],
                    data["storage_type"],
                    data["capacity"],
                    data["capacity_unit"]
                )
            )
            self.update_warehouses_list()

    def update_warehouses_list(self):
        sort_map = {0: "name", 1: "warehouse_type", 2: "capacity"}
        sort_by = sort_map[self.sort_combo.currentIndex()]
        warehouses = self.db.fetch_all(f"SELECT * FROM warehouses ORDER BY {sort_by}")

        self.warehouses_table.setRowCount(len(warehouses))
        for row, w in enumerate(warehouses):
            self.warehouses_table.setItem(row, 0, QTableWidgetItem(w["name"]))
            self.warehouses_table.setItem(row, 1, QTableWidgetItem(w["warehouse_type"]))
            self.warehouses_table.setItem(row, 2, QTableWidgetItem(str(w["capacity"])))
            self.warehouses_table.setItem(row, 3, QTableWidgetItem(w["capacity_unit"]))

        if warehouses:
            self.select_warehouse(0, 0)
        else:
            self.selected_warehouse = None
            self.add_crop_btn.setEnabled(False)
            self.add_fert_btn.setEnabled(False)
            self.ship_crop_btn.setEnabled(False)
            self.ship_fert_btn.setEnabled(False)
            self.stocks_table.setRowCount(0)
            self.history_table.setRowCount(0)

    def select_warehouse(self, row, _col):
        w_item = self.warehouses_table.item(row, 0)
        if not w_item:
            return
        wname = w_item.text()
        wh = self.db.fetch_one("SELECT * FROM warehouses WHERE name=?", (wname,))
        self.selected_warehouse = wh
        unit = wh["capacity_unit"] if wh else ""
        for form in [self.crop_in_form, self.crop_out_form, self.fert_in_form, self.fert_out_form]:
            form["unit_value"].setText(unit)
        if not wh:
            return
        if wh["warehouse_type"] == "Склад удобрений и гербицидов":
            self.add_crop_btn.setEnabled(False)
            self.ship_crop_btn.setEnabled(False)
            self.add_fert_btn.setEnabled(True)
            self.ship_fert_btn.setEnabled(True)
        else:
            self.add_crop_btn.setEnabled(True)
            self.ship_crop_btn.setEnabled(True)
            self.add_fert_btn.setEnabled(False)
            self.ship_fert_btn.setEnabled(False)
        self.update_stocks_table()
        self.update_history_table()

    def update_stocks_table(self):
        if not self.selected_warehouse:
            self.stocks_table.setRowCount(0)
            return
        wh = self.selected_warehouse
        wh_id = wh["id"]
        if wh["warehouse_type"] == "Склад удобрений и гербицидов":
            ops = self.db.fetch_all(
                """
                SELECT object_id,
                       SUM(CASE WHEN operation_type='incoming' THEN quantity ELSE -quantity END) as qty,
                       unit
                FROM warehouse_operations
                WHERE warehouse_id=? AND object_type='fertilizer'
                GROUP BY object_id, unit
                HAVING qty > 0
                """,
                (wh_id,)
            )
            self.stocks_table.setRowCount(len(ops))
            for i, op in enumerate(ops):
                fert = self.db.fetch_one("SELECT * FROM fertilizers WHERE id=?", (op["object_id"],))
                name = fert["name"] if fert else ""
                ftype = fert.get("fertilizer_type", "") if fert else ""
                quantity = op["qty"]
                unit = op["unit"]
                self.stocks_table.setItem(i, 0, QTableWidgetItem(name))
                self.stocks_table.setItem(i, 1, QTableWidgetItem(ftype))
                self.stocks_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
                self.stocks_table.setItem(i, 3, QTableWidgetItem(unit))
                photo_lbl = QLabel()
                photo_lbl.setAlignment(Qt.AlignCenter)
                if fert and fert.get("photo"):
                    pix = QPixmap()
                    pix.loadFromData(fert["photo"])
                    w = self.stocks_table.columnWidth(4) or 64
                    h = self.stocks_table.verticalHeader().sectionSize(i) or 64
                    pix = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    photo_lbl.setPixmap(pix)
                self.stocks_table.setCellWidget(i, 4, photo_lbl)
        else:
            ops = self.db.fetch_all(
                """
                SELECT object_id,
                       SUM(CASE WHEN operation_type='incoming' THEN quantity ELSE -quantity END) as qty,
                       unit
                FROM warehouse_operations
                WHERE warehouse_id=? AND object_type='crop'
                GROUP BY object_id, unit
                HAVING qty > 0
                """,
                (wh_id,)
            )
            self.stocks_table.setRowCount(len(ops))
            for i, op in enumerate(ops):
                crop = self.db.fetch_one("SELECT * FROM crops WHERE id=?", (op["object_id"],))
                name = crop["name"] if crop else ""
                category = crop.get("category", "") if crop else ""
                quantity = op["qty"]
                unit = op["unit"]
                self.stocks_table.setItem(i, 0, QTableWidgetItem(name))
                self.stocks_table.setItem(i, 1, QTableWidgetItem(category))
                self.stocks_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
                self.stocks_table.setItem(i, 3, QTableWidgetItem(unit))
                photo_lbl = QLabel()
                photo_lbl.setAlignment(Qt.AlignCenter)
                if crop and crop.get("photo"):
                    pix = QPixmap()
                    pix.loadFromData(crop["photo"])
                    w = self.stocks_table.columnWidth(4) or 64
                    h = self.stocks_table.verticalHeader().sectionSize(i) or 64
                    pix = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    photo_lbl.setPixmap(pix)
                self.stocks_table.setCellWidget(i, 4, photo_lbl)

    def update_history_table(self):
        if not self.selected_warehouse:
            self.history_table.setRowCount(0)
            return
        wh_id = self.selected_warehouse["id"]
        ops = self.db.fetch_all(
            """
            SELECT * FROM warehouse_operations
            WHERE warehouse_id=?
            ORDER BY date DESC, id DESC
            """,
            (wh_id,)
        )
        self.history_table.setRowCount(len(ops))
        for row, op in enumerate(ops):
            self.history_table.setItem(row, 0, QTableWidgetItem(op["date"] or ""))
            self.history_table.setItem(row, 1, QTableWidgetItem(op.get("operation_type", "")))
            self.history_table.setItem(row, 2, QTableWidgetItem(op.get("object_type", "")))
            if op.get("plot_id"):
                plot = self.db.fetch_one("SELECT name FROM plots WHERE id=?", (op["plot_id"],))
                self.history_table.setItem(row, 3, QTableWidgetItem(plot["name"] if plot else ""))
            else:
                self.history_table.setItem(row, 3, QTableWidgetItem("—"))
            if op.get("object_type") == "crop":
                obj = self.db.fetch_one("SELECT name FROM crops WHERE id=?", (op["object_id"],))
            else:
                obj = self.db.fetch_one("SELECT name FROM fertilizers WHERE id=?", (op["object_id"],))
            self.history_table.setItem(row, 4, QTableWidgetItem(obj["name"] if obj else ""))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(op.get("quantity", ""))))
            self.history_table.setItem(row, 6, QTableWidgetItem(op.get("unit", "")))
            resp_names = []
            if op.get("responsible_ids"):
                ids = [i for i in str(op["responsible_ids"]).split(",") if i]
                for rid in ids:
                    wrk = self.db.fetch_one("SELECT name FROM workers WHERE id=?", (rid,))
                    if wrk:
                        resp_names.append(wrk["name"])
            self.history_table.setItem(row, 7, QTableWidgetItem(", ".join(resp_names)))
            doc_btn = QPushButton("Документы")
            def open_docs_for_op(op_id=op["id"]):
                dlg = DocumentManagerDialog(self, item_id=op_id, db_manager=self.db,
                                           table_name="warehouse_operation_documents",
                                           id_field="operation_id")
                dlg.exec_()
            doc_btn.clicked.connect(open_docs_for_op)
            self.history_table.setCellWidget(row, 8, doc_btn)
