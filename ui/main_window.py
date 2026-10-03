from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QStackedWidget,
    QMessageBox,
)

from ui.dashboard import DashboardPage
from ui.products import ProductsPage
from ui.sales import SalesPage
from ui.stock import StockPage
from ui.invoices import InvoicesPage
from ui.expenses import ExpensesPage
from ui.reports import ReportsPage
from ui.style import MODERN_STYLE


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application Pharmacie.

    Interface destinée aux utilisateurs WORKER.
    L'utilisateur connecté est reçu depuis la page de connexion.
    """

    def __init__(self, current_user=None):
        super().__init__()

        self.current_user = current_user

        self.setWindowTitle("Gestion de Pharmacie Desktop")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 650)

        self.setStyleSheet(MODERN_STYLE)

        self.setup_ui()

    # ==========================================================
    # INTERFACE PRINCIPALE
    # ==========================================================

    def setup_ui(self):
        """Construit toute l'interface principale."""

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ======================================================
        # SIDEBAR
        # ======================================================

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 15)
        sidebar_layout.setSpacing(8)

        # ======================================================
        # LOGO
        # ======================================================

        title = QLabel("🏥 PHARMACIE")
        title.setObjectName("brand")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sidebar_layout.addWidget(title)

        # ======================================================
        # UTILISATEUR CONNECTÉ
        # ======================================================

        user_frame = QFrame()
        user_frame.setObjectName("userFrame")

        user_layout = QVBoxLayout(user_frame)
        user_layout.setContentsMargins(10, 12, 10, 12)
        user_layout.setSpacing(3)

        user_name = self.get_user_name()
        user_role = self.get_user_role()

        self.user_name_label = QLabel(user_name)
        self.user_name_label.setObjectName("userName")
        self.user_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.user_role_label = QLabel(user_role)
        self.user_role_label.setObjectName("userRole")
        self.user_role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_layout.addWidget(self.user_name_label)
        user_layout.addWidget(self.user_role_label)

        sidebar_layout.addWidget(user_frame)

        sidebar_layout.addSpacing(15)

        # ======================================================
        # PAGES
        # ======================================================

        self.stack = QStackedWidget()

        self.pages = [
    DashboardPage(),
    ProductsPage(),
    SalesPage(),
    StockPage(),
    InvoicesPage(),
    ExpensesPage(),
    ReportsPage(),
]

        for page in self.pages:
            self.stack.addWidget(page)

        # ======================================================
        # NAVIGATION
        # ======================================================

        nav_items = [
            ("🏠  Tableau de bord", 0),
            ("💊  Produits", 1),
            ("🛒  Ventes", 2),
            ("📦  Stock", 3),
            ("🧾  Factures", 4),
            ("💰  Dépenses", 5),
            ("📊  Rapports", 6),
        ]

        self.buttons = []

        for text, index in nav_items:

            button = QPushButton(text)

            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)

            button.clicked.connect(
                lambda checked=False, i=index: self.go_to_page(i)
            )

            sidebar_layout.addWidget(button)
            self.buttons.append(button)

        # ======================================================
        # ESPACE FLEXIBLE
        # ======================================================

        sidebar_layout.addStretch()

        # ======================================================
        # DÉCONNEXION
        # ======================================================

        logout_button = QPushButton("🚪  Déconnexion")
        logout_button.setObjectName("logoutButton")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.setMinimumHeight(42)

        logout_button.clicked.connect(self.logout)

        sidebar_layout.addWidget(logout_button)

        # ======================================================
        # AJOUT À LA FENÊTRE
        # ======================================================

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

        # Première page
        self.go_to_page(0)

    # ==========================================================
    # UTILISATEUR
    # ==========================================================

    def get_user_name(self):
        """
        Retourne le nom de l'utilisateur connecté.

        Compatible avec :
        - objet SQLAlchemy User
        - dictionnaire
        """

        if self.current_user is None:
            return "Utilisateur"

        # Objet SQLAlchemy
        if hasattr(self.current_user, "full_name"):

            name = self.current_user.full_name

            if name:
                return str(name)

        # Dictionnaire
        if isinstance(self.current_user, dict):

            name = self.current_user.get("full_name")

            if name:
                return str(name)

        return "Utilisateur"

    def get_user_role(self):
        """Retourne le rôle de l'utilisateur connecté."""

        if self.current_user is None:
            return "WORKER"

        # Objet SQLAlchemy
        if hasattr(self.current_user, "role"):

            role = self.current_user.role

            if role:
                return str(role).upper()

        # Dictionnaire
        if isinstance(self.current_user, dict):

            role = self.current_user.get("role")

            if role:
                return str(role).upper()

        return "WORKER"

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def go_to_page(self, index):
        """
        Change la page affichée.
        """

        if index < 0 or index >= len(self.pages):
            return

        # Changer la page
        self.stack.setCurrentIndex(index)

        # Mettre à jour les boutons
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

        # Récupérer la page actuelle
        page = self.pages[index]

        # Rafraîchir automatiquement
        if hasattr(page, "refresh"):

            try:
                page.refresh()

            except Exception as error:

                print(
                    f"Erreur lors du rafraîchissement "
                    f"de la page {index}: {error}"
                )

    # ==========================================================
    # DÉCONNEXION
    # ==========================================================

    def logout(self):
        """Déconnecte l'utilisateur."""

        confirmation = QMessageBox.question(
            self,
            "Déconnexion",
            "Voulez-vous vraiment vous déconnecter ?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:

            from ui.login import LoginWindow

            self.login_window = LoginWindow()
            self.login_window.show()

            self.close()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir la page de connexion.\n\n{error}",
            )

    # ==========================================================
    # FERMETURE
    # ==========================================================

    def closeEvent(self, event):
        """Gestion de la fermeture de la fenêtre."""

        event.accept()