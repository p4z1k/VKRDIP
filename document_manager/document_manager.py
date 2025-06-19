##document_manager/document_manager.py
import os
import sys
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox, QInputDialog, QComboBox
)
from PyQt5.QtCore import Qt
class DocumentManagerDialog(QDialog):
    CATEGORIES = {

        "Общие документы": ["PDF", "DOC", "Изображение"]
    }
    def __init__(
        self,
        parent=None,
        item_id: int = None,
        db_manager=None,
        table_name: str = None,
        id_field: str = None
    ):
        super().__init__(parent)
        self.item_id = item_id
        self.db = db_manager
        self.table_name = table_name
        self.id_field = id_field
        self.setWindowTitle("Управление документами")
        self.setMinimumSize(700, 450)
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.docs_list = QListWidget()
        layout.addWidget(QLabel("Список документов:"))
        layout.addWidget(self.docs_list)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить документ")
        self.add_btn.clicked.connect(self.add_document)
        btn_layout.addWidget(self.add_btn)
        self.open_btn = QPushButton("Открыть документ")
        self.open_btn.clicked.connect(self.open_document)
        btn_layout.addWidget(self.open_btn)
        self.del_btn = QPushButton("Удалить документ")
        self.del_btn.clicked.connect(self.delete_document)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def load_documents(self):
        self.docs_list.clear()
        rows = self.db.fetch_all(
            f"SELECT id, file_name, upload_date "
            f"FROM {self.table_name} WHERE {self.id_field} = ? ORDER BY upload_date DESC",
            (self.item_id,)
        )
        self.docs = rows 
        for doc in rows:
            display_text = f"{doc['file_name']}    |    {doc['upload_date']}"
            self.docs_list.addItem(display_text)

    def add_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для загрузки",
            "",
            "Все файлы (*.*);;PDF (*.pdf);;Word (*.docx *.doc);;Изображения (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        file_ext = os.path.splitext(file_path)[1].lower()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.table_name == "equipment_service_documents":
            rec = self.db.fetch_one(
                "SELECT equipment_id FROM equipment_service WHERE id=?",
                (self.item_id,)
            )
            eq_id = rec['equipment_id'] if rec else self.item_id
            eq_rec = self.db.fetch_one("SELECT name FROM equipment WHERE id=?", (eq_id,))
            entity_name = eq_rec['name'] if eq_rec else str(eq_id)
            year_str = datetime.now().strftime("%Y")
            default_fname = f"Документ для события {entity_name} {year_str}{file_ext}"
            file_name, ok_name = QInputDialog.getText(
                self, "Имя файла",
                "Отредактируйте имя файла:",
                text=default_fname
            )
            if not ok_name or not file_name.strip():
                return
            file_name = file_name.strip()
            try:
                with open(file_path, "rb") as f:
                    blob = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл: {e}")
                return
            file_type = file_ext.lstrip(".").lower()
            try:
                self.db.execute(
                    f"""
                    INSERT INTO {self.table_name}
                      (service_id, file_name, file_data, file_type, upload_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.item_id, file_name, blob, file_type, now)
                )
                self.load_documents()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить документ: {e}")
            return
        categories = list(self.CATEGORIES.keys())
        if categories:
            cat, ok_cat = QInputDialog.getItem(
                self, "Выбор категории",
                "Категория документа:", categories, 0, False
            )
            if not ok_cat:
                return
            subcats = self.CATEGORIES.get(cat, [])
            if subcats:
                sub, ok_sub = QInputDialog.getItem(
                    self, "Выбор подкатегории",
                    "Подкатегория документа:", subcats, 0, False
                )
                if not ok_sub:
                    return
            else:
                sub = ""
        else:
            cat = ""
            sub = ""
        if self.table_name == "equipment_documents":
            rec = self.db.fetch_one("SELECT name FROM equipment WHERE id=?", (self.item_id,))
            entity_name = rec['name'] if rec else str(self.item_id)
        else:
            rec = self.db.fetch_one("SELECT name FROM plots WHERE id=?", (self.item_id,))
            entity_name = rec['name'] if rec else str(self.item_id)

        default_fname = f"{sub} для {entity_name}{file_ext}"
        file_name, ok_name = QInputDialog.getText(
            self, "Имя файла", "Отредактируйте имя файла:", text=default_fname
        )
        if not ok_name or not file_name.strip():
            return
        file_name = file_name.strip()
        try:
            with open(file_path, "rb") as f:
                blob = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл: {e}")
            return
        file_type = file_ext.lstrip(".").lower()
        try:
            self.db.execute(
                f"""
                INSERT INTO {self.table_name}
                  ({self.id_field}, document_type, document_subtype, file_name, file_data, file_type, upload_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.item_id,
                    cat,
                    sub,
                    file_name,
                    blob,
                    file_type,
                    now
                )
            )
            self.load_documents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить документ: {e}")

    def open_document(self):
        idx = self.docs_list.currentRow()
        if idx < 0:
            QMessageBox.information(self, "Открытие документа", "Сначала выберите документ.")
            return
        doc = self.docs[idx]
        doc_id = doc["id"]
        rec = self.db.fetch_one(
            f"SELECT file_name, file_data FROM {self.table_name} WHERE id = ?", (doc_id,)
        )
        if not rec:
            QMessageBox.warning(self, "Ошибка", "Не найден документ в базе.")
            return
        file_name = rec["file_name"]
        blob = rec["file_data"]
        suffix = os.path.splitext(file_name)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(blob)
        tmp.flush()
        tmp.close()
        try:
            if os.name == "nt":
                os.startfile(tmp.name)
            elif sys.platform == "darwin":
                os.system(f"open \"{tmp.name}\"")
            else:
                os.system(f"xdg-open \"{tmp.name}\"")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def delete_document(self):
        idx = self.docs_list.currentRow()
        if idx < 0:
            QMessageBox.information(self, "Удаление документа", "Сначала выберите документ.")
            return
        doc = self.docs[idx]
        doc_id = doc["id"]
        fname = doc["file_name"]
        reply = QMessageBox.question(
            self,
            "Удаление документа",
            f"Вы уверены, что хотите удалить документ '{fname}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        try:
            self.db.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (doc_id,))
            self.load_documents()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить документ: {e}")
