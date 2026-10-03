from datetime import date, timedelta
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QLineEdit,
    QScrollArea,
)

from database.database import (
    SessionLocal,
    is_low_stock,
)

from database.models import (
    Product,
    ProductBatch,
)


class StockPage(QWidget):
    """
    Page professionnelle de gestion des stocks.

    Nouvelle logique :

    ------------------------------------------------------------
    CARTON
    ------------------------------------------------------------
    1. Nombre de boîtes dans un carton
    2. Nombre de plaquettes dans une boîte
    3. Nombre de cartons
    4. Prix de vente par plaquette
    5. Date d'expiration

    Exemple :

        5 boîtes / carton
        10 plaquettes / boîte
        2 cartons

    Donc :

        1 carton = 50 plaquettes
        2 cartons = 100 plaquettes

    Prix :

        500 CDF / plaquette
        5 000 CDF / boîte
        25 000 CDF / carton

    ------------------------------------------------------------
    BOÎTE
    ------------------------------------------------------------

        quantité = nombre de boîtes
        prix = prix de vente par boîte

    ------------------------------------------------------------
    PLAQUETTE
    ------------------------------------------------------------

        quantité = nombre de plaquettes
        prix = prix de vente par plaquette

    ------------------------------------------------------------
    AUTRE PRODUIT
    ------------------------------------------------------------

        quantité = quantité du produit
        prix = prix de vente unitaire

    ------------------------------------------------------------

    Les stocks par lots sont conservés.

    Le stock d'un médicament peut donc être réparti
    sur plusieurs lots avec des dates d'expiration différentes.

    Le système affiche les lots par ordre d'expiration
    afin de respecter le principe FEFO.
    """

    EXPIRY_WARNING_DAYS = 90

    def __init__(self):
        super().__init__()

        self.setObjectName("stockPage")

        # ============================================================
        # LAYOUT EXTERNE
        # ============================================================

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer_layout.setSpacing(0)

        # ============================================================
        # SCROLL AREA
        # ============================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setObjectName(
            "stockScrollArea"
        )

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        # ============================================================
        # CONTENEUR
        # ============================================================

        self.page_container = QWidget()

        self.page_container.setObjectName(
            "stockPageContainer"
        )

        self.page_container.setMinimumWidth(1100)

        # ============================================================
        # LAYOUT
        # ============================================================

        layout = QVBoxLayout(
            self.page_container
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            35,
        )

        layout.setSpacing(18)

        self.scroll_area.setWidget(
            self.page_container
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # ============================================================
        # TITRE
        # ============================================================

        title = QLabel(
            "📦 Gestion des Stocks"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Suivi des produits, fournisseurs, lots, "
            "conditionnements, prix et dates d'expiration"
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ============================================================
        # CARTES STATISTIQUES
        # ============================================================

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(15)

        self.card_total = self._create_stat_card(
            "Produits",
            "0",
            "#2563EB",
            "📦",
        )

        self.card_batches = self._create_stat_card(
            "Lots",
            "0",
            "#0891B2",
            "🧾",
        )

        self.card_expired = self._create_stat_card(
            "Lots expirés",
            "0",
            "#DC2626",
            "🔴",
        )

        self.card_warning = self._create_stat_card(
            "Expiration proche",
            "0",
            "#D97706",
            "⚠️",
        )

        self.card_low_stock = self._create_stat_card(
            "Stock faible",
            "0",
            "#7C3AED",
            "📉",
        )

        stats_layout.addWidget(
            self.card_total
        )

        stats_layout.addWidget(
            self.card_batches
        )

        stats_layout.addWidget(
            self.card_expired
        )

        stats_layout.addWidget(
            self.card_warning
        )

        stats_layout.addWidget(
            self.card_low_stock
        )

        layout.addLayout(
            stats_layout
        )

        # ============================================================
        # RECHERCHE
        # ============================================================

        search_frame = QFrame()

        search_frame.setObjectName(
            "searchFrame"
        )

        search_layout = QVBoxLayout(
            search_frame
        )

        search_layout.setContentsMargins(
            15,
            12,
            15,
            12,
        )

        search_layout.setSpacing(7)

        search_label = QLabel(
            "Rechercher un produit, fournisseur ou lot"
        )

        search_label.setObjectName(
            "searchLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "🔍 Nom du produit, fournisseur ou numéro de lot..."
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.textChanged.connect(
            self.refresh
        )

        search_layout.addWidget(
            search_label
        )

        search_layout.addWidget(
            self.search_input
        )

        layout.addWidget(
            search_frame
        )

        # ============================================================
        # TABLEAU
        # ============================================================

        self.table = QTableWidget()

        self.table.setObjectName(
            "stockTable"
        )

        self.table.setColumnCount(10)

        self.table.setHorizontalHeaderLabels(
            [
                "Produit",
                "Fournisseur",
                "Condition",
                "Configuration",
                "Stock réel",
                "Prix / plaquette",
                "Prix / boîte",
                "Prix / carton",
                "Expiration",
                "État",
            ]
        )

        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(False)

        self.table.setMinimumHeight(450)

        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # ============================================================
        # HEADER
        # ============================================================

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for index in range(1, 10):
            header.setSectionResizeMode(
                index,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        layout.addWidget(
            self.table
        )

        # ============================================================
        # FOOTER
        # ============================================================

        footer = QLabel(
            "💡 Les stocks sont conservés par lot. "
            "Pour les produits conditionnés en carton, "
            "la configuration est affichée avec le nombre "
            "de boîtes par carton et de plaquettes par boîte. "
            "Les lots arrivant à expiration sont signalés "
            "et les lots les plus proches de l'expiration "
            "doivent être utilisés en priorité."
        )

        footer.setObjectName(
            "stockFooter"
        )

        footer.setWordWrap(True)

        layout.addWidget(
            footer
        )

        layout.addSpacing(20)

        # ============================================================
        # STYLE
        # ============================================================

        self.apply_styles()

        # ============================================================
        # CHARGEMENT
        # ============================================================

        self.refresh()

    # =================================================================
    # CARTE STATISTIQUE
    # =================================================================

    def _create_stat_card(
        self,
        title,
        value,
        color,
        icon,
    ):
        card = QFrame()

        card.setObjectName(
            "statCard"
        )

        card.setMinimumHeight(115)

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        card_layout.setSpacing(5)

        top_layout = QHBoxLayout()

        title_label = QLabel(title)

        title_label.setObjectName(
            "statTitle"
        )

        icon_label = QLabel(icon)

        icon_label.setObjectName(
            "statIcon"
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 22px;
            }}
            """
        )

        top_layout.addWidget(
            title_label
        )

        top_layout.addStretch()

        top_layout.addWidget(
            icon_label
        )

        value_label = QLabel(value)

        value_label.setObjectName(
            "statValue"
        )

        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 30px;
                font-weight: bold;
            }}
            """
        )

        line = QFrame()

        line.setFixedHeight(4)

        line.setStyleSheet(
            f"""
            QFrame {{
                background-color: {color};
                border-radius: 2px;
            }}
            """
        )

        card_layout.addLayout(
            top_layout
        )

        card_layout.addWidget(
            value_label
        )

        card_layout.addWidget(
            line
        )

        return card

    # =================================================================
    # STYLE
    # =================================================================

    def apply_styles(self):

        self.setStyleSheet(
            """
            #stockPage {
                background-color: #F8FAFC;
            }

            #stockScrollArea {
                background-color: #F8FAFC;
                border: none;
            }

            #stockPageContainer {
                background-color: #F8FAFC;
            }

            QScrollBar:vertical {
                background-color: #EEF2F6;
                width: 10px;
                margin: 3px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #B8C1CC;
                min-height: 40px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #98A2B3;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }

            #pageTitle {
                color: #0F172A;
                font-size: 25px;
                font-weight: bold;
            }

            #pageSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            #statCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }

            #statCard:hover {
                border: 1px solid #CBD5E1;
            }

            #statTitle {
                color: #64748B;
                font-size: 12px;
                font-weight: 600;
            }

            #searchFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            #searchLabel {
                color: #334155;
                font-weight: bold;
                font-size: 13px;
            }

            QLineEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 10px 12px;
                color: #0F172A;
                font-size: 13px;
            }

            QLineEdit:focus {
                border: 2px solid #2563EB;
                background-color: white;
            }

            #stockTable {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #E2E8F0;
                color: #1E293B;
                font-size: 12px;
                outline: none;
            }

            #stockTable::item {
                padding: 8px;
            }

            #stockTable::item:selected {
                background-color: #DBEAFE;
                color: #1E3A8A;
            }

            QHeaderView::section {
                background-color: #0F172A;
                color: white;
                padding: 11px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }

            #stockFooter {
                background-color: white;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px;
                font-size: 11px;
            }
            """
        )

    # =================================================================
    # OUTILS DE LECTURE
    # =================================================================

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value or default)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value or default)
        except (
            TypeError,
            ValueError,
        ):
            return default

    def _get_packaging(self, product):
        """
        Récupère la condition initiale du produit.
        """

        packaging = getattr(
            product,
            "packaging",
            None,
        )

        if not packaging:
            return "Autre produit"

        return str(packaging)

    def _get_boxes_per_carton(self, product):
        """
        Nombre de boîtes dans un carton.
        """

        value = self._safe_int(
            getattr(
                product,
                "boxes_per_carton",
                0,
            ),
            0,
        )

        return max(value, 1)

    def _get_plaquettes_per_box(self, product):
        """
        Nombre de plaquettes dans une boîte.

        Dans la nouvelle logique, `units_per_box`
        représente le nombre de plaquettes par boîte.
        """

        value = self._safe_int(
            getattr(
                product,
                "units_per_box",
                0,
            ),
            0,
        )

        if value <= 0:

            value = self._safe_int(
                getattr(
                    product,
                    "units_per_plaquette",
                    0,
                ),
                0,
            )

        return max(value, 1)

    # =================================================================
    # CONFIGURATION DU CONDITIONNEMENT
    # =================================================================

    def _format_configuration(self, product):
        """
        Affiche la configuration du produit.
        """

        packaging = self._get_packaging(
            product
        )

        if packaging.lower() == "carton":

            boxes = self._get_boxes_per_carton(
                product
            )

            plaquettes = self._get_plaquettes_per_box(
                product
            )

            return (
                f"{boxes} boîte(s) / carton\n"
                f"{plaquettes} plaquette(s) / boîte"
            )

        if packaging.lower() == "boîte":

            plaquettes = self._get_plaquettes_per_box(
                product
            )

            if plaquettes > 1:

                return (
                    f"{plaquettes} plaquette(s) / boîte"
                )

            return "Vente par boîte"

        if packaging.lower() == "plaquette":

            return "Vente par plaquette"

        return "Produit unitaire"

    # =================================================================
    # FORMATAGE DU STOCK
    # =================================================================

    def _format_stock(
        self,
        product,
        stock_units,
    ):
        """
        Affiche le stock selon la condition initiale.

        IMPORTANT :

        - Carton :
          stock_units = plaquettes

        - Boîte :
          stock_units = boîtes

        - Plaquette :
          stock_units = plaquettes

        - Autre produit :
          stock_units = unités.
        """

        packaging = self._get_packaging(
            product
        ).lower()

        stock = max(
            0,
            self._safe_int(
                stock_units,
                0,
            ),
        )

        if packaging == "carton":

            boxes_per_carton = (
                self._get_boxes_per_carton(
                    product
                )
            )

            plaquettes_per_box = (
                self._get_plaquettes_per_box(
                    product
                )
            )

            plaquettes_per_carton = (
                boxes_per_carton
                * plaquettes_per_box
            )

            cartons = (
                stock
                // plaquettes_per_carton
            )

            remainder = (
                stock
                % plaquettes_per_carton
            )

            boxes = (
                remainder
                // plaquettes_per_box
            )

            plaquettes = (
                remainder
                % plaquettes_per_box
            )

            parts = []

            if cartons:
                parts.append(
                    f"{cartons} carton"
                    + (
                        "s"
                        if cartons > 1
                        else ""
                    )
                )

            if boxes:
                parts.append(
                    f"{boxes} boîte"
                    + (
                        "s"
                        if boxes > 1
                        else ""
                    )
                )

            if plaquettes:
                parts.append(
                    f"{plaquettes} plaquette"
                    + (
                        "s"
                        if plaquettes > 1
                        else ""
                    )
                )

            if not parts:
                return "0 plaquette"

            return " + ".join(parts)

        if packaging == "boîte":

            return (
                f"{stock} boîte"
                + (
                    "s"
                    if stock > 1
                    else ""
                )
            )

        if packaging == "plaquette":

            return (
                f"{stock} plaquette"
                + (
                    "s"
                    if stock > 1
                    else ""
                )
            )

        return (
            f"{stock} unité"
            + (
                "s"
                if stock > 1
                else ""
            )
        )

    # =================================================================
    # PRIX
    # =================================================================

    def _get_prices(self, product):
        """
        Récupère les trois prix affichables :

        prix par plaquette
        prix par boîte
        prix par carton
        """

        packaging = self._get_packaging(
            product
        ).lower()

        price_per_plaquette = self._safe_float(
            getattr(
                product,
                "price_per_plaquette",
                0,
            )
        )

        price_per_box = self._safe_float(
            getattr(
                product,
                "price_per_box",
                0,
            )
        )

        price_per_carton = self._safe_float(
            getattr(
                product,
                "price_per_carton",
                0,
            )
        )

        # ------------------------------------------------------------
        # Carton
        # ------------------------------------------------------------

        if packaging == "carton":

            boxes_per_carton = (
                self._get_boxes_per_carton(
                    product
                )
            )

            plaquettes_per_box = (
                self._get_plaquettes_per_box(
                    product
                )
            )

            if price_per_plaquette <= 0:

                price_per_plaquette = (
                    self._safe_float(
                        getattr(
                            product,
                            "price",
                            0,
                        )
                    )
                )

            if price_per_box <= 0:

                price_per_box = (
                    price_per_plaquette
                    * plaquettes_per_box
                )

            if price_per_carton <= 0:

                price_per_carton = (
                    price_per_box
                    * boxes_per_carton
                )

        # ------------------------------------------------------------
        # Boîte
        # ------------------------------------------------------------

        elif packaging == "boîte":

            if price_per_box <= 0:

                price_per_box = (
                    self._safe_float(
                        getattr(
                            product,
                            "price",
                            0,
                        )
                    )
                )

        # ------------------------------------------------------------
        # Plaquette
        # ------------------------------------------------------------

        elif packaging == "plaquette":

            if price_per_plaquette <= 0:

                price_per_plaquette = (
                    self._safe_float(
                        getattr(
                            product,
                            "price",
                            0,
                        )
                    )
                )

        # ------------------------------------------------------------
        # Autre produit
        # ------------------------------------------------------------

        else:

            if price_per_plaquette <= 0:

                price_per_plaquette = (
                    self._safe_float(
                        getattr(
                            product,
                            "price",
                            0,
                        )
                    )
                )

        return (
            price_per_plaquette,
            price_per_box,
            price_per_carton,
        )

    @staticmethod
    def _format_price(value):
        return f"{value:,.2f} CDF"

    # =================================================================
    # LOTS
    # =================================================================

    def _get_batches(
        self,
        session,
        product,
    ):
        """
        Récupère les lots dans l'ordre FEFO.

        Le lot avec la date d'expiration
        la plus proche arrive en premier.
        """

        try:

            return (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id
                    == product.id
                )
                .order_by(
                    ProductBatch.expiry_date.asc(),
                    ProductBatch.id.asc(),
                )
                .all()
            )

        except Exception as error:

            print(
                "Erreur récupération lots :",
                error,
            )

            return []

    # =================================================================
    # STOCK TOTAL
    # =================================================================

    def _get_product_stock(
        self,
        product,
        batches,
    ):
        """
        Calcule le stock total du produit.

        Priorité aux lots.

        Si aucun lot n'existe,
        utilisation de l'ancien stock du produit.
        """

        if batches:

            total = 0

            for batch in batches:

                total += self._safe_int(
                    getattr(
                        batch,
                        "stock_units",
                        0,
                    )
                )

            return total

        return self._safe_int(
            getattr(
                product,
                "stock_units",
                0,
            )
        )

    # =================================================================
    # EXPIRATION
    # =================================================================

    def _get_expiry_status(
        self,
        expiry_date,
        today,
        alert_limit,
    ):

        if expiry_date is None:

            return (
                "⚠️ DATE NON DÉFINIE",
                QColor("#FEF3C7"),
                "missing",
            )

        if expiry_date < today:

            return (
                "🔴 EXPIRÉ",
                QColor("#FEE2E2"),
                "expired",
            )

        if expiry_date <= alert_limit:

            return (
                "⚠️ EXPIRE BIENTÔT",
                QColor("#FEF3C7"),
                "warning",
            )

        return (
            "🟢 OK",
            QColor("#DCFCE7"),
            "ok",
        )

    # =================================================================
    # RECHERCHE
    # =================================================================

    def _matches_search(
        self,
        product,
        batch,
        search_text,
    ):

        if not search_text:
            return True

        product_name = (
            getattr(
                product,
                "name",
                None,
            )
            or ""
        )

        supplier = (
            getattr(
                batch,
                "supplier",
                None,
            )
            if batch is not None
            else None
        )

        if not supplier:

            supplier = getattr(
                product,
                "supplier",
                None,
            )

        batch_number = ""

        if batch is not None:

            batch_number = (
                getattr(
                    batch,
                    "batch_number",
                    None,
                )
                or ""
            )

        packaging = (
            self._get_packaging(
                product
            )
        )

        combined = " ".join(
            [
                str(product_name),
                str(supplier or ""),
                str(batch_number),
                str(packaging),
            ]
        ).lower()

        return search_text in combined

    # =================================================================
    # ACTUALISATION
    # =================================================================

    def refresh(self):

        session = SessionLocal()

        try:

            search_text = (
                self.search_input
                .text()
                .strip()
                .lower()
            )

            products = (
                session.query(Product)
                .order_by(
                    Product.name.asc()
                )
                .all()
            )

            today = date.today()

            alert_limit = (
                today
                + timedelta(
                    days=self.EXPIRY_WARNING_DAYS
                )
            )

            c_total_products = 0
            c_total_batches = 0
            c_expired = 0
            c_warning = 0
            c_low_stock = 0

            self.table.setRowCount(0)

            # ========================================================
            # PRODUITS
            # ========================================================

            for product in products:

                batches = self._get_batches(
                    session,
                    product,
                )

                # ====================================================
                # ANCIEN SYSTÈME SANS LOT
                # ====================================================

                if not batches:

                    if not self._matches_search(
                        product,
                        None,
                        search_text,
                    ):
                        continue

                    c_total_products += 1

                    stock_units = (
                        self._safe_int(
                            getattr(
                                product,
                                "stock_units",
                                0,
                            )
                        )
                    )

                    expiry_date = getattr(
                        product,
                        "expiry_date",
                        None,
                    )

                    (
                        status_text,
                        status_color,
                        category,
                    ) = self._get_expiry_status(
                        expiry_date,
                        today,
                        alert_limit,
                    )

                    if category == "expired":
                        c_expired += 1

                    elif category == "warning":
                        c_warning += 1

                    minimum_stock = (
                        self._safe_int(
                            getattr(
                                product,
                                "min_quantity",
                                0,
                            )
                        )
                    )

                    low_stock = (
                        stock_units
                        <= minimum_stock
                    )

                    if low_stock:
                        c_low_stock += 1

                    self._add_stock_row(
                        product=product,
                        batch=None,
                        stock_units=stock_units,
                        expiry_date=expiry_date,
                        status_text=status_text,
                        status_color=status_color,
                        low_stock=low_stock,
                        minimum_stock=minimum_stock,
                    )

                    continue

                # ====================================================
                # NOUVEAU SYSTÈME PAR LOT
                # ====================================================

                visible_batches = []

                for batch in batches:

                    if self._matches_search(
                        product,
                        batch,
                        search_text,
                    ):
                        visible_batches.append(
                            batch
                        )

                if not visible_batches:
                    continue

                c_total_products += 1

                c_total_batches += len(
                    visible_batches
                )

                # ====================================================
                # STOCK TOTAL
                # ====================================================

                total_stock = (
                    self._get_product_stock(
                        product,
                        batches,
                    )
                )

                minimum_stock = (
                    self._safe_int(
                        getattr(
                            product,
                            "min_quantity",
                            0,
                        )
                    )
                )

                low_stock = (
                    total_stock
                    <= minimum_stock
                )

                if low_stock:
                    c_low_stock += 1

                # ====================================================
                # LOTS
                # ====================================================

                for batch in visible_batches:

                    stock_units = (
                        self._safe_int(
                            getattr(
                                batch,
                                "stock_units",
                                0,
                            )
                        )
                    )

                    expiry_date = getattr(
                        batch,
                        "expiry_date",
                        None,
                    )

                    (
                        status_text,
                        status_color,
                        category,
                    ) = self._get_expiry_status(
                        expiry_date,
                        today,
                        alert_limit,
                    )

                    if category == "expired":
                        c_expired += 1

                    elif category == "warning":
                        c_warning += 1

                    self._add_stock_row(
                        product=product,
                        batch=batch,
                        stock_units=stock_units,
                        expiry_date=expiry_date,
                        status_text=status_text,
                        status_color=status_color,
                        low_stock=low_stock,
                        minimum_stock=minimum_stock,
                    )

            # ========================================================
            # HAUTEUR DU TABLEAU
            # ========================================================

            header_height = (
                self.table
                .horizontalHeader()
                .height()
            )

            rows_height = 0

            for row in range(
                self.table.rowCount()
            ):

                rows_height += (
                    self.table.rowHeight(
                        row
                    )
                )

            table_height = (
                header_height
                + rows_height
                + 15
            )

            table_height = max(
                table_height,
                450,
            )

            self.table.setMinimumHeight(
                table_height
            )

            self.table.setMaximumHeight(
                table_height
            )

            # ========================================================
            # CARTES
            # ========================================================

            self._set_card_value(
                self.card_total,
                c_total_products,
            )

            self._set_card_value(
                self.card_batches,
                c_total_batches,
            )

            self._set_card_value(
                self.card_expired,
                c_expired,
            )

            self._set_card_value(
                self.card_warning,
                c_warning,
            )

            self._set_card_value(
                self.card_low_stock,
                c_low_stock,
            )

        except Exception as error:

            print(
                "Erreur lors du chargement des stocks :",
                error,
            )

        finally:

            session.close()

    # =================================================================
    # AJOUT D'UNE LIGNE
    # =================================================================

    def _add_stock_row(
        self,
        product,
        batch,
        stock_units,
        expiry_date,
        status_text,
        status_color,
        low_stock,
        minimum_stock,
    ):

        row = self.table.rowCount()

        self.table.insertRow(row)

        self.table.setRowHeight(
            row,
            62,
        )

        # ============================================================
        # PRODUIT
        # ============================================================

        product_item = QTableWidgetItem(
            getattr(
                product,
                "name",
                None,
            )
            or "-"
        )

        self.table.setItem(
            row,
            0,
            product_item,
        )

        # ============================================================
        # FOURNISSEUR
        # ============================================================

        supplier = None

        if batch is not None:

            supplier = getattr(
                batch,
                "supplier",
                None,
            )

        if not supplier:

            supplier = getattr(
                product,
                "supplier",
                None,
            )

        supplier_item = QTableWidgetItem(
            supplier or "-"
        )

        self.table.setItem(
            row,
            1,
            supplier_item,
        )

        # ============================================================
        # CONDITION
        # ============================================================

        packaging = self._get_packaging(
            product
        )

        packaging_item = QTableWidgetItem(
            packaging
        )

        packaging_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if packaging.lower() == "carton":

            packaging_item.setBackground(
                QColor("#DBEAFE")
            )

        elif packaging.lower() == "boîte":

            packaging_item.setBackground(
                QColor("#E0F2FE")
            )

        elif packaging.lower() == "plaquette":

            packaging_item.setBackground(
                QColor("#DCFCE7")
            )

        else:

            packaging_item.setBackground(
                QColor("#F1F5F9")
            )

        self.table.setItem(
            row,
            2,
            packaging_item,
        )

        # ============================================================
        # CONFIGURATION
        # ============================================================

        configuration_item = QTableWidgetItem(
            self._format_configuration(
                product
            )
        )

        configuration_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            3,
            configuration_item,
        )

        # ============================================================
        # STOCK
        # ============================================================

        stock_item = QTableWidgetItem(
            self._format_stock(
                product,
                stock_units,
            )
        )

        stock_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            4,
            stock_item,
        )

        # ============================================================
        # PRIX
        # ============================================================

        (
            price_per_plaquette,
            price_per_box,
            price_per_carton,
        ) = self._get_prices(
            product
        )

        # ------------------------------------------------------------
        # Prix plaquette
        # ------------------------------------------------------------

        plaquette_item = QTableWidgetItem(
            self._format_price(
                price_per_plaquette
            )
        )

        plaquette_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            5,
            plaquette_item,
        )

        # ------------------------------------------------------------
        # Prix boîte
        # ------------------------------------------------------------

        box_item = QTableWidgetItem(
            self._format_price(
                price_per_box
            )
        )

        box_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            6,
            box_item,
        )

        # ------------------------------------------------------------
        # Prix carton
        # ------------------------------------------------------------

        carton_item = QTableWidgetItem(
            self._format_price(
                price_per_carton
            )
        )

        carton_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            7,
            carton_item,
        )

        # ============================================================
        # EXPIRATION
        # ============================================================

        if expiry_date:

            try:

                expiry_text = (
                    expiry_date.strftime(
                        "%d/%m/%Y"
                    )
                )

            except AttributeError:

                expiry_text = str(
                    expiry_date
                )

        else:

            expiry_text = "N/A"

        expiry_item = QTableWidgetItem(
            expiry_text
        )

        expiry_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            8,
            expiry_item,
        )

        # ============================================================
        # ÉTAT
        # ============================================================

        status_item = QTableWidgetItem(
            status_text
        )

        status_item.setBackground(
            status_color
        )

        status_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            9,
            status_item,
        )

        # ============================================================
        # DONNÉES INTERNES
        # ============================================================

        product_item.setData(
            Qt.ItemDataRole.UserRole,
            product.id,
        )

        if batch is not None:

            product_item.setData(
                Qt.ItemDataRole.UserRole + 1,
                batch.id,
            )

            batch_number = getattr(
                batch,
                "batch_number",
                None,
            )

            if batch_number:

                product_item.setToolTip(
                    f"Lot : {batch_number}"
                )

    # =================================================================
    # VALEUR CARTE
    # =================================================================

    def _set_card_value(
        self,
        card,
        value,
    ):

        label = card.findChild(
            QLabel,
            "statValue",
        )

        if label:

            label.setText(
                str(value)
            )


# ====================================================================
# LANCEMENT DIRECT
# ====================================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Pharmacie - Gestion des stocks"
    )

    window = StockPage()

    window.setWindowTitle(
        "Pharmacie - Gestion des Stocks"
    )

    window.resize(
        1450,
        850,
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()