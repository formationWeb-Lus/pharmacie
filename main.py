import sys
from PySide6.QtWidgets import QApplication
from database.database import init_db
from ui.main_window import MainWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Pharmacie")
    app.setOrganizationName("Pharmacie")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
