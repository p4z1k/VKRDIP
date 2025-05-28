## equipment_tab.py


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLineEdit, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog  # Добавлен импорт QDialog
)
from PyQt5.QtCore import Qt
from ui.equipment_wizard import EquipmentWizard

class EquipmentTab(QWidget):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()
        self.update_equipment_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Панель управления
        control_panel = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить технику")
        self.add_btn.clicked.connect(self.add_equipment)
        
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_equipment)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_equipment)
        self.delete_btn.setEnabled(False)
        
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
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию...")
        self.search_edit.textChanged.connect(self.update_equipment_list)
        
        control_panel.addWidget(self.add_btn)
        control_panel.addWidget(self.edit_btn)
        control_panel.addWidget(self.delete_btn)
        control_panel.addWidget(self.filter_combo)
        control_panel.addWidget(self.search_edit)
        
        # Таблица техники
        self.equipment_table = QTableWidget()
        self.equipment_table.setColumnCount(6)
        self.equipment_table.setHorizontalHeaderLabels([
            "Категория", "Вид", "Подвид", "Название", "Состояние", "Рег. номер"
        ])
        self.equipment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.equipment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.equipment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.equipment_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addLayout(control_panel)
        layout.addWidget(self.equipment_table)

    def update_equipment_list(self):
        """Обновляет список техники с учетом фильтров"""
        category_filter = self.filter_combo.currentText()
        search_text = self.search_edit.text().lower()
        
        query = "SELECT * FROM equipment"
        params = []
        
        if category_filter != "Все категории":
            query += " WHERE category LIKE ?"
            params.append(f"%{category_filter[:5]}%")  # Берем первые 5 символов для фильтрации
        
        if search_text and category_filter == "Все категории":
            query += " WHERE LOWER(name) LIKE ?"
            params.append(f"%{search_text}%")
        elif search_text:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{search_text}%")
            
        query += " ORDER BY category, type, name"
        
        equipment_list = self.db.fetch_all(query, tuple(params)) if params else self.db.fetch_all(query)
        
        self.equipment_table.setRowCount(len(equipment_list))
        for row, equipment in enumerate(equipment_list):
            self.equipment_table.setItem(row, 0, QTableWidgetItem(equipment['category']))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(equipment['type']))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(equipment.get('subtype', '-')))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(equipment['name']))
            self.equipment_table.setItem(row, 4, QTableWidgetItem(equipment.get('status', 'Рабочая')))
            self.equipment_table.setItem(row, 5, QTableWidgetItem(equipment.get('reg_number', '-')))

    def on_selection_changed(self):
        """Активирует/деактивирует кнопки при изменении выбора"""
        selected = self.equipment_table.selectionModel().hasSelection()
        self.edit_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)

    def add_equipment(self):
        """Открывает мастер добавления новой техники"""
        dialog = EquipmentWizard(self, self.db)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.execute(
                """INSERT INTO equipment 
                (category, type, subtype, name, year, reg_number, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data['category'], data['type'], data['subtype'],
                    data['name'], data['year'], data['reg_number'],
                    data['status'], data['notes']
                )
            )
            self.update_equipment_list()

    def edit_equipment(self):
        """Открывает мастер редактирования выбранной техники"""
        selected_row = self.equipment_table.currentRow()
        if selected_row >= 0:
            equipment_id = self.get_selected_equipment_id(selected_row)
            if equipment_id:
                dialog = EquipmentWizard(self, self.db, equipment_id)
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    self.db.execute(
                        """UPDATE equipment SET 
                        category=?, type=?, subtype=?, name=?, 
                        year=?, reg_number=?, status=?, notes=?
                        WHERE id=?""",
                        (
                            data['category'], data['type'], data['subtype'],
                            data['name'], data['year'], data['reg_number'],
                            data['status'], data['notes'], equipment_id
                        )
                    )
                    self.update_equipment_list()

    def delete_equipment(self):
        """Удаляет выбранную технику"""
        selected_row = self.equipment_table.currentRow()
        if selected_row >= 0:
            equipment_id = self.get_selected_equipment_id(selected_row)
            if equipment_id:
                if QMessageBox.question(
                    self, "Удаление техники",
                    "Вы уверены, что хотите удалить эту технику?",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes:
                    self.db.execute("DELETE FROM equipment WHERE id=?", (equipment_id,))
                    self.update_equipment_list()

    def get_selected_equipment_id(self, row):
        """Возвращает ID выбранной техники"""
        name = self.equipment_table.item(row, 3).text()
        equipment = self.db.fetch_one(
            "SELECT id FROM equipment WHERE name = ?", 
            (name,)
        )
        return equipment['id'] if equipment else None