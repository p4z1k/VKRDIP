##ui/main_window.py
import json
import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QListWidget, QListWidgetItem, QStackedWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QDateEdit, QHeaderView, QMessageBox, QCheckBox,
    QAction, QMenu, qApp, QSizePolicy, QDialog, QApplication
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QIcon
from themes.themes import DARK_STYLE, LIGHT_STYLE
from ui.equipment_tab import EquipmentTab
from map.map_widget import MapWidget
from controllers.land_plots_manager import LandPlotManager
from ui.plot_wizard import PlotWizard
from ui.warehouse_tab import WarehouseTab
from ui.crops_fertilizers_tab import CropsFertilizersTab
from ui.field_work_tab import FieldWorkTab
from ui.workers_tab import WorkersTab
from analytics.analytics_tab import AnalyticsTab
from document_manager.document_manager import DocumentManagerDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = "full_data.db"
        self.plot_manager = LandPlotManager(self.db_path)
        self.plot_manager.db.update_table_structure()
        self.current_plot_id = None
        qApp.setStyleSheet(LIGHT_STYLE)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("СУУСХП")
        self.setGeometry(100, 100, 1400, 900)
        menubar = self.menuBar()
        theme_menu = menubar.addMenu("Тема")
        light_action = QAction("Светлая", self)
        light_action.triggered.connect(self.set_light_theme)
        theme_menu.addAction(light_action)
        dark_action = QAction("Тёмная", self)
        dark_action.triggered.connect(self.set_dark_theme)
        theme_menu.addAction(dark_action)
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        self.sidebar = QListWidget()
        self.sidebar.setIconSize(QSize(32, 32))
        self.sidebar.setSpacing(5)
        self.sidebar.setMovement(QListWidget.Static)
        self.sidebar.setMaximumWidth(200)
        self.sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        item_plots      = QListWidgetItem(QIcon(os.path.join(icons_dir, "plots.png")),          "Участки")
        item_fieldwork  = QListWidgetItem(QIcon(os.path.join(icons_dir, "field_work.png")),     "Работа с полями")
        item_warehouses = QListWidgetItem(QIcon(os.path.join(icons_dir, "warehouse.png")),      "Склады")
        item_crops      = QListWidgetItem(QIcon(os.path.join(icons_dir, "crops.png")),          "Культуры и удобрения")
        item_workers    = QListWidgetItem(QIcon(os.path.join(icons_dir, "workers.png")),        "Рабочие")
        item_equipment  = QListWidgetItem(QIcon(os.path.join(icons_dir, "equipment.png")),      "Техника")
        item_analytics  = QListWidgetItem(QIcon(os.path.join(icons_dir, "analytics.png")),      "Аналитика")
        for itm in (
            item_plots, item_fieldwork, item_warehouses,
            item_crops, item_workers, item_equipment, item_analytics
        ):
            itm.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.sidebar.addItem(itm)
        self.stack = QStackedWidget()
        self.plots_tab      = QWidget()
        self.init_plots_tab()  
        self.field_work_tab = FieldWorkTab(self.plot_manager.db, self)
        self.warehouses_tab = WarehouseTab(self, self.plot_manager)
        self.crops_ferts_tab= CropsFertilizersTab(self.plot_manager.db)
        self.workers_tab    = WorkersTab(self.plot_manager.db)
        self.equipment_tab  = EquipmentTab(self, self.plot_manager.db)
        self.analytics_tab  = AnalyticsTab(db_path=self.db_path)
        self.stack.addWidget(self.plots_tab)
        self.stack.addWidget(self.field_work_tab)
        self.stack.addWidget(self.warehouses_tab)
        self.stack.addWidget(self.crops_ferts_tab)
        self.stack.addWidget(self.workers_tab)
        self.stack.addWidget(self.equipment_tab)
        self.stack.addWidget(self.analytics_tab)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setCentralWidget(container)
        self.statusBar().showMessage("Готово")
        self.update_plot_list()

    def set_light_theme(self):
        qApp.setStyleSheet(LIGHT_STYLE)

    def set_dark_theme(self):
        qApp.setStyleSheet(DARK_STYLE)

    def init_plots_tab(self):
        main_layout = QHBoxLayout(self.plots_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        control_panel = QHBoxLayout()
        self.add_plot_btn = QPushButton("Добавить участок")
        self.add_plot_btn.clicked.connect(self.show_plot_wizard)
        control_panel.addWidget(self.add_plot_btn)
        left_panel.addLayout(control_panel)
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
        left_panel.addLayout(filter_panel)
        self.plots_list = QListWidget()
        self.plots_list.itemClicked.connect(self.on_plot_selected)
        self.plots_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.plots_list.customContextMenuRequested.connect(self.show_plot_context_menu)
        left_panel.addWidget(self.plots_list)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(800, 500)
        self.show_all_plots_check = QCheckBox("Показать все участки")
        self.show_all_plots_check.stateChanged.connect(self.toggle_all_plots_display)
        self.docs_btn = QPushButton("Документы участка")
        self.docs_btn.setEnabled(False)
        self.docs_btn.clicked.connect(self.open_plot_documents)
        right_panel.addWidget(self.show_all_plots_check)
        right_panel.addWidget(self.map_widget, stretch=2)
        right_panel.addWidget(self.docs_btn)
        main_layout.addLayout(left_panel, stretch=2)
        main_layout.addLayout(right_panel, stretch=5)

    def update_plot_list(self):
        try:
            self.plots_list.clear()
            filter_type = self.filter_combo.currentText()
            if filter_type == 'Все':
                filter_type = None
            sort_mapping = {
                'По названию': 'name',
                'По площади': 'area',
                'По типу': 'type'
            }
            sort_key = sort_mapping[self.sort_combo.currentText()]
            plots = self.plot_manager.get_all_plots(
                sort_key=sort_key,
                filter_type=filter_type,
                search_query=self.search_edit.text()
            )
            for plot in plots:
                plot_type = plot.get('type', 'Собственный')
                rental_info = ""
                status = plot.get('status', 'Новый')
                crop = plot.get('crop', '').strip()
                if plot_type == 'Арендованный' and plot.get('rental_expiry_date'):
                    expiry_date = plot['rental_expiry_date']
                    rental_info = f" (Аренда до: {expiry_date})"
                area = plot.get('area_ha', plot.get('area', 0))
                item_text = f"{plot['id']}. {plot['name']} - {area:.2f} га ({status})"
                if crop:
                    item_text += f" [{crop}]"
                item_text += rental_info
                self.plots_list.addItem(item_text)
            if self.show_all_plots_check.isChecked():
                plots_with_info = []
                for plot in plots:
                    coords = plot.get('coordinates')
                    if isinstance(coords, str):
                        try:
                            coords = json.loads(coords)
                        except json.JSONDecodeError:
                            coords = []
                    if coords:
                        plots_with_info.append({
                            'id': plot.get('id'),
                            'coordinates': coords,
                            'name': plot.get('name', ''),
                            'status': plot.get('status', 'Новый'),
                            'crop': plot.get('crop', '') 
                        })
                self.map_widget.draw_all_plots(plots_with_info)
                self.show_all_plots = True
            else:
                self.map_widget.clear_all_plots()
                self.show_all_plots = False
        except Exception as e:
            print(f"Ошибка при обновлении списка участков: {e}")

    def on_plot_selected(self, item):
        try:
            plot_id = int(item.text().split(".")[0])
            self.current_plot_id = plot_id
            self.docs_btn.setEnabled(True)
            plot = self.plot_manager.get_plot_by_id(plot_id)
            if plot:
                coords = plot.get('coordinates')
                if isinstance(coords, str):
                    try:
                        coords = json.loads(coords)
                    except json.JSONDecodeError:
                        coords = []
                if coords:
                    name = plot.get('name', '')
                    status = plot.get('status', 'Новый')
                    crop = plot.get('crop', '')
                    if self.show_all_plots_check.isChecked():
                        self.map_widget.highlight_plot(coords, name, status, crop)
                    else:
                        self.map_widget.clear_plot()
                        self.map_widget.draw_plot(coords, name, status, crop, zoom_to=True)
                else:
                    self.map_widget.clear_plot()
        except Exception as e:
            print(f"Ошибка при выборе участка: {e}")
            self.current_plot_id = None
            self.docs_btn.setEnabled(False)

    def toggle_all_plots_display(self, state):
        try:
            if state == Qt.Checked:
                plots = self.plot_manager.get_all_plots()
                plots_with_info = []
                for plot in plots:
                    coords = plot.get('coordinates')
                    if isinstance(coords, str):
                        try:
                            coords = json.loads(coords)
                        except json.JSONDecodeError:
                            coords = []
                    if coords:
                        plots_with_info.append({
                            'id': plot.get('id'),
                            'coordinates': coords,
                            'name': plot.get('name', ''),
                            'status': plot.get('status', 'Новый'),
                            'crop': plot.get('crop', '')
                        })
                self.map_widget.draw_all_plots(plots_with_info)
                self.show_all_plots = True
            else:
                self.map_widget.clear_all_plots()
                self.show_all_plots = False
        except Exception as e:
            print(f"Ошибка при переключении «Показать все участки»: {e}")

    def show_plot_context_menu(self, pos):
        item = self.plots_list.itemAt(pos)
        if not item:
            return
        menu = QMenu()
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        action = menu.exec_(self.plots_list.mapToGlobal(pos))
        plot_id = int(item.text().split(".")[0])
        if action == edit_action:
            self.edit_plot(item)
        elif action == delete_action:
            self.delete_plot(item)

    def edit_plot(self, item):
        plot_id = int(item.text().split(".")[0])
        try:
            plot = self.plot_manager.get_plot_by_id(plot_id)
            dialog = PlotWizard(self, self.plot_manager)
            dialog.plot_name_edit.setText(plot.get('name', ''))
            area_ha = plot.get('area_ha') if plot.get('area_ha') is not None else plot.get('area', 0) / 10000
            dialog.area_ha_edit.setValue(area_ha)
            dialog.plot_type_combo.setCurrentText(plot.get('type', 'Собственный'))
            dialog.cadastral_edit.setText(plot.get('cadastral_number', ''))
            dialog.address_edit.setText(plot.get('address', ''))
            dialog.land_category_edit.setText(plot.get('land_category', ''))
            dialog.land_use_edit.setText(plot.get('land_use', ''))
            cadastral_value = plot.get('cadastral_value', 0) or 0
            dialog.cadastral_value_edit.setValue(float(cadastral_value))
            dialog.owner_name_edit.setText(plot.get('owner_name', ''))
            dialog.owner_contacts_edit.setText(plot.get('owner_contacts', ''))
            if plot.get('type') == 'Арендованный' and plot.get('rental_expiry_date'):
                try:
                    dialog.rental_expiry_date.setDate(
                        QDate.fromString(plot['rental_expiry_date'], "yyyy-MM-dd")
                    )
                except:
                    dialog.rental_expiry_date.setDate(QDate.currentDate().addYears(1))
            dialog.plot_id = plot_id
            coords = plot.get('coordinates')
            if coords:
                try:
                    if isinstance(coords, str):
                        coords = json.loads(coords)
                    dialog.coordinates = coords
                    dialog.display_saved_coordinates()
                except Exception:
                    dialog.coordinates = []
            if dialog.exec_() == QDialog.Accepted:
                self.update_plot_list()
                self.refresh_related_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось редактировать участок: {e}")

    def delete_plot(self, item):
        plot_id = int(item.text().split(".")[0])
        reply = QMessageBox.question(
            self, "Удалить участок",
            f"Вы уверены, что хотите удалить участок #{plot_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.plot_manager.delete_plot(plot_id)
                self.update_plot_list()
                self.map_widget.clear_all_plots()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить участок: {e}")

    def show_plot_wizard(self):
        dialog = PlotWizard(self, self.plot_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.update_plot_list()

    def open_plot_documents(self):
        if not self.current_plot_id:
            return
        dialog = DocumentManagerDialog(self.current_plot_id, self.plot_manager.db, parent=self)
        dialog.exec_()

    def refresh_related_data(self):
        self.update_plot_list()
        if hasattr(self, 'field_work_tab') and self.stack.currentIndex() == 1:
            self.field_work_tab.refresh_everything()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
