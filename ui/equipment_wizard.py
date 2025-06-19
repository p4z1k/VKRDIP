##ui/equipment_wizard.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, 
    QLineEdit, QTextEdit, QDialogButtonBox, QGroupBox,
    QPushButton, QMessageBox, QLabel, QInputDialog
)
from PyQt5.QtCore import Qt
from datetime import datetime
from document_manager.document_manager import DocumentManagerDialog

class EquipmentWizard(QDialog):
    def __init__(self, parent=None, db_manager=None, equipment_id=None):
        super().__init__(parent)
        self.db = db_manager
        self.equipment_id = equipment_id 
        self.setWindowTitle("Добавить технику" if not equipment_id else "Управление техникой")
        self.setMinimumSize(600, 500)
        self.category_combo = QComboBox()
        self.type_combo = QComboBox()
        self.subtype_combo = QComboBox()
        self.name_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.reg_number_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.docs_btn = QPushButton("Документы техники")
        self.docs_btn.setEnabled(False)
        self.docs_btn.clicked.connect(self.open_document_manager)
        self.init_ui()
        if self.equipment_id:
            self.load_equipment_data()
            self.docs_btn.setEnabled(True)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        type_group = QGroupBox("Классификация техники")
        type_layout = QFormLayout()
        self.category_combo.addItems([
            "Почвообрабатывающая техника",
            "Посевная техника",
            "Удобрительные машины",
            "Уборочная техника",
            "Транспортная техника",
            "Специализированная техника"
        ])
        self.category_combo.currentTextChanged.connect(self.update_types)
        type_layout.addRow("Категория:", self.category_combo)
        self.type_combo.currentTextChanged.connect(self.update_subtypes)
        type_layout.addRow("Вид техники:", self.type_combo)
        type_layout.addRow("Подвид (если есть):", self.subtype_combo)
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)
        details_group = QGroupBox("Характеристики")
        details_layout = QFormLayout()
        details_layout.addRow("Название/Модель:", self.name_edit)
        details_layout.addRow("Год выпуска:", self.year_edit)
        details_layout.addRow("Рег. номер:", self.reg_number_edit)
        self.notes_edit.setPlaceholderText("Дополнительные характеристики...")
        details_layout.addRow("Примечания:", self.notes_edit)
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group)
        main_layout.addWidget(self.docs_btn, alignment=Qt.AlignLeft)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        self.update_types()

    def update_types(self):
        category = self.category_combo.currentText()
        self.type_combo.clear()
        equipment_types = {
            "Почвообрабатывающая техника": [
                "Плуги", "Бороны", "Культиваторы", "Чизели", 
                "Лущильники", "Дискаторы", "Катки"
            ],
            "Посевная техника": [
                "Сеялки", "Рассадопосадочные машины", "Пневматические сеялки"
            ],
            "Удобрительные машины": [
                "Разбрасыватели удобрений", "Опрыскиватели",
                "Штанговые опрыскиватели", "Инжекторные вносители"
            ],
            "Уборочная техника": [
                "Комбайны", "Косилки", "Пресс-подборщики",
                "Складыватели валков", "Погрузчики"
            ],
            "Транспортная техника": [
                "Тракторы", "Прицепы и полуприцепы",
                "Автотранспорт", "Зерновозы, кормовозы"
            ],
            "Специализированная техника": [
                "Машины для сбора трав"
            ]
        }
        self.type_combo.addItems(equipment_types.get(category, []))
        self.update_subtypes()

    def update_subtypes(self):
        t = self.type_combo.currentText()
        self.subtype_combo.clear()
        subtypes = {
            "Комбайны": [
                "Зерноуборочные", "Кукурузоуборочные", 
                "Свеклоуборочные", "Картофелеуборочные", 
                "Фруктоуборочные"
            ],
            "Тракторы": [
                "Универсальные", "Гусеничные", "Колесные"
            ],
            "Прицепы и полуприцепы": [
                "Самосвальные", "Бункерные"
            ],
            "Автотранспорт": [
                "Грузовики", "Самосвалы"
            ]
        }
        if t in subtypes:
            self.subtype_combo.addItems(subtypes[t])
            self.subtype_combo.setEnabled(True)
        else:
            self.subtype_combo.setEnabled(False)

    def load_equipment_data(self):
        if not self.equipment_id:
            return
        eq = self.db.fetch_one("SELECT * FROM equipment WHERE id = ?", (self.equipment_id,))
        if not eq:
            return
        self.category_combo.setCurrentText(eq['category'])
        self.type_combo.setCurrentText(eq['type'])
        if eq.get('subtype'):
            self.subtype_combo.setCurrentText(eq['subtype'])
        self.name_edit.setText(eq['name'])
        self.year_edit.setText(eq.get('year', ''))
        self.reg_number_edit.setText(eq.get('reg_number', ''))
        self.notes_edit.setPlainText(eq.get('notes', ''))
    def get_data(self) -> dict:
        return {
            "category": self.category_combo.currentText(),
            "type": self.type_combo.currentText(),
            "subtype": self.subtype_combo.currentText() if self.subtype_combo.isEnabled() else "",
            "name": self.name_edit.text(),
            "year": self.year_edit.text(),
            "reg_number": self.reg_number_edit.text(),
            "notes": self.notes_edit.toPlainText()
        }

    def accept(self):
        if not self.category_combo.currentText().strip():
            QMessageBox.warning(self, "Ошибка", "Укажите категорию техники.")
            return
        if not self.type_combo.currentText().strip():
            QMessageBox.warning(self, "Ошибка", "Укажите вид техники.")
            return
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Укажите название/модель техники.")
            return
        super().accept()

    def open_document_manager(self):
        if not self.equipment_id:
            QMessageBox.warning(self, "Документы", "Сначала сохраните технику.")
            return
        dialog = DocumentManagerDialog(
            parent=self,
            item_id=self.equipment_id,
            db_manager=self.db,
            table_name="equipment_documents",
            id_field="equipment_id"
        )
        dialog.exec_()
