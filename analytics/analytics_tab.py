##ui/analytics_tab.py
import os
import sqlite3
from datetime import datetime
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSizePolicy,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QSplitter,
    QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QSizePolicy
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
class SelectionDialog(QDialog):
    def __init__(self, title: str, items: list[str], selected: list[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 400)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for it in items:
            lw = QListWidgetItem(it)
            lw.setFlags(lw.flags() | Qt.ItemIsUserCheckable)
            lw.setCheckState(Qt.Checked if selected and it in selected else Qt.Unchecked)
            self.list_widget.addItem(lw)
        layout.addWidget(self.list_widget)
        btn_box = QHBoxLayout()
        ok = QPushButton("ОК")
        cancel = QPushButton("Отмена")
        btn_box.addWidget(ok)
        btn_box.addWidget(cancel)
        layout.addLayout(btn_box)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
    def get_selected(self) -> list[str]:
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]
class AnalyticsTab(QWidget):
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.abspath(os.path.join(base_dir, "..", "full_data.db"))
        self.db_path = db_path
        self.available_cultures = []
        self.available_plots = []
        self.selected_cultures = []
        self.selected_plots = []
        self._init_ui()
        self._load_filter_values()
    def _get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка подключения", f"Не удалось подключиться к базе:\n{e}")
            return None
    def _load_filter_values(self):
        conn = self._get_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT DISTINCT strftime('%Y', date) FROM harvests WHERE date IS NOT NULL ORDER BY 1 DESC;"
            )
            years = [row[0] for row in cursor.fetchall() if row[0]]

            cursor.execute("SELECT DISTINCT name FROM crops WHERE name IS NOT NULL;")
            cultures = sorted([row[0] for row in cursor.fetchall() if row[0]])

            cursor.execute("SELECT DISTINCT name FROM plots WHERE name IS NOT NULL;")
            plots = sorted([row[0] for row in cursor.fetchall() if row[0]])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка чтения данных", f"Не удалось считать фильтры:\n{e}")
            conn.close()
            return
        conn.close()
        self.year_start_combo.clear()
        self.year_end_combo.clear()
        self.year_start_combo.addItem("Все", None)
        self.year_end_combo.addItem("Все", None)
        for y in years:
            self.year_start_combo.addItem(y, y)
            self.year_end_combo.addItem(y, y)
        self.available_cultures = cultures
        self.available_plots = plots
        self.selected_cultures = []
        self.selected_plots = []
        self.btn_select_cult.setText("Выбрать культуры…")
        self.btn_select_plot.setText("Выбрать участки…")
    def _init_ui(self):
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск в таблице.")
        self.search_edit.textChanged.connect(self._filter_table_rows)
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.export_chart_btn = QPushButton("Сохранить график")
        self.export_chart_btn.clicked.connect(self._export_chart)
        self.export_table_btn = QPushButton("Экспорт таблицы")
        self.export_table_btn.clicked.connect(self._export_table)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(8, 8, 8, 8)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        card_font = QFont()
        card_font.setPointSize(10)
        card_font.setBold(True)
        self.total_label      = QLabel("Всего урожая: — т");      self.total_label.setFont(card_font)
        self.avg_label        = QLabel("Средний урожай: — т/участок"); self.avg_label.setFont(card_font)
        self.yield_avg_label  = QLabel("Средняя урожайность: — т/га"); self.yield_avg_label.setFont(card_font)
        self.count_label      = QLabel("Записей: —");           self.count_label.setFont(card_font)
        for lbl in (self.total_label, self.avg_label, self.yield_avg_label, self.count_label):
            top_layout.addWidget(lbl)
        top_layout.addStretch(1)
        lbl_start = QLabel("Год с:")
        self.year_start_combo = QComboBox(); self.year_start_combo.addItem("Все", None)
        lbl_end   = QLabel("по:")
        self.year_end_combo   = QComboBox(); self.year_end_combo.addItem("Все", None)
        for w in (lbl_start, self.year_start_combo, lbl_end, self.year_end_combo):
            top_layout.addWidget(w)
        lbl_cult = QLabel("Культуры:")
        self.btn_select_cult = QPushButton("Выбрать культуры…")
        self.btn_select_cult.clicked.connect(self.open_culture_dialog)
        lbl_plot = QLabel("Участки:")
        self.btn_select_plot = QPushButton("Выбрать участки…")
        self.btn_select_plot.clicked.connect(self.open_plot_dialog)
        for w in (lbl_cult, self.btn_select_cult, lbl_plot, self.btn_select_plot):
            top_layout.addWidget(w)
        lbl_metric = QLabel("Метрика:")
        self.metric_combo = QComboBox()
        for text, data in [
            ("Общий урожай (т)", "total_harvest"),
            ("Урожайность (т/га)", "yield"),
            ("Расход семян (т)", "total_sowing"),
            ("Расход удобрений (т)", "total_fertilizer"),
            ("Урожай на 1 т семян", "harvest_per_sowing"),
            ("Урожай на 1 т удобрений", "harvest_per_fertilizer")
        ]:
            self.metric_combo.addItem(text, data)
        lbl_chart = QLabel("Вид графика:")
        self.chart_combo = QComboBox()
        for text, data in [
            ("Столбчатая (по участкам)", "bar_plot"),
            ("Столбчатая (по культурам)", "bar_culture"),
            ("Динамика (линейный)", "line_trend"),
            ("Круговая диаграмма", "pie")
        ]:
            self.chart_combo.addItem(text, data)
        self.show_button = QPushButton("Показать")
        self.show_button.clicked.connect(self.update_analytics)
        for w in (lbl_metric, self.metric_combo, lbl_chart, self.chart_combo, self.show_button):
            top_layout.addWidget(w)

        main_layout.addLayout(top_layout)
        from PyQt5.QtWidgets import QSplitter, QSizePolicy
        from PyQt5.QtCore import Qt
        splitter = QSplitter(Qt.Horizontal)
        left_frame = QWidget()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.toolbar)
        left_layout.addWidget(self.canvas)
        left_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_frame = QWidget()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.search_edit)
        right_layout.addWidget(self.table)
        right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setMinimumWidth(800)
        main_layout.addWidget(splitter)
        bottom_layout = QHBoxLayout()
        self.info_label = QLabel("Данные актуальны на: —, источник – full_data.db")
        bottom_layout.addWidget(self.info_label)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.export_chart_btn)
        bottom_layout.addWidget(self.export_table_btn)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def open_culture_dialog(self):
        dlg = SelectionDialog("Выбор культур", self.available_cultures, self.selected_cultures, self)
        if dlg.exec_() == QDialog.Accepted:
            self.selected_cultures = dlg.get_selected()
            text = f"Культуры: {len(self.selected_cultures)} выбрано" if self.selected_cultures else "Выбрать культуры…"
            self.btn_select_cult.setText(text)

    def open_plot_dialog(self):
        dlg = SelectionDialog("Выбор участков", self.available_plots, self.selected_plots, self)
        if dlg.exec_() == QDialog.Accepted:
            self.selected_plots = dlg.get_selected()
            text = f"Участки: {len(self.selected_plots)} выбрано" if self.selected_plots else "Выбрать участки…"
            self.btn_select_plot.setText(text)

    def _build_query(self):
        where_clauses = []
        params = {}
        y_start = self.year_start_combo.currentData()
        y_end = self.year_end_combo.currentData()
        if y_start and y_end:
            if int(y_start) > int(y_end):
                y_start, y_end = y_end, y_start
            where_clauses.append("CAST(strftime('%Y', h.date) AS INTEGER) BETWEEN :y_start AND :y_end")
            params['y_start'], params['y_end'] = int(y_start), int(y_end)
        elif y_start:
            where_clauses.append("CAST(strftime('%Y', h.date) AS INTEGER) >= :y_start")
            params['y_start'] = int(y_start)
        elif y_end:
            where_clauses.append("CAST(strftime('%Y', h.date) AS INTEGER) <= :y_end")
            params['y_end'] = int(y_end)
        if self.selected_cultures:
            placeholders = ", ".join(f":cult_{i}" for i in range(len(self.selected_cultures)))
            where_clauses.append(f"h.culture IN ({placeholders})")
            for i, cult in enumerate(self.selected_cultures):
                params[f'cult_{i}'] = cult
        if self.selected_plots:
            placeholders = ", ".join(f":plot_{i}" for i in range(len(self.selected_plots)))
            where_clauses.append(f"p.name IN ({placeholders})")
            for i, plot in enumerate(self.selected_plots):
                params[f'plot_{i}'] = plot

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT
                p.name AS plot,
                p.area AS area,
                h.culture AS culture,
                CAST(strftime('%Y', h.date) AS INTEGER) AS year,
                SUM(h.amount) AS total_harvest,
                SUM(COALESCE(s.quantity, 0)) AS total_sowing,
                SUM(COALESCE(f.quantity, 0)) AS total_fertilizer
            FROM harvests h
            LEFT JOIN plots p ON h.plot_id = p.id
            LEFT JOIN sowing_use s ON s.field_id = h.plot_id AND s.name = h.culture AND strftime('%Y', s.date) = strftime('%Y', h.date)
            LEFT JOIN fertilizer_use f ON f.field_id = h.plot_id AND strftime('%Y', f.date) = strftime('%Y', h.date)
            {where_sql}
            GROUP BY p.name, h.culture, CAST(strftime('%Y', h.date) AS INTEGER)
            ORDER BY year DESC, culture, plot;
        """
        return query, params

    def update_analytics(self):
        query, params = self._build_query()
        conn = self._get_connection()
        if conn is None:
            return
        try:
            df = pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка SQL", f"Не удалось выполнить запрос:\n{e}")
            conn.close()
            return
        finally:
            conn.close()
        if df.empty:
            self.figure.clear()
            self.canvas.draw()
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            QMessageBox.information(self, "Нет данных", "По заданным фильтрам нет записей.")
            self.total_label.setText("Всего урожая: — т")
            self.avg_label.setText("Средний урожай: — т/участок")
            self.yield_avg_label.setText("Средняя урожайность: — т/га")
            self.count_label.setText("Записей: 0")
            self.info_label.setText(
                f"Данные актуальны на: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}, источник – full_data.db"
            )
            return
        df['yield'] = df.apply(
            lambda row: (row['total_harvest'] / row['area']) if (row['area'] and row['area'] > 0) else 0,
            axis=1
        )
        df['harvest_per_sowing'] = df.apply(
            lambda row: (row['total_harvest'] / row['total_sowing']) if (row['total_sowing'] and row['total_sowing'] > 0) else 0,
            axis=1
        )
        df['harvest_per_fertilizer'] = df.apply(
            lambda row: (row['total_harvest'] / row['total_fertilizer']) if (row['total_fertilizer'] and row['total_fertilizer'] > 0) else 0,
            axis=1
        )
        total_harvest_sum = df['total_harvest'].sum()
        count_records = len(df)
        avg_harvest = total_harvest_sum / count_records if count_records else 0
        total_area_for_yield = df[['plot', 'area']].drop_duplicates(subset=['plot'])['area'].sum()
        avg_yield = (total_harvest_sum / total_area_for_yield) if total_area_for_yield > 0 else 0
        self.total_label.setText(f"Всего урожая: {total_harvest_sum:.1f} т")
        self.avg_label.setText(f"Средний урожай: {avg_harvest:.1f} т/участок")
        self.yield_avg_label.setText(f"Средняя урожайность: {avg_yield:.2f} т/га")
        self.count_label.setText(f"Записей: {count_records}")
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        metric = self.metric_combo.currentData()
        chart_type = self.chart_combo.currentData()
        try:
            if chart_type == "bar_plot":
                group_plot = df.groupby(['plot', 'area']).agg(
                    total_harvest_sum=pd.NamedAgg(column='total_harvest', aggfunc='sum'),
                    total_sowing=pd.NamedAgg(column='total_sowing', aggfunc='sum'),
                    total_fertilizer=pd.NamedAgg(column='total_fertilizer', aggfunc='sum'),
                    yield_sum=pd.NamedAgg(column='yield', aggfunc='mean'),
                    harvest_per_sowing=pd.NamedAgg(column='harvest_per_sowing', aggfunc='mean'),
                    harvest_per_fertilizer=pd.NamedAgg(column='harvest_per_fertilizer', aggfunc='mean'),
                ).reset_index()
                if metric == "total_harvest":
                    values = group_plot['total_harvest_sum']
                elif metric == "total_sowing":
                    values = group_plot['total_sowing']
                elif metric == "total_fertilizer":
                    values = group_plot['total_fertilizer']
                elif metric == "harvest_per_sowing":
                    values = group_plot['harvest_per_sowing']
                elif metric == "harvest_per_fertilizer":
                    values = group_plot['harvest_per_fertilizer']
                else:
                    values = group_plot['yield_sum']
                labels = group_plot['plot']
                ax.bar(labels, values)
                ax.set_xlabel("Участок")
                ylabel = self.metric_combo.currentText()
                ax.set_ylabel(ylabel)
                ax.set_title(f"{self.metric_combo.currentText()} по участкам")
                ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
                for rect, val in zip(ax.patches, values):
                    ax.text(
                        rect.get_x() + rect.get_width() / 2,
                        val + (0.5 if metric in ["total_harvest", "total_sowing", "total_fertilizer"] else 0.05),
                        f"{val:.2f}",
                        ha='center',
                        va='bottom',
                        fontsize=8
                    )
            elif chart_type == "bar_culture":
                group_cult = df.groupby('culture').agg(
                    total_harvest_sum=pd.NamedAgg(column='total_harvest', aggfunc='sum'),
                    total_sowing=pd.NamedAgg(column='total_sowing', aggfunc='sum'),
                    total_fertilizer=pd.NamedAgg(column='total_fertilizer', aggfunc='sum'),
                    yield_sum=pd.NamedAgg(column='yield', aggfunc='mean'),
                    harvest_per_sowing=pd.NamedAgg(column='harvest_per_sowing', aggfunc='mean'),
                    harvest_per_fertilizer=pd.NamedAgg(column='harvest_per_fertilizer', aggfunc='mean'),
                )
                if metric == "total_harvest":
                    values = group_cult['total_harvest_sum']
                elif metric == "total_sowing":
                    values = group_cult['total_sowing']
                elif metric == "total_fertilizer":
                    values = group_cult['total_fertilizer']
                elif metric == "harvest_per_sowing":
                    values = group_cult['harvest_per_sowing']
                elif metric == "harvest_per_fertilizer":
                    values = group_cult['harvest_per_fertilizer']
                else:
                    values = group_cult['yield_sum']
                labels = group_cult.index.tolist()
                ax.bar(labels, values)
                ax.set_xlabel("Культура")
                ylabel = self.metric_combo.currentText()
                ax.set_ylabel(ylabel)
                ax.set_title(f"{self.metric_combo.currentText()} по культурам")
                ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
                for rect, val in zip(ax.patches, values):
                    ax.text(
                        rect.get_x() + rect.get_width() / 2,
                        val + (0.5 if metric in ["total_harvest", "total_sowing", "total_fertilizer"] else 0.05),
                        f"{val:.2f}",
                        ha='center',
                        va='bottom',
                        fontsize=8
                    )
            elif chart_type == "line_trend":
                df_trend = df.groupby(['year', 'culture']).agg(
                    value_sum=pd.NamedAgg(column=metric, aggfunc='sum')
                ).reset_index()
                cultures_in_data = df_trend['culture'].unique()
                for cult in cultures_in_data:
                    data_cult = df_trend[df_trend['culture'] == cult].sort_values('year')
                    ax.plot(data_cult['year'], data_cult['value_sum'], marker='o', label=cult)
                    for x, y in zip(data_cult['year'], data_cult['value_sum']):
                        ax.text(
                            x,
                            y + 0.05,
                            f"{y:.2f}",
                            ha='center',
                            va='bottom',
                            fontsize=7
                        )
                ax.set_xlabel("Год")
                ylabel = self.metric_combo.currentText()
                ax.set_ylabel(ylabel)
                ax.set_title(f"Динамика {self.metric_combo.currentText().lower()} по культурам")
                ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
                ax.legend(fontsize=8)
            elif chart_type == "pie":
                selected_plots = [
                    item.text() for item_index in range(self.plot_list.count())
                    for item in [self.plot_list.item(item_index)]
                    if item.checkState() == Qt.Checked
                ]
                if selected_plots:
                    group_plot = df.groupby(['plot', 'area']).agg(
                        value=pd.NamedAgg(column=metric, aggfunc='sum')
                    ).reset_index()
                    sizes = group_plot['value']
                    labels = group_plot['plot']
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax.set_title(f"Доля {self.metric_combo.currentText().lower()} по участкам")
                else:
                    group_cult = df.groupby('culture').agg(
                        value=pd.NamedAgg(column=metric, aggfunc='sum')
                    )
                    sizes = group_cult['value']
                    labels = group_cult.index.tolist()
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax.set_title(f"Доля {self.metric_combo.currentText().lower()} по культурам")
            else:
                ax.text(0.5, 0.5, "Выберите корректный тип графика.", ha='center', va='center')
        except Exception as e:
            QMessageBox.warning(self, "Ошибка построения графика", f"Произошла ошибка:\n{e}")
        self.canvas.draw()
        headers = [
            "Участок", "Культура", "Год", "Урожай, т", "Площадь, га", "Урожайность, т/га",
            "Расход семян, т", "Расход удобрений, т", "Урожай/т семян", "Урожай/т удобр."
        ]
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            item_plot = QTableWidgetItem(str(row['plot']))
            item_cult = QTableWidgetItem(str(row['culture']))
            item_year = QTableWidgetItem(str(int(row['year'])))
            item_th = QTableWidgetItem(f"{row['total_harvest']:.2f}")
            item_area = QTableWidgetItem(f"{row['area']:.2f}")
            yld = row['yield']
            item_yld = QTableWidgetItem(f"{yld:.2f}")
            item_sowing = QTableWidgetItem(f"{row['total_sowing']:.2f}")
            item_fert = QTableWidgetItem(f"{row['total_fertilizer']:.2f}")
            item_hps = QTableWidgetItem(f"{row['harvest_per_sowing']:.2f}")
            item_hpf = QTableWidgetItem(f"{row['harvest_per_fertilizer']:.2f}")
            self.table.setItem(i, 0, item_plot)
            self.table.setItem(i, 1, item_cult)
            self.table.setItem(i, 2, item_year)
            self.table.setItem(i, 3, item_th)
            self.table.setItem(i, 4, item_area)
            self.table.setItem(i, 5, item_yld)
            self.table.setItem(i, 6, item_sowing)
            self.table.setItem(i, 7, item_fert)
            self.table.setItem(i, 8, item_hps)
            self.table.setItem(i, 9, item_hpf)
            if yld < 2.0:
                item_yld.setBackground(QBrush(QColor(255, 200, 200)))
            elif yld > 5.0:
                item_yld.setBackground(QBrush(QColor(200, 255, 200)))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        self.info_label.setText(f"Данные актуальны на: {now_str}, источник – full_data.db")

    def _filter_table_rows(self, text: str):
        """Скрывает строки таблицы, в которых нет введённого текста."""
        text = text.lower()
        for i in range(self.table.rowCount()):
            row_hidden = True
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text in item.text().lower():
                    row_hidden = False
                    break
            self.table.setRowHidden(i, row_hidden)

    def _export_chart(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график как PNG", "", "PNG Files (*.png);;All Files (*)", options=options
        )
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300)
                QMessageBox.information(self, "Сохранено", f"График сохранён: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка сохранения", f"Не удалось сохранить график:\n{e}")

    def _export_table(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Нет данных", "Нет данных для экспорта.")
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт таблицы в CSV", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if file_path:
            cols = [self.table.horizontalHeaderItem(j).text() for j in range(self.table.columnCount())]
            data = []
            for i in range(self.table.rowCount()):
                row_data = []
                for j in range(self.table.columnCount()):
                    item = self.table.item(i, j)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            df_export = pd.DataFrame(data, columns=cols)
            try:
                df_export.to_csv(file_path, index=False, sep=';', encoding='utf-8-sig')
                QMessageBox.information(self, "Экспорт завершён", f"Таблица сохранена: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка экспорта", f"Не удалось сохранить таблицу:\n{e}")
