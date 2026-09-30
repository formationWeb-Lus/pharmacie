from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget
from ui.dashboard import DashboardPage
from ui.products import ProductsPage
from ui.sales import SalesPage
from ui.stock import StockPage
from ui.invoices import InvoicesPage
from ui.reports import ReportsPage
from ui.style import MODERN_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion de Pharmacie Desktop")
        self.resize(1200, 750)
        self.setStyleSheet(MODERN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)

        title = QLabel("🏥 PHARMACIE")
        title.setObjectName("brand")
        side_layout.addWidget(title)

        self.stack = QStackedWidget()
        self.pages = [
            DashboardPage(),
            ProductsPage(),
            SalesPage(),
            StockPage(),
            InvoicesPage(),
            ReportsPage()
        ]
        for p in self.pages:
            self.stack.addWidget(p)

        nav_items = [
            ("🏠 Tableau de bord", 0),
            ("💊 Produits", 1),
            ("🛒 Ventes", 2),
            ("📦 Stock", 3),
            ("🧾 Factures", 4),
            ("📊 Rapports", 5),
        ]

        self.buttons = []
        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=idx: self.go_to_page(i))
            side_layout.addWidget(btn)
            self.buttons.append(btn)

        side_layout.addStretch()

        layout.addWidget(sidebar)
        layout.addWidget(self.stack)

        self.go_to_page(0)

    def go_to_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)

        page = self.pages[index]
        if hasattr(page, "refresh"):
            page.refresh()