## field_work_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,QMenu,
    QLabel, QComboBox, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QGroupBox,
    QDateEdit, QDialog, QMessageBox, QDialogButtonBox, QTabWidget
)
from PyQt5.QtCore import Qt, QDate
from ui.field_work_wizard import FieldWorkWizard  
from ui.harvest_dialog import HarvestDialog  

class FieldWorkTab(QWidget):
    def __init__(self, parent=None, plot_manager=None):
        super().__init__(parent)
        self.plot_manager = plot_manager
        self.current_plot_id = None
        self.init_ui()
        self.update_plot_list()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Панель фильтрации и поиска участков
        filter_panel = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск участков...")
        self.search_edit.textChanged.connect(self.update_plot_list)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['Все', 'Собственный', 'Арендованный'])
        self.filter_combo.currentTextChanged.connect(self.update_plot_list)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Все статусы', 'Новый', 'Подготовка почвы', 'Посев', 
                                   'Уход за посевами', 'Защита растений', 'Уборка урожая',
                                   'Послеуборочная обработка', 'Отдых'])
        self.status_filter.currentTextChanged.connect(self.update_plot_list)
        
        filter_panel.addWidget(self.search_edit)
        filter_panel.addWidget(QLabel("Фильтр:"))
        filter_panel.addWidget(self.filter_combo)
        filter_panel.addWidget(QLabel("Статус:"))
        filter_panel.addWidget(self.status_filter)

        # Список участков
        self.plots_list = QListWidget()
        self.plots_list.itemClicked.connect(self.on_plot_selected)
        
        # Кнопка для добавления работы
        self.add_work_btn = QPushButton("Добавить работу")
        self.add_work_btn.clicked.connect(self.show_work_wizard)
        self.add_work_btn.setEnabled(False)
        
        # Вкладки для информации
        self.tabs = QTabWidget()
        
        # Вкладка "Статус и информация"
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        self.status_label = QLabel("Статус: Не выбран")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.plot_info = QLabel()
        self.plot_info.setWordWrap(True)
        status_layout.addWidget(self.plot_info)
        
        # Вкладка "Работы"
        works_tab = QWidget()
        works_layout = QVBoxLayout(works_tab)
        
        # Панель сортировки работ
        sort_panel = QHBoxLayout()
        self.sort_works_combo = QComboBox()
        self.sort_works_combo.addItems(["По дате (новые)", "По дате (старые)", "По типу работы", "По статусу"])
        self.sort_works_combo.currentIndexChanged.connect(self.update_works_table)
        sort_panel.addWidget(QLabel("Сортировка:"))
        sort_panel.addWidget(self.sort_works_combo)
        sort_panel.addStretch()
        
        self.works_table = QTableWidget()
        self.works_table.setColumnCount(5)
        self.works_table.setHorizontalHeaderLabels(["Дата", "Тип работы", "Статус", "Ответственный", "Действия"])
        self.works_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.works_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.works_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.works_table.customContextMenuRequested.connect(self.show_work_context_menu)
        
        works_layout.addLayout(sort_panel)
        works_layout.addWidget(self.works_table)
        
        self.tabs.addTab(status_tab, "Информация")
        self.tabs.addTab(works_tab, "Работы")

        main_layout.addLayout(filter_panel)
        main_layout.addWidget(self.plots_list)
        main_layout.addWidget(self.add_work_btn)
        main_layout.addWidget(self.tabs)

    def show_work_context_menu(self, pos):
        row = self.works_table.rowAt(pos.y())
        if row >= 0:
            menu = QMenu()
            
            # Получаем текущий статус работы
            current_status = self.works_table.item(row, 2).text()
            
            # Добавляем действия для смены статуса
            statuses = ["Запланировано", "В процессе", "Завершено", "Отменено"]
            for status in statuses:
                if status != current_status:
                    action = menu.addAction(f"Изменить статус на: {status}")
                    action.setData((row, status))
                    action.triggered.connect(self.change_work_status)
            
            menu.exec_(self.works_table.viewport().mapToGlobal(pos))

    def change_work_status(self):
        action = self.sender()
        row, new_status = action.data()
    
        work_id = self.works_table.item(row, 0).data(Qt.UserRole)
    
        # Обновляем статус в базе данных
        self.plot_manager.db.execute(
            "UPDATE field_works SET status=? WHERE id=?",
            (new_status, work_id)
        )
    
        # Обновляем таблицу
        self.update_works_table()
    
        # Обновляем статус участка, если работа завершена
        if new_status == "Завершено":
            plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
            if plot:
                self.update_plot_info(plot)


    def update_plot_list(self):
        filter_type = self.filter_combo.currentText()
        if filter_type == 'Все':
            filter_type = None
            
        status_filter = self.status_filter.currentText()
        if status_filter == 'Все статусы':
            status_filter = None

        self.plots_list.clear()

        plots = self.plot_manager.get_all_plots(
            filter_type=filter_type,
            search_query=self.search_edit.text()
        )
        
        # Фильтрация по статусу
        if status_filter:
            plots = [p for p in plots if p.get('status') == status_filter]

        for plot in plots:
            plot_type = plot.get('type', 'Собственный')
            status = plot.get('status', 'Новый')
            
            item_text = f"{plot['id']}. {plot['name']} - {status}"
            self.plots_list.addItem(item_text)

    def on_plot_selected(self, item):
        try:
            self.current_plot_id = int(item.text().split(".")[0])
            plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
            
            if plot:
                self.add_work_btn.setEnabled(True)
                self.update_plot_info(plot)
                self.update_works_table()
        except Exception as e:
            print(f"Ошибка при выборе участка: {str(e)}")
            self.current_plot_id = None
            self.add_work_btn.setEnabled(False)

    def update_plot_info(self, plot):
        status = plot.get('status', 'Новый')
    
        # Определяем цвета для всех возможных статусов
        status_colors = {
            'Новый': 'gray',
            'Подготовка почвы': 'orange',
            'Посев': 'green',
            'Уход за посевами': 'blue',
            'Защита растений': 'purple',
            'Уборка урожая': 'darkgreen',
            'Послеуборочная обработка': 'brown',
            'Отдых': 'lightgray',
            'В обработке': 'orange',  # Добавлен для совместимости
            'Засеян': 'green',       # Добавлен для совместимости
            'Убран': 'darkgreen'     # Добавлен для совместимости
        }
    
        # Получаем цвет или используем черный по умолчанию
        color = status_colors.get(status, 'black')
    
        self.status_label.setText(f"Статус: <span style='color:{color}'>{status}</span>")
    
        info_text = f"""
        <b>Название:</b> {plot['name']}<br>
        <b>Площадь:</b> {plot.get('area_ha', plot.get('area', 0)):.2f} га<br>
        <b>Тип:</b> {plot.get('type', 'Собственный')}<br>
        <b>Кадастровый номер:</b> {plot.get('cadastral_number', 'не указан')}<br>
        <b>Адрес:</b> {plot.get('address', 'не указан')}
        """
    
        if plot.get('status') == 'Посев' or plot.get('status') == 'Засеян':
            last_sowing = self.plot_manager.db.fetch_one(
                "SELECT culture FROM field_works WHERE plot_id=? AND category='Посевные работы' ORDER BY work_date DESC LIMIT 1",
                (self.current_plot_id,)
            )
            if last_sowing:
                info_text += f"<br><b>Культура:</b> {last_sowing['culture']}"
    
        self.plot_info.setText(info_text)

    def update_works_table(self):
        if not self.current_plot_id:
            return
            
        self.works_table.setRowCount(0)
            
        # Определяем порядок сортировки
        sort_order = self.sort_works_combo.currentText()
        order_by = {
            "По дате (новые)": "work_date DESC",
            "По дате (старые)": "work_date ASC",
            "По типу работы": "work_type ASC",
            "По статусу": "status ASC"
        }.get(sort_order, "work_date DESC")

        works = self.plot_manager.db.fetch_all(
            f"SELECT * FROM field_works WHERE plot_id=? ORDER BY {order_by}",
            (self.current_plot_id,)
        )
        
        self.works_table.setRowCount(len(works))
        for row, work in enumerate(works):
            self.works_table.setItem(row, 0, QTableWidgetItem(work['work_date']))
            self.works_table.item(row, 0).setData(Qt.UserRole, work['id'])  # Сохраняем ID работы
            
            self.works_table.setItem(row, 1, QTableWidgetItem(work['work_type']))
            self.works_table.setItem(row, 2, QTableWidgetItem(work['status']))
            self.works_table.setItem(row, 3, QTableWidgetItem(work.get('worker', '')))
            
            btn = QPushButton("Изменить")
            btn.clicked.connect(self.create_work_handler(work))
            self.works_table.setCellWidget(row, 4, btn)

    def create_work_handler(self, work):
        def handler():
            self.edit_work(work)
        return handler

    def edit_work(self, work):
        dialog = FieldWorkWizard(self, self.current_plot_id, self.plot_manager, work)
        if dialog.exec_() == QDialog.Accepted:
            work_data = dialog.get_data()
            self.save_work(work_data, work['id'] if 'id' in work else None)
            self.update_works_table()
            self.update_plot_info(self.plot_manager.get_plot_by_id(self.current_plot_id))

    def show_work_wizard(self):
        if not self.current_plot_id:
            return
            
        dialog = FieldWorkWizard(self, self.current_plot_id, self.plot_manager)
        if dialog.exec_() == QDialog.Accepted:
            work_data = dialog.get_data()
            self.save_work(work_data)
            self.update_works_table()
            self.update_plot_info(self.plot_manager.get_plot_by_id(self.current_plot_id))

    def save_work(self, work_data, work_id=None):
        try:
            now = QDate.currentDate().toString("yyyy-MM-dd")
            
            if work_id:
                # Обновление существующей работы
                self.plot_manager.db.execute(
                    """UPDATE field_works SET 
                    category=?, work_type=?, work_date=?, status=?, 
                    worker=?, equipment=?, description=?, notes=?, 
                    culture=?, fertilizer=?, updated_at=?
                    WHERE id=?""",
                    (
                        work_data["category"],
                        work_data["work_type"],
                        work_data["work_date"],
                        work_data["status"],
                        work_data["worker"],
                        work_data["equipment"],
                        work_data["description"],
                        work_data["notes"],
                        work_data.get("culture"),
                        work_data.get("fertilizer"),
                        now,
                        work_id
                    )
                )
            else:
                # Добавление новой работы
                self.plot_manager.db.execute(
                    """INSERT INTO field_works 
                    (plot_id, category, work_type, work_date, status, 
                     worker, equipment, description, notes, culture, fertilizer,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        work_data["plot_id"],
                        work_data["category"],
                        work_data["work_type"],
                        work_data["work_date"],
                        work_data["status"],
                        work_data["worker"],
                        work_data["equipment"],
                        work_data["description"],
                        work_data["notes"],
                        work_data.get("culture"),
                        work_data.get("fertilizer"),
                        now,
                        now
                    )
                )
            
            # Обновляем статус участка при необходимости
            if work_data["status"] == 'Завершено':
                new_status = None
    
                if work_data["category"] == "Подготовка почвы":
                    new_status = "Подготовка почвы"
                elif work_data["category"] == "Посевные работы":
                    new_status = "Посев"
                elif work_data["category"] == "Уборка урожая":
                    new_status = "Уборка урожая"
                elif work_data["category"] == "Послеуборочная обработка":
                    new_status = "Отдых"
    
                if new_status:
                    self.plot_manager.db.execute(
                        "UPDATE plots SET status=? WHERE id=?",
                        (new_status, work_data["plot_id"])
                    )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить работу: {str(e)}")

    def handle_harvest(self, work_data):
        warehouses = self.plot_manager.db.fetch_all("SELECT id, name FROM warehouses")
        
        harvest_dialog = HarvestDialog(
            self, 
            self.plot_manager.db, 
            work_data["plot_id"],
            work_data.get("culture"), 
            warehouses
        )
        
        if harvest_dialog.exec_() == QDialog.Accepted:
            harvest_data = harvest_dialog.get_data()
            
            if not harvest_data['amount'] or harvest_data['amount'] <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество урожая должно быть больше 0")
                return
            
            harvest_id = self.plot_manager.db.execute(
                """INSERT INTO harvests 
                (plot_id, date, culture, amount)
                VALUES (?, ?, ?, ?)""",
                (
                    work_data["plot_id"],
                    harvest_data['date'],
                    harvest_data['culture'],
                    harvest_data['amount']
                )
            ).lastrowid
            
            if harvest_data.get('warehouse_id'):
                try:
                    self.plot_manager.db.execute(
                        """INSERT INTO warehouse_operations 
                        (warehouse_id, operation_type, culture, amount, operation_date, 
                         source, harvest_id, plot_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            harvest_data['warehouse_id'],
                            'incoming',
                            harvest_data['culture'],
                            harvest_data['amount'],
                            harvest_data['date'],
                            'Уборка урожая',
                            harvest_id,
                            work_data["plot_id"]
                        )
                    )
                    
                    current = self.plot_manager.db.fetch_one(
                        "SELECT amount FROM warehouse_stocks WHERE warehouse_id=? AND culture=?",
                        (harvest_data['warehouse_id'], harvest_data['culture'])
                    )
                
                    if current:
                        new_amount = current['amount'] + harvest_data['amount']
                        self.plot_manager.db.execute(
                            "UPDATE warehouse_stocks SET amount=? WHERE warehouse_id=? AND culture=?",
                            (new_amount, harvest_data['warehouse_id'], harvest_data['culture'])
                        )
                    else:
                        self.plot_manager.db.execute(
                            "INSERT INTO warehouse_stocks (warehouse_id, culture, amount) VALUES (?, ?, ?)",
                            (harvest_data['warehouse_id'], harvest_data['culture'], harvest_data['amount'])
                        )
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось добавить урожай на склад: {str(e)}")