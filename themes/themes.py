# themes.py
# Стандарт (QSS-строка)
# themes/themes.py

LIGHT_STYLE = r"""
/* Базовые настройки для всех QWidget */
QWidget {
    background-color: #f0f8ff;  /* Очень светлый голубой фон */
    color: #0d47a1;             /* Тёмно-синий текст */
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}

/* QPushButton */
QPushButton {
    background-color: #ffffff;
    color: #0d47a1;
    border: 1px solid #64b5f6;  /* Светло-голубая рамка */
    border-radius: 4px;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #e3f2fd;  /* При наведении — более насыщенный голубой */
}
QPushButton:pressed {
    background-color: #bbdefb;  /* При нажатии — ещё более тёмная заливка */
}

/* QLineEdit и QComboBox */
QLineEdit, QComboBox {
    background-color: #ffffff;
    color: #0d47a1;
    border: 1px solid #64b5f6;
    border-radius: 4px;
    padding: 2px 4px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #1976d2;  /* Граница при фокусе — тёмно-синяя */
}

/* QTextEdit и QPlainTextEdit */
QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #0d47a1;
    border: 1px solid #64b5f6;
    border-radius: 4px;
    padding: 4px;
}

/* QListWidget */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #64b5f6;
    padding: 2px;
}
QListWidget::item {
    padding: 4px;
}
QListWidget::item:selected {
    background-color: #bbdefb;  /* Выбранный элемент — светло-голубой */
    color: #0d47a1;
}

/* QTableWidget */
QTableWidget {
    background-color: #ffffff;
    gridline-color: #bbdefb;
    selection-background-color: #bbdefb;
    selection-color: #0d47a1;
}
QTableWidget::item {
    padding: 2px;
}
QTableWidget::item:selected {
    background-color: #bbdefb;
    color: #0d47a1;
}
QHeaderView::section {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #90caf9, stop:1 #42a5f5
    );
    color: #ffffff;
    padding: 4px;
    border: 1px solid #64b5f6;
}
QHeaderView::section:hover {
    background-color: #bbdefb;
}

/* QTabWidget и QTabBar */
QTabWidget::pane {
    border: 1px solid #64b5f6;
    background-color: #e3f2fd;
    padding: 2px;
}
QTabBar::tab {
    background: #ffffff;
    border: 1px solid #64b5f6;
    border-bottom-color: #e3f2fd;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 4px 8px;
    margin-right: -1px;
}
QTabBar::tab:hover {
    background: #e3f2fd;
}
QTabBar::tab:selected {
    background: #e3f2fd;
    border-color: #1976d2;  /* Особая рамка у активной вкладки */
}

/* QTreeView и QTreeWidget */
QTreeView, QTreeWidget {
    background-color: #ffffff;
    gridline-color: #bbdefb;
}
QTreeView::item:selected, QTreeWidget::item:selected {
    background-color: #bbdefb;
    color: #0d47a1;
}

/* QMessageBox */
QMessageBox {
    background-color: #f0f8ff;
}

/* QToolTip */
QToolTip {
    background-color: #bbdefb;
    color: #0d47a1;
    border: 1px solid #64b5f6;
    padding: 4px;
    border-radius: 4px;
}

/* QScrollBar вертикальный */
QScrollBar:vertical {
    background: #e3f2fd;
    width: 12px;
    margin: 0px;
    border: 1px solid #64b5f6;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #64b5f6;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #42a5f5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}

/* QProgressBar */
QProgressBar {
    border: 1px solid #64b5f6;
    border-radius: 4px;
    text-align: center;
    background-color: #ffffff;
}
QProgressBar::chunk {
    background-color: #64b5f6;
    width: 10px;
}

/* QCheckBox и QRadioButton */
QCheckBox, QRadioButton {
    color: #0d47a1;
}
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #64b5f6;
    width: 12px;
    height: 12px;
    border-radius: 2px;
    background: #ffffff;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #64b5f6;
}

/* Дополнительные детали */
QSpacerItem, QSplitter, QFrame {
    background-color: transparent;
}

/* Стиль для QPushButton с иконками */
QPushButton[iconLoaded="true"] {
    padding-left: 32px;  /* Оставляем место для иконки */
}

/* Диалоги (QDialog) */
QDialog {
    background-color: #f0f8ff;
}

/* QComboBox раскрывающееся меню */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    selection-background-color: #bbdefb;
    selection-color: #0d47a1;
}

/* QMenu */
QMenu {
    background-color: #ffffff;
    border: 1px solid #64b5f6;
}
QMenu::item {
    padding: 4px 20px;
    background-color: transparent;
}
QMenu::item:selected {
    background-color: #bbdefb;
    color: #0d47a1;
}
"""


# Тёмная тема (QSS-строка)

DARK_STYLE = r"""
/* Основные настройки для всех QWidget */
QWidget {
    background-color: #202123;  /* общий фон */
    color: #d1d5db;             /* основной светлый текст */
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}

/* QPushButton */
QPushButton {
    background-color: #343541;  /* фон кнопок */
    color: #d1d5db;             /* текст кнопок */
    border: 1px solid #4b5563;  /* граница */
    border-radius: 4px;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #4b5563;  /* при наведении */
}
QPushButton:pressed {
    background-color: #3e4451;  /* при нажатии */
}

/* QLineEdit и QComboBox */
QLineEdit, QComboBox {
    background-color: #343541;
    color: #d1d5db;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 2px 4px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #10a37f;  /* акцентная рамка */
}

/* QTextEdit и QPlainTextEdit */
QTextEdit, QPlainTextEdit {
    background-color: #343541;
    color: #d1d5db;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 4px;
}

/* QListWidget */
QListWidget {
    background-color: #343541;
    border: 1px solid #4b5563;
    padding: 2px;
}
QListWidget::item {
    padding: 4px;
    color: #d1d5db;
}
QListWidget::item:selected {
    background-color: #10a37f;  /* зелёный акцент */
    color: #ffffff;
}

/* QTableWidget */
QTableWidget {
    background-color: #343541;
    gridline-color: #4b5563;
    selection-background-color: #10a37f;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 2px;
    color: #d1d5db;
}
QTableWidget::item:selected {
    background-color: #10a37f;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #343541;
    color: #d1d5db;
    padding: 4px;
    border: 1px solid #4b5563;
}
QHeaderView::section:hover {
    background-color: #4b5563;
}

/* QTabWidget и QTabBar */
QTabWidget::pane {
    border: 1px solid #4b5563;
    background-color: #202123;
    padding: 2px;
}
QTabBar::tab {
    background: #343541;
    border: 1px solid #4b5563;
    border-bottom-color: #202123;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 4px 8px;
    margin-right: -1px;
    color: #d1d5db;
}
QTabBar::tab:hover {
    background: #4b5563;
}
QTabBar::tab:selected {
    background: #4b5563;
    border-color: #10a37f;
    color: #ffffff;
}

/* QTreeView и QTreeWidget */
QTreeView, QTreeWidget {
    background-color: #343541;
    gridline-color: #4b5563;
}
QTreeView::item, QTreeWidget::item {
    color: #d1d5db;
}
QTreeView::item:selected, QTreeWidget::item:selected {
    background-color: #10a37f;
    color: #ffffff;
}

/* QMessageBox */
QMessageBox {
    background-color: #202123;
    color: #d1d5db;
}

/* QToolTip */
QToolTip {
    background-color: #4b5563;
    color: #ffffff;
    border: 1px solid #4b5563;
    padding: 4px;
    border-radius: 4px;
}

/* QScrollBar вертикальный */
QScrollBar:vertical {
    background: #202123;
    width: 12px;
    margin: 0px;
    border: 1px solid #4b5563;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #4b5563;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #10a37f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}

/* QProgressBar */
QProgressBar {
    border: 1px solid #4b5563;
    border-radius: 4px;
    text-align: center;
    background-color: #343541;
    color: #d1d5db;
}
QProgressBar::chunk {
    background-color: #10a37f;
    width: 10px;
}

/* QCheckBox и QRadioButton */
QCheckBox, QRadioButton {
    color: #d1d5db;
}
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #4b5563;
    width: 12px;
    height: 12px;
    border-radius: 2px;
    background: #343541;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #10a37f;
}

/* QComboBox раскрывающееся меню */
QComboBox QAbstractItemView {
    background-color: #343541;
    selection-background-color: #10a37f;
    selection-color: #ffffff;
}

/* QMenu */
QMenu {
    background-color: #343541;
    border: 1px solid #4b5563;
}
QMenu::item {
    padding: 4px 20px;
    background-color: transparent;
    color: #d1d5db;
}
QMenu::item:selected {
    background-color: #10a37f;
    color: #ffffff;
}

/* QDialog */
QDialog {
    background-color: #202123;
    color: #d1d5db;
}
"""
