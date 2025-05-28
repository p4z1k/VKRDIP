## field_work_wizard.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QLineEdit, QTextEdit, QDialogButtonBox, QFormLayout,
    QGroupBox, QListWidget, QListWidgetItem, QStackedWidget, QWidget
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QDoubleValidator

class FieldWorkWizard(QDialog):
    def __init__(self, parent=None, plot_id=None, plot_manager=None, work_data=None):
        super().__init__(parent)
        self.plot_id = plot_id
        self.plot_manager = plot_manager
        self.work_data = work_data or {}
        self.setWindowTitle("Редактирование работы" if work_data else "Добавление работы")
        self.setMinimumSize(600, 500)
        
        self.category_combo = None
        self.work_type_combo = None
        self.date_edit = None
        self.status_combo = None
        self.worker_combo = None
        self.equipment_list = None
        self.description_edit = None
        self.notes_edit = None
        
        self.init_ui()
        self.load_workers()
        self.load_equipment()
        self.load_cultures()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Основная форма
        form_layout = QFormLayout()
        
        # Категория работы
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Подготовка почвы",
            "Посевные работы",
            "Уход за посевами",
            "Защита растений",
            "Уборка урожая",
            "Послеуборочная обработка"
        ])
        self.category_combo.currentTextChanged.connect(self.update_work_types)
        form_layout.addRow("Категория:", self.category_combo)
        
        # Конкретный тип работы
        self.work_type_combo = QComboBox()
        form_layout.addRow("Тип работы:", self.work_type_combo)
        
        # Дата выполнения
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата выполнения:", self.date_edit)
        
        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Запланировано",
            "В процессе",
            "Завершено",
            "Отменено"
        ])
        form_layout.addRow("Статус:", self.status_combo)
        
        # Исполнитель
        self.worker_combo = QComboBox()
        form_layout.addRow("Ответственный:", self.worker_combo)
        
        # Техника (множественный выбор)
        self.equipment_list = QListWidget()
        self.equipment_list.setSelectionMode(QListWidget.MultiSelection)
        form_layout.addRow("Используемая техника:", self.equipment_list)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Подробное описание работы...")
        form_layout.addRow("Описание:", self.description_edit)
        
        # Примечания
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Дополнительные примечания...")
        form_layout.addRow("Примечания:", self.notes_edit)
        
        # Специальные поля (будут показаны при необходимости)
        self.special_fields_stack = QStackedWidget()
        
        # Для посевных работ
        sowing_widget = QWidget()
        sowing_layout = QFormLayout(sowing_widget)
        self.culture_combo = QComboBox()
        sowing_layout.addRow("Культура:", self.culture_combo)
        self.sowing_details = QLineEdit()
        sowing_layout.addRow("Детали посева:", self.sowing_details)
        self.special_fields_stack.addWidget(sowing_widget)
        
        # Для защиты растений
        protection_widget = QWidget()
        protection_layout = QFormLayout(protection_widget)
        self.protection_type = QLineEdit()
        protection_layout.addRow("Средство защиты:", self.protection_type)
        self.protection_details = QLineEdit()
        protection_layout.addRow("Способ применения:", self.protection_details)
        self.special_fields_stack.addWidget(protection_widget)
        
        # Пустой виджет по умолчанию
        self.special_fields_stack.addWidget(QWidget())
        
        form_layout.addRow(self.special_fields_stack)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)
        
        # Загрузка данных, если редактируем существующую работу
        if self.work_data:
            self.load_work_data()
        
        # Инициализация списков
        self.update_work_types()

    def update_work_types(self):
        category = self.category_combo.currentText()
        self.work_type_combo.clear()
        
        work_types = {
            "Подготовка почвы": [
                "Вспашка",
                "Боронование",
                "Культивация",
                "Известкование"
            ],
            "Посевные работы": [
                "Посев",
                "Посадка",
                "Подсев"
            ],
            "Уход за посевами": [
                "Прополка",
                "Окучивание",
                "Подкормка",
                "Полив"
            ],
            "Защита растений": [
                "Обработка гербицидами",
                "Обработка инсектицидами",
                "Обработка фунгицидами"
            ],
            "Уборка урожая": [
                "Комбайнирование",
                "Ручной сбор",
                "Транспортировка"
            ],
            "Послеуборочная обработка": [
                "Уборка остатков",
                "Внесение удобрений",
                "Подготовка к зиме"
            ]
        }
        
        self.work_type_combo.addItems(work_types.get(category, []))
        self.update_special_fields()

    def update_special_fields(self):
        category = self.category_combo.currentText()
        
        if category == "Посевные работы":
            self.special_fields_stack.setCurrentIndex(0)
        elif category == "Защита растений":
            self.special_fields_stack.setCurrentIndex(1)
        else:
            self.special_fields_stack.setCurrentIndex(2)

    def load_workers(self):
        workers = self.plot_manager.db.fetch_all("SELECT name FROM workers ORDER BY name")
        self.worker_combo.clear()
        for worker in workers:
            self.worker_combo.addItem(worker['name'])

    def load_equipment(self):
        equipment = self.plot_manager.db.fetch_all("SELECT name FROM equipment ORDER BY name")
        self.equipment_list.clear()
        for item in equipment:
            self.equipment_list.addItem(QListWidgetItem(item['name']))

    def load_cultures(self):
        cultures = self.plot_manager.db.fetch_all("SELECT name FROM crops ORDER BY name")
        self.culture_combo.clear()
        for culture in cultures:
            self.culture_combo.addItem(culture['name'])

    def load_work_data(self):
        if not self.work_data:
            return
            
        self.category_combo.setCurrentText(self.work_data.get('category', 'Подготовка почвы'))
        self.work_type_combo.setCurrentText(self.work_data.get('work_type', ''))
        self.date_edit.setDate(QDate.fromString(self.work_data.get('work_date', QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
        self.status_combo.setCurrentText(self.work_data.get('status', 'Запланировано'))
        self.worker_combo.setCurrentText(self.work_data.get('worker', ''))
        
        # Выбор оборудования
        equipment = self.work_data.get('equipment', '').split(', ')
        for i in range(self.equipment_list.count()):
            item = self.equipment_list.item(i)
            item.setSelected(item.text() in equipment)
        
        self.description_edit.setPlainText(self.work_data.get('description', ''))
        self.notes_edit.setPlainText(self.work_data.get('notes', ''))
        
        # Специальные поля
        if self.work_data.get('category') == "Посевные работы":
            self.culture_combo.setCurrentText(self.work_data.get('culture', ''))
            self.sowing_details.setText(self.work_data.get('details', ''))
        elif self.work_data.get('category') == "Защита растений":
            self.protection_type.setText(self.work_data.get('protection_type', ''))
            self.protection_details.setText(self.work_data.get('protection_details', ''))

    def get_data(self):
        selected_equipment = []
        for i in range(self.equipment_list.count()):
            if self.equipment_list.item(i).isSelected():
                selected_equipment.append(self.equipment_list.item(i).text())
        
        data = {
            "plot_id": self.plot_id,
            "category": self.category_combo.currentText(),
            "work_type": self.work_type_combo.currentText(),
            "work_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "worker": self.worker_combo.currentText(),
            "equipment": ", ".join(selected_equipment),
            "description": self.description_edit.toPlainText(),
            "notes": self.notes_edit.toPlainText()
        }
        
        # Специальные данные
        if self.category_combo.currentText() == "Посевные работы":
            data["culture"] = self.culture_combo.currentText()
            data["details"] = self.sowing_details.text()
        elif self.category_combo.currentText() == "Защита растений":
            data["protection_type"] = self.protection_type.text()
            data["protection_details"] = self.protection_details.text()
        
        return data