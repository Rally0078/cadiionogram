import sys
from src.ui.mainwidget import MainWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CADI Ionogram Plotter")
        self.setCentralWidget(MainWidget())
        self.resize(1366, 768)
        self.setMinimumSize(1280, 720)
        self.showMaximized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
