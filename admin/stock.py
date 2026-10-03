from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFrame,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
)

from database.database import (
    SessionLocal,
    calculate_product_global_stock,
    get_stock_display,
    is_batch_expired,
    is_batch_expiring_soon,
)

from database.models import (
    Product,
    ProductBatch,
)


# ============================================================
# FORMATAGE
# ============================================================

def format_money(value):
    try:
        value = float(value or 0)

        return (
            f"{value:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
        )

    except Exception:
        return "0,00"


def format_number(value):
    try:
        value = float(value or 0)

        if value.is_integer():
            return f"{int(value):,}".replace(",", " ")

        return (
            f"{value:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
        )

    except Exception:
        return "0"


def format_date(value):

    if not value:
        return "-"

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    return str(value)


# ============================================================
# PAGE STOCK ADMIN
# ============================================================

class StockPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("StockPage")

        self.setup_ui()
        self.apply_styles()
        self.load_stock()

    # ========================================================
    # INTERFACE PRINCIPALE
    # ========================================================

    def setup_ui(self):

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        outer_layout.addWidget(scroll)

        # ====================================================
        # CONTENU
        # ====================================================

        content = QWidget()

        content.setObjectName("stockContent")

        scroll.setWidget(content)

        main_layout = QVBoxLayout(content)

        main_layout.setContentsMargins(
            30,
            28,
            30,
            40,
        )

        main_layout.setSpacing(22)

        # ====================================================
        # EN-TÊTE
        # ====================================================

        header = QHBoxLayout()

        header.setSpacing(20)

        title_container = QVBoxLayout()

        title_container.setSpacing(5)

        title = QLabel(
            "Gestion du stock"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Contrôlez les produits, les quantités, les lots, "
            "les expirations et la valeur financière du stock."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(True)

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header.addLayout(
            title_container,
            1
        )

        refresh_button = QPushButton(
            "↻  Actualiser"
        )

        refresh_button.setObjectName(
            "refreshButton"
        )

        refresh_button.setMinimumSize(
            145,
            46
        )

        refresh_button.clicked.connect(
            self.load_stock
        )

        header.addWidget(
            refresh_button,
            0,
            Qt.AlignTop
        )

        main_layout.addLayout(header)

        # ====================================================
        # LIGNE STATUT ADMIN
        # ====================================================

        status_bar = QFrame()

        status_bar.setObjectName(
            "adminStatusBar"
        )

        status_layout = QHBoxLayout(
            status_bar
        )

        status_layout.setContentsMargins(
            18,
            12,
            18,
            12
        )

        status_layout.setSpacing(10)

        status_icon = QLabel("●")

        status_icon.setObjectName(
            "statusIcon"
        )

        status_text = QLabel(
            "Surveillance du stock active"
        )

        status_text.setObjectName(
            "statusText"
        )

        status_description = QLabel(
            "Les indicateurs sont calculés à partir des stocks enregistrés."
        )

        status_description.setObjectName(
            "statusDescription"
        )

        status_layout.addWidget(
            status_icon
        )

        status_layout.addWidget(
            status_text
        )

        status_layout.addWidget(
            status_description
        )

        status_layout.addStretch()

        main_layout.addWidget(
            status_bar
        )

        # ====================================================
        # TITRE STATISTIQUES
        # ====================================================

        statistics_title = QLabel(
            "Vue financière et opérationnelle"
        )

        statistics_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            statistics_title
        )

        # ====================================================
        # CARTES
        # ====================================================

        stats_layout = QGridLayout()

        stats_layout.setHorizontalSpacing(16)
        stats_layout.setVerticalSpacing(16)

        # Première ligne

        self.products_card = self.create_stat_card(
            "Produits",
            "0",
            "Produits enregistrés",
            "▣",
            "blue"
        )

        self.stock_units_card = self.create_stat_card(
            "Stock total",
            "0",
            "Unités disponibles",
            "▤",
            "green"
        )

        self.purchase_value_card = self.create_stat_card(
            "Valeur du stock",
            "0,00",
            "Prix d'achat total",
            "₣",
            "orange"
        )

        self.sale_value_card = self.create_stat_card(
            "Valeur potentielle",
            "0,00",
            "Prix de vente total",
            "◆",
            "purple"
        )

        stats_layout.addWidget(
            self.products_card,
            0,
            0
        )

        stats_layout.addWidget(
            self.stock_units_card,
            0,
            1
        )

        stats_layout.addWidget(
            self.purchase_value_card,
            0,
            2
        )

        stats_layout.addWidget(
            self.sale_value_card,
            0,
            3
        )

        # Deuxième ligne

        self.low_stock_card = self.create_stat_card(
            "Stock faible",
            "0",
            "Produits à réapprovisionner",
            "!",
            "red"
        )

        self.expiring_card = self.create_stat_card(
            "Expiration proche",
            "0",
            "Lots dans les 30 jours",
            "◷",
            "orange"
        )

        self.expired_card = self.create_stat_card(
            "Produits expirés",
            "0",
            "Lots nécessitant une action",
            "×",
            "darkred"
        )

        self.available_card = self.create_stat_card(
            "Stock disponible",
            "0",
            "Produits sans alerte",
            "✓",
            "teal"
        )

        stats_layout.addWidget(
            self.low_stock_card,
            1,
            0
        )

        stats_layout.addWidget(
            self.expiring_card,
            1,
            1
        )

        stats_layout.addWidget(
            self.expired_card,
            1,
            2
        )

        stats_layout.addWidget(
            self.available_card,
            1,
            3
        )

        main_layout.addLayout(
            stats_layout
        )

        # ====================================================
        # FILTRES
        # ====================================================

        filters_title = QLabel(
            "Recherche et filtres"
        )

        filters_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            filters_title
        )

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "filterFrame"
        )

        filter_layout = QGridLayout(
            filter_frame
        )

        filter_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        filter_layout.setHorizontalSpacing(12)
        filter_layout.setVerticalSpacing(8)

        # Recherche

        search_label = QLabel(
            "Rechercher un produit"
        )

        search_label.setObjectName(
            "filterLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Nom, catégorie ou numéro de lot..."
        )

        self.search_input.setMinimumHeight(
            44
        )

        self.search_input.textChanged.connect(
            self.load_stock
        )

        filter_layout.addWidget(
            search_label,
            0,
            0
        )

        filter_layout.addWidget(
            self.search_input,
            1,
            0
        )

        # Catégorie

        category_label = QLabel(
            "Catégorie"
        )

        category_label.setObjectName(
            "filterLabel"
        )

        self.category_filter = QComboBox()

        self.category_filter.setMinimumHeight(
            44
        )

        self.category_filter.currentTextChanged.connect(
            self.load_stock
        )

        filter_layout.addWidget(
            category_label,
            0,
            1
        )

        filter_layout.addWidget(
            self.category_filter,
            1,
            1
        )

        # État

        status_label = QLabel(
            "État du stock"
        )

        status_label.setObjectName(
            "filterLabel"
        )

        self.status_filter = QComboBox()

        self.status_filter.setMinimumHeight(
            44
        )

        self.status_filter.addItems([
            "Tous",
            "Stock disponible",
            "Stock faible",
            "Rupture",
            "Expiration proche",
            "Expiré",
        ])

        self.status_filter.currentTextChanged.connect(
            self.load_stock
        )

        filter_layout.addWidget(
            status_label,
            0,
            2
        )

        filter_layout.addWidget(
            self.status_filter,
            1,
            2
        )

        # Bouton effacer

        clear_button = QPushButton(
            "Réinitialiser"
        )

        clear_button.setObjectName(
            "clearButton"
        )

        clear_button.setMinimumHeight(
            44
        )

        clear_button.clicked.connect(
            self.clear_filters
        )

        filter_layout.addWidget(
            clear_button,
            1,
            3
        )

        filter_layout.setColumnStretch(
            0,
            3
        )

        filter_layout.setColumnStretch(
            1,
            1
        )

        filter_layout.setColumnStretch(
            2,
            1
        )

        filter_layout.setColumnStretch(
            3,
            0
        )

        main_layout.addWidget(
            filter_frame
        )

        # ====================================================
        # TITRE TABLEAU
        # ====================================================

        table_header = QHBoxLayout()

        table_title = QLabel(
            "Inventaire détaillé"
        )

        table_title.setObjectName(
            "sectionTitle"
        )

        table_header.addWidget(
            table_title
        )

        table_header.addStretch()

        self.result_count = QLabel(
            "0 produit"
        )

        self.result_count.setObjectName(
            "resultCount"
        )

        table_header.addWidget(
            self.result_count
        )

        main_layout.addLayout(
            table_header
        )

        # ====================================================
        # TABLEAU
        # ====================================================

        self.stock_table = QTableWidget()

        self.stock_table.setColumnCount(
            10
        )

        self.stock_table.setHorizontalHeaderLabels([
            "Produit",
            "Catégorie",
            "Conditionnement",
            "Stock",
            "Stock base",
            "Valeur achat",
            "Valeur vente",
            "Lot",
            "Expiration",
            "État",
        ])

        self.stock_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.stock_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.stock_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.stock_table.verticalHeader().setVisible(
            False
        )

        self.stock_table.setAlternatingRowColors(
            True
        )

        self.stock_table.setMinimumHeight(
            500
        )

        self.stock_table.setWordWrap(False)

        header_view = self.stock_table.horizontalHeader()

        header_view.setStretchLastSection(False)

        header_view.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        for column in [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
        ]:

            header_view.setSectionResizeMode(
                column,
                QHeaderView.ResizeToContents
            )

        self.stock_table.cellDoubleClicked.connect(
            self.on_row_double_clicked
        )

        main_layout.addWidget(
            self.stock_table
        )

        # ====================================================
        # NOTE ADMIN
        # ====================================================

        note = QLabel(
            "Conseil administrateur : double-cliquez sur un produit "
            "pour consulter le détail de ses lots, son stock et ses prix."
        )

        note.setObjectName(
            "adminNote"
        )

        note.setWordWrap(True)

        main_layout.addWidget(
            note
        )

        # espace inférieur

        bottom_space = QWidget()

        bottom_space.setMinimumHeight(
            20
        )

        main_layout.addWidget(
            bottom_space
        )

    # ========================================================
    # CARTE STATISTIQUE
    # ========================================================

    def create_stat_card(
        self,
        title,
        value,
        description,
        icon,
        color_name
    ):

        card = QFrame()

        card.setObjectName(
            f"statCard_{color_name}"
        )

        card.setMinimumHeight(
            155
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20,
            17,
            20,
            17
        )

        layout.setSpacing(
            5
        )

        # Ligne supérieure

        top = QHBoxLayout()

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "statTitle"
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setObjectName(
            f"statIcon_{color_name}"
        )

        icon_label.setAlignment(
            Qt.AlignCenter
        )

        icon_label.setFixedSize(
            38,
            38
        )

        top.addWidget(
            title_label
        )

        top.addStretch()

        top.addWidget(
            icon_label
        )

        layout.addLayout(
            top
        )

        # Chiffre

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "statValue"
        )

        value_label.setMinimumHeight(
            52
        )

        value_label.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        value_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        value_label.setWordWrap(
            False
        )

        layout.addWidget(
            value_label
        )

        # Description

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "statDescription"
        )

        description_label.setWordWrap(
            True
        )

        layout.addWidget(
            description_label
        )

        card.value_label = value_label

        return card

    # ========================================================
    # STYLES
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""

            /* ==================================================
               PAGE
               ================================================== */

            QWidget#StockPage {
                background-color: #f1f5f9;
                color: #0f172a;
            }

            QWidget#stockContent {
                background-color: #f1f5f9;
            }


            /* ==================================================
               TITRES
               ================================================== */

            QLabel#pageTitle {
                color: #0f172a;
                font-size: 30px;
                font-weight: 800;
            }

            QLabel#pageSubtitle {
                color: #64748b;
                font-size: 14px;
            }

            QLabel#sectionTitle {
                color: #0f172a;
                font-size: 18px;
                font-weight: 750;
                padding-top: 4px;
            }


            /* ==================================================
               BARRE ADMIN
               ================================================== */

            QFrame#adminStatusBar {
                background-color: #ecfdf5;
                border: 1px solid #bbf7d0;
                border-radius: 12px;
            }

            QLabel#statusIcon {
                color: #16a34a;
                font-size: 14px;
                font-weight: 900;
            }

            QLabel#statusText {
                color: #166534;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#statusDescription {
                color: #4d7c5c;
                font-size: 12px;
            }


            /* ==================================================
               BOUTON ACTUALISER
               ================================================== */

            QPushButton#refreshButton {
                background-color: #0f766e;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#refreshButton:hover {
                background-color: #115e59;
            }

            QPushButton#refreshButton:pressed {
                background-color: #134e4a;
            }


            /* ==================================================
               CARTES STATISTIQUES
               ================================================== */

            QFrame#statCard_blue,
            QFrame#statCard_green,
            QFrame#statCard_orange,
            QFrame#statCard_purple,
            QFrame#statCard_red,
            QFrame#statCard_darkred,
            QFrame#statCard_teal {

                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 15px;
            }

            QFrame#statCard_blue {
                border-left: 5px solid #2563eb;
            }

            QFrame#statCard_green {
                border-left: 5px solid #16a34a;
            }

            QFrame#statCard_orange {
                border-left: 5px solid #ea580c;
            }

            QFrame#statCard_purple {
                border-left: 5px solid #7c3aed;
            }

            QFrame#statCard_red {
                border-left: 5px solid #dc2626;
            }

            QFrame#statCard_darkred {
                border-left: 5px solid #991b1b;
            }

            QFrame#statCard_teal {
                border-left: 5px solid #0f766e;
            }


            QLabel#statTitle {
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#statValue {
                color: #0f172a;
                font-size: 28px;
                font-weight: 850;
                padding-top: 3px;
                padding-bottom: 3px;
            }

            QLabel#statDescription {
                color: #94a3b8;
                font-size: 11px;
                font-weight: 500;
            }


            QLabel#statIcon_blue {
                background-color: #dbeafe;
                color: #2563eb;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_green {
                background-color: #dcfce7;
                color: #16a34a;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_orange {
                background-color: #ffedd5;
                color: #ea580c;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_purple {
                background-color: #ede9fe;
                color: #7c3aed;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_red {
                background-color: #fee2e2;
                color: #dc2626;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_darkred {
                background-color: #fee2e2;
                color: #991b1b;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }

            QLabel#statIcon_teal {
                background-color: #ccfbf1;
                color: #0f766e;
                border-radius: 19px;
                font-size: 17px;
                font-weight: 900;
            }


            /* ==================================================
               FILTRES
               ================================================== */

            QFrame#filterFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }

            QLabel#filterLabel {
                color: #334155;
                font-size: 12px;
                font-weight: 700;
            }

            QLineEdit,
            QComboBox {

                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 7px 11px;
                color: #0f172a;
                font-size: 13px;
                min-height: 28px;
            }

            QLineEdit:hover,
            QComboBox:hover {
                border: 1px solid #94a3b8;
            }

            QLineEdit:focus,
            QComboBox:focus {
                background-color: white;
                border: 2px solid #0f766e;
            }


            QPushButton#clearButton {
                background-color: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 8px 18px;
                font-weight: 700;
            }

            QPushButton#clearButton:hover {
                background-color: #e2e8f0;
            }


            /* ==================================================
               TABLEAU
               ================================================== */

            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                gridline-color: #e2e8f0;
                color: #0f172a;
                selection-background-color: #ccfbf1;
                selection-color: #0f172a;
                font-size: 12px;
                outline: none;
            }

            QTableWidget::item {
                padding: 9px 7px;
                border-bottom: 1px solid #f1f5f9;
            }

            QTableWidget::item:selected {
                background-color: #ccfbf1;
                color: #0f172a;
            }

            QHeaderView::section {
                background-color: #0f172a;
                color: white;
                padding: 11px 8px;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }

            QHeaderView::section:first {
                border-top-left-radius: 10px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 10px;
            }


            /* ==================================================
               RESULTAT
               ================================================== */

            QLabel#resultCount {
                color: #64748b;
                background-color: #e2e8f0;
                border-radius: 12px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 700;
            }


            /* ==================================================
               NOTE ADMIN
               ================================================== */

            QLabel#adminNote {
                background-color: #f8fafc;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 9px;
                padding: 10px 14px;
                font-size: 11px;
            }


            /* ==================================================
               SCROLLBAR
               ================================================== */

            QScrollBar:vertical {
                background-color: #e2e8f0;
                width: 11px;
                margin: 2px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #94a3b8;
                min-height: 40px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #64748b;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

        """)

    # ========================================================
    # CHARGEMENT DU STOCK
    # ========================================================

    def load_stock(self):

        session = SessionLocal()

        try:

            search = (
                self.search_input
                .text()
                .strip()
                .lower()
            )

            selected_category = (
                self.category_filter.currentText()
            )

            selected_status = (
                self.status_filter.currentText()
            )

            products = (
                session.query(Product)
                .order_by(Product.name.asc())
                .all()
            )

            # =================================================
            # CATÉGORIES
            # =================================================

            categories = sorted(
                {
                    str(product.category).strip()
                    for product in products
                    if product.category
                    and str(product.category).strip()
                }
            )

            current_category = (
                self.category_filter.currentText()
            )

            self.category_filter.blockSignals(
                True
            )

            self.category_filter.clear()

            self.category_filter.addItem(
                "Toutes"
            )

            self.category_filter.addItems(
                categories
            )

            if (
                current_category
                and current_category in categories
            ):

                self.category_filter.setCurrentText(
                    current_category
                )

            else:

                self.category_filter.setCurrentIndex(
                    0
                )

            self.category_filter.blockSignals(
                False
            )

            # =================================================
            # DONNÉES
            # =================================================

            rows = []

            total_products = 0
            total_stock_units = 0
            total_purchase_value = 0
            total_sale_value = 0

            low_stock_count = 0
            expiring_count = 0
            expired_count = 0
            available_count = 0

            for product in products:

                product_name = str(
                    product.name or ""
                )

                category = str(
                    product.category or ""
                )

                # Recherche

                if search:

                    searchable = (
                        f"{product_name} "
                        f"{category} "
                        f"{product.batch_number or ''}"
                    ).lower()

                    if search not in searchable:
                        continue

                # Catégorie

                if (
                    selected_category
                    and selected_category != "Toutes"
                    and category != selected_category
                ):
                    continue

                # Stock

                stock_units = self.get_product_stock(
                    session,
                    product
                )

                stock_units = float(
                    stock_units or 0
                )

                stock_display = (
                    self.get_stock_display_safe(
                        product,
                        stock_units
                    )
                )

                # Lots

                batches = (
                    session.query(ProductBatch)
                    .filter(
                        ProductBatch.product_id
                        == product.id
                    )
                    .order_by(
                        ProductBatch.expiry_date.asc()
                    )
                    .all()
                )

                active_batches = [
                    batch
                    for batch in batches
                    if float(
                        batch.stock_units or 0
                    ) > 0
                ]

                # États

                is_low = (
                    self.is_product_low_stock(
                        product,
                        stock_units
                    )
                )

                has_expired = False
                has_expiring = False

                for batch in batches:

                    batch_stock = float(
                        batch.stock_units or 0
                    )

                    if batch_stock <= 0:
                        continue

                    try:

                        if is_batch_expired(
                            batch
                        ):
                            has_expired = True

                        elif is_batch_expiring_soon(
                            batch
                        ):
                            has_expiring = True

                    except Exception:

                        expiry_status = (
                            self.get_expiry_status(
                                batch.expiry_date
                            )
                        )

                        if expiry_status == "expired":
                            has_expired = True

                        elif expiry_status == "soon":
                            has_expiring = True

                # Compteurs

                total_products += 1
                total_stock_units += stock_units

                if is_low:
                    low_stock_count += 1

                if has_expiring:
                    expiring_count += 1

                if has_expired:
                    expired_count += 1

                if (
                    stock_units > 0
                    and not is_low
                    and not has_expired
                    and not has_expiring
                ):
                    available_count += 1

                # Valeur achat

                purchase_price = float(
                    product.purchase_price or 0
                )

                purchase_value = (
                    stock_units
                    * purchase_price
                )

                total_purchase_value += (
                    purchase_value
                )

                # Valeur vente

                sale_value = (
                    self.calculate_sale_value(
                        product,
                        stock_units
                    )
                )

                total_sale_value += (
                    sale_value
                )

                # Filtre état

                if not self.match_status_filter(
                    selected_status,
                    stock_units,
                    is_low,
                    has_expired,
                    has_expiring
                ):
                    continue

                # Lot affiché

                batch_number = "-"
                expiry_date = None

                if active_batches:

                    first_batch = (
                        active_batches[0]
                    )

                    batch_number = (
                        first_batch.batch_number
                        or "-"
                    )

                    expiry_date = (
                        first_batch.expiry_date
                    )

                else:

                    batch_number = (
                        product.batch_number
                        or "-"
                    )

                    expiry_date = (
                        product.expiry_date
                    )

                # État

                status = (
                    self.get_product_status(
                        stock_units,
                        product,
                        has_expired,
                        has_expiring
                    )
                )

                rows.append({
                    "product": product,
                    "stock_units": stock_units,
                    "stock_display": stock_display,
                    "purchase_value": purchase_value,
                    "sale_value": sale_value,
                    "batch_number": batch_number,
                    "expiry_date": expiry_date,
                    "status": status,
                })

            # =================================================
            # TABLEAU
            # =================================================

            self.stock_table.setRowCount(
                len(rows)
            )

            for row, data in enumerate(rows):

                product = data["product"]

                self.set_table_item(
                    row,
                    0,
                    product.name or "-"
                )

                self.set_table_item(
                    row,
                    1,
                    product.category or "-"
                )

                self.set_table_item(
                    row,
                    2,
                    product.packaging
                    or product.base_unit
                    or "Pièce"
                )

                self.set_table_item(
                    row,
                    3,
                    data["stock_display"]
                )

                self.set_table_item(
                    row,
                    4,
                    format_number(
                        data["stock_units"]
                    ),
                    Qt.AlignRight
                    | Qt.AlignVCenter
                )

                self.set_table_item(
                    row,
                    5,
                    format_money(
                        data["purchase_value"]
                    ),
                    Qt.AlignRight
                    | Qt.AlignVCenter
                )

                self.set_table_item(
                    row,
                    6,
                    format_money(
                        data["sale_value"]
                    ),
                    Qt.AlignRight
                    | Qt.AlignVCenter
                )

                self.set_table_item(
                    row,
                    7,
                    data["batch_number"]
                )

                self.set_table_item(
                    row,
                    8,
                    format_date(
                        data["expiry_date"]
                    )
                )

                status_item = QTableWidgetItem(
                    data["status"]
                )

                status_item.setTextAlignment(
                    Qt.AlignCenter
                    | Qt.AlignVCenter
                )

                self.stock_table.setItem(
                    row,
                    9,
                    status_item
                )

            # =================================================
            # STATISTIQUES
            # =================================================

            self.products_card.value_label.setText(
                format_number(
                    total_products
                )
            )

            self.stock_units_card.value_label.setText(
                format_number(
                    total_stock_units
                )
            )

            self.purchase_value_card.value_label.setText(
                f"{format_money(total_purchase_value)} FC"
            )

            self.sale_value_card.value_label.setText(
                f"{format_money(total_sale_value)} FC"
            )

            self.low_stock_card.value_label.setText(
                format_number(
                    low_stock_count
                )
            )

            self.expiring_card.value_label.setText(
                format_number(
                    expiring_count
                )
            )

            self.expired_card.value_label.setText(
                format_number(
                    expired_count
                )
            )

            self.available_card.value_label.setText(
                format_number(
                    available_count
                )
            )

            # =================================================
            # COMPTEUR
            # =================================================

            if len(rows) <= 1:

                self.result_count.setText(
                    f"{len(rows)} produit"
                )

            else:

                self.result_count.setText(
                    f"{len(rows)} produits"
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur de chargement",
                (
                    "Impossible de charger le stock.\n\n"
                    f"{error}"
                )
            )

        finally:

            session.close()

    # ========================================================
    # STOCK GLOBAL
    # ========================================================

    def get_product_stock(
        self,
        session,
        product
    ):

        try:

            stock = (
                calculate_product_global_stock(
                    session,
                    product
                )
            )

            return float(
                stock or 0
            )

        except TypeError:

            try:

                stock = (
                    calculate_product_global_stock(
                        product
                    )
                )

                return float(
                    stock or 0
                )

            except Exception:
                pass

        except Exception:
            pass

        try:

            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id
                    == product.id
                )
                .all()
            )

            batch_stock = sum(
                float(
                    batch.stock_units or 0
                )
                for batch in batches
            )

            if batch_stock > 0:
                return batch_stock

        except Exception:
            pass

        return float(
            product.stock_units or 0
        )

    # ========================================================
    # STOCK AFFICHÉ
    # ========================================================

    def get_stock_display_safe(
        self,
        product,
        stock_units
    ):

        try:

            result = get_stock_display(
                product
            )

            if result is not None:
                return str(result)

        except Exception:
            pass

        base_unit = (
            product.base_unit
            or "Pièce"
        )

        units_per_plaquette = float(
            product.units_per_plaquette or 1
        )

        plaquettes_per_box = float(
            product.plaquettes_per_box or 1
        )

        boxes_per_carton = float(
            product.boxes_per_carton or 1
        )

        packaging = (
            product.packaging
            or base_unit
        )

        packaging_lower = (
            str(packaging)
            .lower()
            .strip()
        )

        if packaging_lower == "carton":

            units_per_carton = (
                units_per_plaquette
                * plaquettes_per_box
                * boxes_per_carton
            )

            if units_per_carton > 0:

                cartons = (
                    stock_units
                    / units_per_carton
                )

                return (
                    f"{format_number(cartons)} Carton(s)"
                )

        if packaging_lower in (
            "boîte",
            "boite"
        ):

            units_per_box = (
                units_per_plaquette
                * plaquettes_per_box
            )

            if units_per_box > 0:

                boxes = (
                    stock_units
                    / units_per_box
                )

                return (
                    f"{format_number(boxes)} Boîte(s)"
                )

        if packaging_lower == "plaquette":

            if units_per_plaquette > 0:

                plaquettes = (
                    stock_units
                    / units_per_plaquette
                )

                return (
                    f"{format_number(plaquettes)} Plaquette(s)"
                )

        return (
            f"{format_number(stock_units)} "
            f"{base_unit}"
        )

    # ========================================================
    # VALEUR DE VENTE
    # ========================================================

    def calculate_sale_value(
        self,
        product,
        stock_units
    ):

        try:

            price = float(
                product.price_per_comprime or 0
            )

            if price > 0:

                return (
                    stock_units
                    * price
                )

        except Exception:
            pass

        try:

            price = float(
                product.price or 0
            )

            return (
                stock_units
                * price
            )

        except Exception:

            return 0

    # ========================================================
    # STOCK FAIBLE
    # ========================================================

    def is_product_low_stock(
        self,
        product,
        stock_units
    ):

        minimum = float(
            product.min_quantity or 0
        )

        if minimum <= 0:
            return False

        return stock_units <= minimum

    # ========================================================
    # ÉTAT
    # ========================================================

    def get_product_status(
        self,
        stock_units,
        product,
        has_expired,
        has_expiring
    ):

        if stock_units <= 0:
            return "Rupture"

        if has_expired:
            return "Expiré"

        if has_expiring:
            return "Expiration proche"

        if self.is_product_low_stock(
            product,
            stock_units
        ):
            return "Stock faible"

        return "Disponible"

    # ========================================================
    # FILTRE ÉTAT
    # ========================================================

    def match_status_filter(
        self,
        selected_status,
        stock_units,
        is_low,
        has_expired,
        has_expiring
    ):

        if selected_status == "Tous":
            return True

        if selected_status == "Stock disponible":

            return (
                stock_units > 0
                and not is_low
                and not has_expired
                and not has_expiring
            )

        if selected_status == "Stock faible":

            return (
                stock_units > 0
                and is_low
            )

        if selected_status == "Rupture":

            return stock_units <= 0

        if selected_status == "Expiration proche":

            return (
                has_expiring
                and not has_expired
            )

        if selected_status == "Expiré":

            return has_expired

        return True

    # ========================================================
    # EXPIRATION
    # ========================================================

    def get_expiry_status(
        self,
        expiry_date
    ):

        if not expiry_date:
            return "none"

        try:

            if isinstance(
                expiry_date,
                datetime
            ):

                expiry = (
                    expiry_date.date()
                )

            elif isinstance(
                expiry_date,
                date
            ):

                expiry = expiry_date

            else:

                expiry = datetime.strptime(
                    str(expiry_date),
                    "%Y-%m-%d"
                ).date()

            today = date.today()

            days = (
                expiry - today
            ).days

            if days < 0:
                return "expired"

            if days <= 30:
                return "soon"

            return "normal"

        except Exception:

            return "none"

    # ========================================================
    # TABLE ITEM
    # ========================================================

    def set_table_item(
        self,
        row,
        column,
        text,
        alignment=None
    ):

        item = QTableWidgetItem(
            str(text)
        )

        if alignment is not None:

            item.setTextAlignment(
                alignment
            )

        self.stock_table.setItem(
            row,
            column,
            item
        )

    # ========================================================
    # DOUBLE CLIC
    # ========================================================

    def on_row_double_clicked(
        self,
        row,
        column
    ):

        product_item = (
            self.stock_table.item(
                row,
                0
            )
        )

        if not product_item:
            return

        product_name = (
            product_item.text()
        )

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.name
                    == product_name
                )
                .first()
            )

            if product:

                self.show_product_details(
                    product.id
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                str(error)
            )

        finally:

            session.close()

    # ========================================================
    # DÉTAILS
    # ========================================================

    def show_product_details(
        self,
        product_id
    ):

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.id
                    == product_id
                )
                .first()
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Ce produit n'existe plus."
                )

                return

            stock_units = (
                self.get_product_stock(
                    session,
                    product
                )
            )

            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id
                    == product.id
                )
                .order_by(
                    ProductBatch.expiry_date.asc()
                )
                .all()
            )

            dialog = ProductStockDetailsDialog(
                product,
                stock_units,
                batches,
                self
            )

            dialog.exec()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible d'afficher les détails.\n\n"
                    f"{error}"
                )
            )

        finally:

            session.close()

    # ========================================================
    # EFFACER FILTRES
    # ========================================================

    def clear_filters(self):

        self.search_input.clear()

        self.status_filter.setCurrentIndex(
            0
        )

        self.category_filter.setCurrentIndex(
            0
        )

        self.load_stock()


# ============================================================
# DIALOGUE DÉTAILS
# ============================================================

class ProductStockDetailsDialog(QDialog):

    def __init__(
        self,
        product,
        stock_units,
        batches,
        parent=None
    ):

        super().__init__(parent)

        self.product = product
        self.stock_units = stock_units
        self.batches = batches

        self.setWindowTitle(
            f"Stock - {product.name}"
        )

        self.resize(
            950,
            650
        )

        self.setup_ui()
        self.apply_styles()

    # ========================================================
    # INTERFACE
    # ========================================================

    def setup_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        layout.setSpacing(
            18
        )

        title = QLabel(
            self.product.name
            or "Produit"
        )

        title.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            title
        )

        # ====================================================
        # INFORMATIONS
        # ====================================================

        info_frame = QFrame()

        info_frame.setObjectName(
            "infoFrame"
        )

        info_layout = QGridLayout(
            info_frame
        )

        info_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        info_layout.setHorizontalSpacing(
            25
        )

        info_layout.setVerticalSpacing(
            14
        )

        informations = [
            (
                "Catégorie",
                self.product.category or "-"
            ),
            (
                "Unité de base",
                self.product.base_unit or "-"
            ),
            (
                "Conditionnement",
                self.product.packaging or "-"
            ),
            (
                "Stock actuel",
                format_number(
                    self.stock_units
                )
            ),
            (
                "Stock minimum",
                format_number(
                    self.product.min_quantity
                )
            ),
            (
                "Prix d'achat",
                f"{format_money(self.product.purchase_price)} FC"
            ),
            (
                "Prix unité",
                f"{format_money(self.product.price_per_comprime)} FC"
            ),
            (
                "Prix plaquette",
                f"{format_money(self.product.price_per_plaquette)} FC"
            ),
            (
                "Prix boîte",
                f"{format_money(self.product.price_per_box)} FC"
            ),
            (
                "Prix carton",
                f"{format_money(self.product.price_per_carton)} FC"
            ),
        ]

        for index, (label, value) in enumerate(
            informations
        ):

            row = index // 2
            column = (index % 2) * 2

            self.add_info(
                info_layout,
                row,
                column,
                label,
                value
            )

        layout.addWidget(
            info_frame
        )

        # ====================================================
        # CONVERSIONS
        # ====================================================

        conversion_frame = QFrame()

        conversion_frame.setObjectName(
            "conversionFrame"
        )

        conversion_layout = QVBoxLayout(
            conversion_frame
        )

        conversion_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        conversion_title = QLabel(
            "Structure du conditionnement"
        )

        conversion_title.setObjectName(
            "conversionTitle"
        )

        conversion_text = (
            f"1 plaquette = "
            f"{format_number(self.product.units_per_plaquette or 1)} "
            f"{self.product.base_unit or 'unité'}"
            f"     •     "
            f"1 boîte = "
            f"{format_number(self.product.plaquettes_per_box or 1)} "
            f"plaquette(s)"
            f"     •     "
            f"1 carton = "
            f"{format_number(self.product.boxes_per_carton or 1)} "
            f"boîte(s)"
        )

        conversion_label = QLabel(
            conversion_text
        )

        conversion_label.setWordWrap(
            True
        )

        conversion_layout.addWidget(
            conversion_title
        )

        conversion_layout.addWidget(
            conversion_label
        )

        layout.addWidget(
            conversion_frame
        )

        # ====================================================
        # LOTS
        # ====================================================

        batches_title = QLabel(
            "Lots enregistrés"
        )

        batches_title.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            batches_title
        )

        table = QTableWidget()

        table.setColumnCount(
            6
        )

        table.setHorizontalHeaderLabels([
            "Lot",
            "Expiration",
            "Stock",
            "Prix achat",
            "Fournisseur",
            "État",
        ])

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.verticalHeader().setVisible(
            False
        )

        table.setAlternatingRowColors(
            True
        )

        table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        table.horizontalHeader().setSectionResizeMode(
            4,
            QHeaderView.Stretch
        )

        table.horizontalHeader().setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )

        table.setRowCount(
            len(self.batches)
        )

        for row, batch in enumerate(
            self.batches
        ):

            self.set_table_item(
                table,
                row,
                0,
                batch.batch_number or "-"
            )

            self.set_table_item(
                table,
                row,
                1,
                format_date(
                    batch.expiry_date
                )
            )

            self.set_table_item(
                table,
                row,
                2,
                format_number(
                    batch.stock_units
                ),
                Qt.AlignRight
            )

            self.set_table_item(
                table,
                row,
                3,
                f"{format_money(batch.purchase_price)} FC",
                Qt.AlignRight
            )

            self.set_table_item(
                table,
                row,
                4,
                batch.supplier or "-"
            )

            self.set_table_item(
                table,
                row,
                5,
                self.get_batch_status(batch),
                Qt.AlignCenter
            )

        layout.addWidget(
            table,
            1
        )

        # ====================================================
        # BOUTON
        # ====================================================

        buttons_layout = QHBoxLayout()

        buttons_layout.addStretch()

        close_button = QPushButton(
            "Fermer"
        )

        close_button.setMinimumSize(
            120,
            42
        )

        close_button.clicked.connect(
            self.accept
        )

        buttons_layout.addWidget(
            close_button
        )

        layout.addLayout(
            buttons_layout
        )

    # ========================================================
    # INFORMATION
    # ========================================================

    def add_info(
        self,
        layout,
        row,
        column,
        label,
        value
    ):

        label_widget = QLabel(
            label
        )

        label_widget.setObjectName(
            "infoLabel"
        )

        value_widget = QLabel(
            str(value)
        )

        value_widget.setObjectName(
            "infoValue"
        )

        layout.addWidget(
            label_widget,
            row,
            column
        )

        layout.addWidget(
            value_widget,
            row,
            column + 1
        )

    # ========================================================
    # TABLE ITEM
    # ========================================================

    def set_table_item(
        self,
        table,
        row,
        column,
        text,
        alignment=None
    ):

        item = QTableWidgetItem(
            str(text)
        )

        if alignment is not None:

            item.setTextAlignment(
                alignment
            )

        table.setItem(
            row,
            column,
            item
        )

    # ========================================================
    # ÉTAT LOT
    # ========================================================

    def get_batch_status(
        self,
        batch
    ):

        stock = float(
            batch.stock_units or 0
        )

        if stock <= 0:
            return "Épuisé"

        try:

            if is_batch_expired(
                batch
            ):
                return "Expiré"

            if is_batch_expiring_soon(
                batch
            ):
                return "Expire bientôt"

        except Exception:

            expiry_status = (
                self.get_expiry_status(
                    batch.expiry_date
                )
            )

            if expiry_status == "expired":
                return "Expiré"

            if expiry_status == "soon":
                return "Expire bientôt"

        return "Disponible"

    # ========================================================
    # EXPIRATION
    # ========================================================

    def get_expiry_status(
        self,
        expiry_date
    ):

        if not expiry_date:
            return "none"

        try:

            if isinstance(
                expiry_date,
                datetime
            ):

                expiry = (
                    expiry_date.date()
                )

            elif isinstance(
                expiry_date,
                date
            ):

                expiry = expiry_date

            else:

                expiry = datetime.strptime(
                    str(expiry_date),
                    "%Y-%m-%d"
                ).date()

            days = (
                expiry - date.today()
            ).days

            if days < 0:
                return "expired"

            if days <= 30:
                return "soon"

            return "normal"

        except Exception:

            return "none"

    # ========================================================
    # STYLES DIALOGUE
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""

            QDialog {
                background-color: #f1f5f9;
                color: #0f172a;
            }

            QLabel {
                color: #475569;
            }

            QLabel#dialogTitle {
                color: #0f172a;
                font-size: 25px;
                font-weight: 800;
            }

            QLabel#sectionTitle {
                color: #0f172a;
                font-size: 17px;
                font-weight: 750;
            }

            QFrame#infoFrame,
            QFrame#conversionFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel#infoLabel {
                color: #64748b;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#infoValue {
                color: #0f172a;
                font-size: 13px;
                font-weight: 750;
            }

            QLabel#conversionTitle {
                color: #0f766e;
                font-size: 13px;
                font-weight: 750;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                gridline-color: #e2e8f0;
                color: #0f172a;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QHeaderView::section {
                background-color: #0f172a;
                color: white;
                padding: 9px;
                border: none;
                font-weight: 700;
            }

            QPushButton {
                background-color: #0f766e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #115e59;
            }

        """)