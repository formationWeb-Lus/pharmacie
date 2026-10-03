import sys

from PySide6.QtWidgets import QApplication

from database.database import init_db
from database.user_database import init_user_database
from ui.login import LoginWindow


def main():
    # Initialisation de la base de données
    init_db()

    # Initialisation de la table des utilisateurs
    init_user_database()

    # Application Qt
    app = QApplication(sys.argv)

    app.setApplicationName("Pharmacie")
    app.setOrganizationName("Pharmacie")

    # -------------------------------------------------
    # IMPORTANT :
    # On démarre TOUJOURS par la connexion.
    # -------------------------------------------------
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()