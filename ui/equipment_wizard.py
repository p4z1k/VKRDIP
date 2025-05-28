## equipment_wizard.py


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, 
    QLineEdit, QTextEdit, QDialogButtonBox, QGroupBox
)

class EquipmentWizard(QDialog):
    def __init__(self, parent=None, db_manager=None, equipment_id=None):
        super().__init__(parent)
        self.db = db_manager
        self.equipment_id = equipment_id
        self.setWindowTitle("Добавить технику" if not equipment_id else "Редактировать технику")
        self.setMinimumSize(500, 400)
        
        # Сначала создаем элементы интерфейса
        self.category_combo = QComboBox()
        self.type_combo = QComboBox()
        self.subtype_combo = QComboBox()
        self.name_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.reg_number_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.notes_edit = QTextEdit()
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Группа "Классификация"
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
        
        # Группа "Характеристики"
        details_group = QGroupBox("Характеристики")
        details_layout = QFormLayout()
        
        details_layout.addRow("Название/Модель:", self.name_edit)
        details_layout.addRow("Год выпуска:", self.year_edit)
        details_layout.addRow("Рег. номер:", self.reg_number_edit)
        
        self.status_combo.addItems(["Рабочая", "На ремонте", "Списана"])
        details_layout.addRow("Состояние:", self.status_combo)
        
        self.notes_edit.setPlaceholderText("Дополнительные характеристики...")
        details_layout.addRow("Примечания:", self.notes_edit)
        
        details_group.setLayout(details_layout)
        
        layout.addWidget(type_group)
        layout.addWidget(details_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Инициализируем списки после создания всех элементов
        self.update_types()
        
        if self.equipment_id:
            self.load_equipment_data()

    def update_types(self):
        """Обновляет список видов техники в зависимости от категории"""
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
        """Обновляет подтипы для выбранного вида техники"""
        type_ = self.type_combo.currentText()
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
        
        if type_ in subtypes:
            self.subtype_combo.addItems(subtypes[type_])
            self.subtype_combo.setEnabled(True)
        else:
            self.subtype_combo.setEnabled(False)

    def load_equipment_data(self):
        """Загружает данные техники для редактирования"""
        if self.db and self.equipment_id:
            equipment = self.db.fetch_one(
                "SELECT * FROM equipment WHERE id = ?", 
                (self.equipment_id,)
            )
            if equipment:
                self.category_combo.setCurrentText(equipment['category'])
                self.type_combo.setCurrentText(equipment['type'])
                if equipment.get('subtype'):
                    self.subtype_combo.setCurrentText(equipment['subtype'])
                self.name_edit.setText(equipment['name'])
                self.year_edit.setText(equipment.get('year', ''))
                self.reg_number_edit.setText(equipment.get('reg_number', ''))
                self.status_combo.setCurrentText(equipment.get('status', 'Рабочая'))
                self.notes_edit.setPlainText(equipment.get('notes', ''))

    def get_data(self):
        """Возвращает данные из формы"""
        return {
            "category": self.category_combo.currentText(),
            "type": self.type_combo.currentText(),
            "subtype": self.subtype_combo.currentText() if self.subtype_combo.isEnabled() else "",
            "name": self.name_edit.text(),
            "year": self.year_edit.text(),
            "reg_number": self.reg_number_edit.text(),
            "status": self.status_combo.currentText(),
            "notes": self.notes_edit.toPlainText()
        }