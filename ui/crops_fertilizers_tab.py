##ui/crops_fertilizers_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from document_manager.document_manager import DocumentManagerDialog
from ui.crop_dialog import CropDialog
from ui.fertilizer_dialog import FertilizerDialog
class CropsFertilizersTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.update_crops_table()
        self.update_fertilizers_table()
    def init_ui(self):
        layout = QVBoxLayout(self)
        crops_box = QVBoxLayout()
        crops_box.addWidget(QLabel("<b>Культуры</b>"))
        btn_row = QHBoxLayout()
        add_crop_btn = QPushButton("Добавить культуру")
        edit_crop_btn = QPushButton("Изменить")
        del_crop_btn = QPushButton("Удалить")
        btn_row.addWidget(add_crop_btn)
        btn_row.addWidget(edit_crop_btn)
        btn_row.addWidget(del_crop_btn)
        crops_box.addLayout(btn_row)
        self.add_crop_btn = add_crop_btn
        self.edit_crop_btn = edit_crop_btn
        self.del_crop_btn = del_crop_btn
        self.crops_table = QTableWidget()
        self.crops_table.setColumnCount(7)
        self.crops_table.setHorizontalHeaderLabels([
            "Название", "Категория", "Тип", "Сорт", "Описание", "Фото", "Документы"
        ])
        self.crops_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.crops_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.crops_table.verticalHeader().setDefaultSectionSize(160)
        crops_box.addWidget(self.crops_table)
        layout.addLayout(crops_box)
        fert_box = QVBoxLayout()
        fert_box.addWidget(QLabel("<b>Удобрения и гербициды</b>"))
        fert_btn_row = QHBoxLayout()
        add_fert_btn = QPushButton("Добавить удобрение/гербицид")
        edit_fert_btn = QPushButton("Изменить")
        del_fert_btn = QPushButton("Удалить")
        fert_btn_row.addWidget(add_fert_btn)
        fert_btn_row.addWidget(edit_fert_btn)
        fert_btn_row.addWidget(del_fert_btn)
        fert_box.addLayout(fert_btn_row)
        self.add_fert_btn = add_fert_btn
        self.edit_fert_btn = edit_fert_btn
        self.del_fert_btn = del_fert_btn
        self.fertilizers_table = QTableWidget()
        self.fertilizers_table.setColumnCount(6)
        self.fertilizers_table.setHorizontalHeaderLabels([
            "Название", "Тип", "Форма", "Производитель", "Фото", "Документы"
        ])
        self.fertilizers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fertilizers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.fertilizers_table.verticalHeader().setDefaultSectionSize(160)
        fert_box.addWidget(self.fertilizers_table)
        layout.addLayout(fert_box)
        self.setLayout(layout)
        self.add_crop_btn.clicked.connect(self.add_crop)
        self.edit_crop_btn.clicked.connect(self.edit_crop)
        self.del_crop_btn.clicked.connect(self.delete_crop)
        self.add_fert_btn.clicked.connect(self.add_fertilizer)
        self.edit_fert_btn.clicked.connect(self.edit_fertilizer)
        self.del_fert_btn.clicked.connect(self.delete_fertilizer)

    def update_crops_table(self):
        crops = self.db.fetch_all("SELECT * FROM crops ORDER BY name")
        self.crops_table.setRowCount(len(crops))
        for row, crop in enumerate(crops):
            self.crops_table.setItem(row, 0, QTableWidgetItem(crop["name"]))
            self.crops_table.setItem(row, 1, QTableWidgetItem(crop.get("category", "")))
            self.crops_table.setItem(row, 2, QTableWidgetItem(crop.get("crop_type", "")))
            self.crops_table.setItem(row, 3, QTableWidgetItem(crop.get("variety", "")))
            self.crops_table.setItem(row, 4, QTableWidgetItem(crop.get("description", "")))
            photo_item = QLabel()
            photo_item.setAlignment(Qt.AlignCenter)
            if crop.get("photo"):
                pixmap = QPixmap()
                pixmap.loadFromData(crop["photo"])
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                photo_item.setPixmap(pixmap)
            self.crops_table.setCellWidget(row, 5, photo_item)
            doc_btn = QPushButton("Документы")
            doc_btn.clicked.connect(lambda _, c_id=crop["id"]: self.open_crop_docs(c_id))
            self.crops_table.setCellWidget(row, 6, doc_btn)

    def open_crop_docs(self, crop_id):
        dlg = DocumentManagerDialog(
            parent=self,
            item_id=crop_id,
            db_manager=self.db,
            table_name="crop_documents",
            id_field="crop_id"
        )
        dlg.exec_()

    def update_fertilizers_table(self):
        fertilizers = self.db.fetch_all("SELECT * FROM fertilizers ORDER BY name")
        self.fertilizers_table.setRowCount(len(fertilizers))
        for row, fert in enumerate(fertilizers):
            self.fertilizers_table.setItem(row, 0, QTableWidgetItem(fert["name"]))
            self.fertilizers_table.setItem(row, 1, QTableWidgetItem(fert.get("fertilizer_type", "")))
            self.fertilizers_table.setItem(row, 2, QTableWidgetItem(fert.get("form", "")))
            self.fertilizers_table.setItem(row, 3, QTableWidgetItem(fert.get("manufacturer", "")))
            photo_item = QLabel()
            photo_item.setAlignment(Qt.AlignCenter)
            if fert.get("photo"):
                pixmap = QPixmap()
                pixmap.loadFromData(fert["photo"])
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                photo_item.setPixmap(pixmap)
            self.fertilizers_table.setCellWidget(row, 4, photo_item)
            doc_btn = QPushButton("Документы")
            doc_btn.clicked.connect(lambda _, f_id=fert["id"]: self.open_fertilizer_docs(f_id))
            self.fertilizers_table.setCellWidget(row, 5, doc_btn)

    def open_fertilizer_docs(self, fertilizer_id):
        dlg = DocumentManagerDialog(
            parent=self,
            item_id=fertilizer_id,
            db_manager=self.db,
            table_name="fertilizer_documents",
            id_field="fertilizer_id"
        )
        dlg.exec_()

    def add_crop(self):
        from ui.crop_dialog import CropDialog
        dlg = CropDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            self.db.execute(
                "INSERT INTO crops (name, category, crop_type, variety, description, photo) VALUES (?, ?, ?, ?, ?, ?)",
                (data["name"], data["category"], data["crop_type"], data["variety"], data["description"], data["photo"])
            )
            self.update_crops_table()

    def edit_crop(self):
        row = self.crops_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите культуру для изменения.")
            return
        crops = self.db.fetch_all("SELECT * FROM crops ORDER BY name")
        crop_id = crops[row]["id"]
        from ui.crop_dialog import CropDialog
        crop = self.db.fetch_one("SELECT * FROM crops WHERE id=?", (crop_id,))
        dlg = CropDialog(self, crop)
        if dlg.exec_():
            data = dlg.get_data()
            self.db.execute(
                "UPDATE crops SET name=?, category=?, crop_type=?, variety=?, description=?, photo=? WHERE id=?",
                (data["name"], data["category"], data["crop_type"], data["variety"], data["description"], data["photo"], crop_id)
            )
            self.update_crops_table()

    def delete_crop(self):
        row = self.crops_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите культуру для удаления.")
            return
        crops = self.db.fetch_all("SELECT * FROM crops ORDER BY name")
        crop_id = crops[row]["id"]
        reply = QMessageBox.question(self, "Удаление", "Удалить выбранную культуру?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.execute("DELETE FROM crops WHERE id=?", (crop_id,))
            self.update_crops_table()


    def add_fertilizer(self):
        from ui.fertilizer_dialog import FertilizerDialog
        dlg = FertilizerDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            self.db.execute(
                "INSERT INTO fertilizers (name, fertilizer_type, form, manufacturer, photo) VALUES (?, ?, ?, ?, ?)",
                (data["name"], data["fertilizer_type"], data["form"], data["manufacturer"], data["photo"])
            )
            self.update_fertilizers_table()

    def edit_fertilizer(self):
        from ui.fertilizer_dialog import FertilizerDialog
        row = self.fertilizers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите удобрение/гербицид для изменения.")
            return
        fertilizers = self.db.fetch_all("SELECT * FROM fertilizers ORDER BY name")
        fert_id = fertilizers[row]["id"]
        from .fertilizer_dialog import FertilizerDialog
        fert = self.db.fetch_one("SELECT * FROM fertilizers WHERE id=?", (fert_id,))
        dlg = FertilizerDialog(self, fert)
        if dlg.exec_():
            data = dlg.get_data()
            self.db.execute(
                "UPDATE fertilizers SET name=?, fertilizer_type=?, form=?, manufacturer=?, photo=? WHERE id=?",
                (data["name"], data["fertilizer_type"], data["form"], data["manufacturer"], data["photo"], fert_id)
            )
            self.update_fertilizers_table()

    def delete_fertilizer(self):
        row = self.fertilizers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите удобрение/гербицид для удаления.")
            return
        fertilizers = self.db.fetch_all("SELECT * FROM fertilizers ORDER BY name")
        fert_id = fertilizers[row]["id"]
        reply = QMessageBox.question(self, "Удаление", "Удалить выбранное удобрение/гербицид?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.execute("DELETE FROM fertilizers WHERE id=?", (fert_id,))
            self.update_fertilizers_table()
