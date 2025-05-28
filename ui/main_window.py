##main_window.py

import json
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QDateEdit, QAbstractItemView,
    QHeaderView, QMessageBox, QCheckBox, QGroupBox, QDialog, QMenu
)
from PyQt5.QtCore import Qt, QDate
from ui.equipment_tab import EquipmentTab  
from map.map_widget import MapWidget  
from controllers.land_plots_manager import LandPlotManager  
from ui.plot_wizard import PlotWizard  
from controllers.harvest_manager import HarvestManager  
from ui.warehouse_tab import WarehouseTab  
from ui.field_work_tab import FieldWorkTab  

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = "full_data.db"
        self.plot_manager = LandPlotManager(self.db_path)
        self.plot_manager.db.update_table_structure()
        self.current_plot_id = None
        self.harvest_manager = HarvestManager(self.plot_manager)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Управление сельскохозяйственными участками")
        self.setGeometry(100, 100, 1400, 900)
  
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
    
        # Вкладка "Участки"
        self.plots_tab = QWidget()
        self.init_plots_tab()
        self.tab_widget.addTab(self.plots_tab, "Участки")
    
        # Вкладка "Работа с полями"
        self.field_work_tab = FieldWorkTab(self, self.plot_manager)
        self.tab_widget.addTab(self.field_work_tab, "Работа с полями")
    
        # Вкладка "Склады"
        self.warehouses_tab = WarehouseTab(self, self.plot_manager)
        self.tab_widget.addTab(self.warehouses_tab, "Склады")

        self.equipment_tab = EquipmentTab(self, self.plot_manager.db)
        self.tab_widget.addTab(self.equipment_tab, "Техника")
    
        self.statusBar().showMessage("Готово")
        self.update_plot_list()

    def init_plots_tab(self):
        main_layout = QHBoxLayout(self.plots_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Левая панель - список участков
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        # Панель управления
        control_panel = QHBoxLayout()
        self.add_plot_btn = QPushButton("Добавить участок")
        self.add_plot_btn.clicked.connect(self.show_plot_wizard)
        
        self.crops_btn = QPushButton("Культуры")
        self.crops_btn.clicked.connect(self.show_crops_window)
        
        self.workers_btn = QPushButton("Рабочие")
        self.workers_btn.clicked.connect(self.show_workers_window)
        
        control_panel.addWidget(self.add_plot_btn)
        control_panel.addWidget(self.crops_btn)
        control_panel.addWidget(self.workers_btn)

        # Панель фильтров
        filter_panel = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск участков...")
        self.search_edit.textChanged.connect(self.update_plot_list)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['Все', 'Собственный', 'Арендованный'])
        self.filter_combo.currentTextChanged.connect(self.update_plot_list)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['По названию', 'По площади', 'По типу'])
        self.sort_combo.currentTextChanged.connect(self.update_plot_list)
        
        filter_panel.addWidget(self.search_edit)
        filter_panel.addWidget(QLabel("Фильтр:"))
        filter_panel.addWidget(self.filter_combo)
        filter_panel.addWidget(QLabel("Сортировка:"))
        filter_panel.addWidget(self.sort_combo)

        # Список участков
        self.plots_list = QListWidget()
        self.plots_list.itemClicked.connect(self.on_plot_selected)
        self.plots_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.plots_list.customContextMenuRequested.connect(self.show_plot_context_menu)
        
        left_panel.addLayout(control_panel)
        left_panel.addLayout(filter_panel)
        left_panel.addWidget(self.plots_list)

        # Правая панель - карта
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(800, 500)
        
        self.show_all_plots_check = QCheckBox("Показать все участки")
        self.show_all_plots_check.stateChanged.connect(self.toggle_all_plots_display)
        
        right_panel.addWidget(self.show_all_plots_check)
        right_panel.addWidget(self.map_widget, stretch=2)

        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=5)

    def on_plot_selected(self, item):
        """Обработчик выбора участка из списка"""
        try:
            # Получаем ID участка из текста элемента списка
            self.current_plot_id = int(item.text().split(".")[0])
            plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
        
            if plot:
                # Обрабатываем координаты (могут быть строкой JSON или уже списком)
                coordinates = plot.get('coordinates')
                if isinstance(coordinates, str):
                    try:
                        coordinates = json.loads(coordinates)
                    except json.JSONDecodeError:
                        coordinates = []
            
                # Обновляем карту
                if coordinates:
                    if self.show_all_plots_check.isChecked():
                        # В режиме показа всех участков просто выделяем выбранный
                        self.map_widget.highlight_plot(
                            coordinates,
                            plot.get('name', ''),
                            plot.get('status', 'Новый')
                        )
                    else:
                        # В обычном режиме показываем только выбранный участок
                        self.map_widget.clear_plot()
                        self.map_widget.draw_plot(
                            coordinates,
                            plot.get('name', ''),
                            plot.get('status', 'Новый'),
                            zoom_to=True
                        )
        except Exception as e:
            print(f"Ошибка при выборе участка: {str(e)}")
            self.current_plot_id = None
        
    def toggle_all_plots_display(self, state):
        if state == Qt.Checked:
            plots = self.plot_manager.get_all_plots()
            plots_with_info = []
            for plot in plots:
                if plot.get('coordinates'):
                    plots_with_info.append({
                        'id': plot['id'],
                        'coordinates': plot['coordinates'],
                        'name': plot.get('name', ''),
                        'status': plot.get('status', 'Новый')
                    })
            self.map_widget.draw_all_plots(plots_with_info)
        
            if self.current_plot_id:
                plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
                if plot and plot.get('coordinates'):
                    self.map_widget.highlight_plot(
                        plot['coordinates'], 
                        plot.get('name', ''),
                        plot.get('status', 'Новый')
                    )
        else:
            self.map_widget.clear_all_plots()
            if self.current_plot_id:
                plot = self.plot_manager.get_plot_by_id(self.current_plot_id)
                if plot and plot.get('coordinates'):
                    self.map_widget.draw_plot(
                        plot['coordinates'], 
                        plot.get('name', ''),
                        plot.get('status', 'Новый'),
                        zoom_to=True
                    )


    def update_plot_list(self):
        sort_mapping = {
            'По названию': 'name',
            'По площади': 'area',
            'По типу': 'type'
        }
    
        filter_type = self.filter_combo.currentText()
        if filter_type == 'Все':
            filter_type = None
    
        self.plots_list.clear()
    
        plots = self.plot_manager.get_all_plots(
            sort_key=sort_mapping[self.sort_combo.currentText()],
            filter_type=filter_type,
            search_query=self.search_edit.text()
        )
    
        for plot in plots:
            plot_type = plot.get('type', 'Собственный')
            rental_info = ""
            status = plot.get('status', 'Новый')
        
            if plot_type == 'Арендованный' and plot.get('rental_expiry_date'):
                expiry_date = plot['rental_expiry_date']
                rental_info = f" (Аренда до: {expiry_date})"
        
            item_text = f"{plot['id']}. {plot['name']} - {plot.get('area_ha', plot.get('area', 0)):.2f} га ({status}){rental_info}"
            self.plots_list.addItem(item_text)

    def show_plot_context_menu(self, pos):
        item = self.plots_list.itemAt(pos)
        if item:
            menu = QMenu()
            edit_action = menu.addAction("Редактировать")
            delete_action = menu.addAction("Удалить")
            
            action = menu.exec_(self.plots_list.mapToGlobal(pos))
            
            if action == edit_action:
                self.edit_plot(item)
            elif action == delete_action:
                self.delete_plot(item)

    def edit_plot(self, item):
        try:
            plot_id = int(item.text().split(".")[0])
            plot = self.plot_manager.get_plot_by_id(plot_id)
        
            if not plot:
                QMessageBox.warning(self, "Ошибка", "Участок не найден")
                return
            
            dialog = PlotWizard(self, self.plot_manager)  
            dialog.plot_name_edit.setText(plot.get('name', ''))
            dialog.plot_type_combo.setCurrentText(plot.get('type', 'Собственный'))
            dialog.cadastral_edit.setText(plot.get('cadastral_number', ''))
            dialog.property_type_edit.setText(plot.get('property_type', 'Земельный участок'))
        
            if plot.get('assignment_date'):
                try:
                    dialog.date_edit.setDate(QDate.fromString(plot['assignment_date'], "yyyy-MM-dd"))
                except:
                    dialog.date_edit.setDate(QDate.currentDate())
        
            dialog.address_edit.setText(plot.get('address', ''))
            area_sqm = plot.get('area_sqm', 0) or 0
            dialog.area_sqm_edit.setValue(float(area_sqm))
            area_ha = plot.get('area_ha', plot.get('area', 0)) or 0
            dialog.area_ha_edit.setValue(float(area_ha))
            dialog.land_category_edit.setText(plot.get('land_category', 'Земли сельскохозяйственного назначения'))
            dialog.land_use_edit.setText(plot.get('land_use', 'Для сельскохозяйственного производства'))
            cadastral_value = plot.get('cadastral_value', 0) or 0
            dialog.cadastral_value_edit.setValue(float(cadastral_value))
            dialog.owner_name_edit.setText(plot.get('owner_name', ''))
            dialog.owner_contacts_edit.setText(plot.get('owner_contacts', ''))
        
            if plot.get('coordinates'):
                try:
                    dialog.coordinates = plot['coordinates']
                    dialog.display_saved_coordinates()
                except:
                    dialog.coordinates = []
        
            if plot.get('type') == 'Арендованный' and plot.get('rental_expiry_date'):
                try:
                    dialog.rental_expiry_date.setDate(QDate.fromString(plot['rental_expiry_date'], "yyyy-MM-dd"))
                except:
                    dialog.rental_expiry_date.setDate(QDate.currentDate().addYears(1))
        
            dialog.plot_id = plot_id
        
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                self.plot_manager.update_plot(
                    plot_id,
                    name=new_data['name'],
                    coordinates=new_data['coordinates'],
                    area=new_data['area_ha'],
                    plot_type=new_data['plot_type'],
                    additional_data={
                        "cadastral_number": new_data["cadastral_number"],
                        "property_type": new_data["property_type"],
                        "assignment_date": new_data["assignment_date"],
                        "address": new_data["address"],
                        "area_sqm": new_data["area_sqm"],
                        "land_category": new_data["land_category"],
                        "land_use": new_data["land_use"],
                        "cadastral_value": new_data["cadastral_value"],
                        "owner_name": new_data["owner_name"],
                        "owner_contacts": new_data["owner_contacts"],
                        "rental_expiry_date": new_data.get("rental_expiry_date")
                    }
                )
                self.update_plot_list()
                self.on_plot_selected(item)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактирование: {str(e)}")

    def delete_plot(self, item):
        plot_id = int(item.text().split(".")[0])
        if QMessageBox.question(
            self, 
            "Удаление участка", 
            "Вы уверены, что хотите удалить этот участок?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.plot_manager.delete_plot(plot_id)
            self.update_plot_list()
            if self.current_plot_id == plot_id:
                self.current_plot_id = None
                self.map_widget.clear_plot()

    def show_plot_wizard(self):
        wizard = PlotWizard(self, self.plot_manager)
        if wizard.exec_() == QDialog.Accepted:
            plot_data = wizard.get_data()
            self.save_new_plot(plot_data)

    def save_new_plot(self, plot_data):
        try:
            self.plot_manager.add_plot(
                name=plot_data["name"],
                coordinates=plot_data["coordinates"],
                area=plot_data["area_ha"],
                plot_type=plot_data["plot_type"],
                additional_data={
                    "cadastral_number": plot_data["cadastral_number"],
                    "property_type": plot_data["property_type"],
                    "assignment_date": plot_data["assignment_date"],
                    "address": plot_data["address"],
                    "area_sqm": plot_data["area_sqm"],
                    "land_category": plot_data["land_category"],
                    "land_use": plot_data["land_use"],
                    "cadastral_value": plot_data["cadastral_value"],
                    "owner_name": plot_data["owner_name"],
                    "owner_contacts": plot_data["owner_contacts"],
                    "rental_expiry_date": plot_data.get("rental_expiry_date")
                }
            )
            self.update_plot_list()
            # Обновляем список участков во вкладке работы с полями
            self.field_work_tab.update_plot_list()
            QMessageBox.information(self, "Успех", "Участок успешно добавлен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить участок: {str(e)}")

    def show_crops_window(self):
        from crops_window import CropsWindow
        dialog = CropsWindow(self.plot_manager.db, self)
        dialog.exec_()

    def show_workers_window(self):
        from workers_window import WorkersWindow
        dialog = WorkersWindow(self.plot_manager.db, self)
        dialog.exec_()

    def optimized_close(self):
        if hasattr(self, 'map_widget'):
            self.map_widget.setHtml('')
            self.map_widget.page().deleteLater()
            self.map_widget.close()

        if hasattr(self, 'plot_manager') and hasattr(self.plot_manager, 'db'):
            self.plot_manager.db.close()

        if hasattr(self, 'plots_list'):
            self.plots_list.clear()
        
    def closeEvent(self, event):
        self.optimized_close()
        super().closeEvent(event)