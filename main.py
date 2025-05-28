##main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from map.map_loader import cleanup_temp_files

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(cleanup_temp_files)
    sys.exit(app.exec_())