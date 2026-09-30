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
    get_stock_display,
    get_price_for_packaging,
    is_low_stock,
)

from database.models import (
    Product,
    ProductBatch,
)


class StockPage(QWidget):
    """
    Page de gestion des stocks de la pharmacie.

    Nouveau système :

    - Le stock est géré par LOT.
    - Chaque lot possède sa propre date d'expiration.
    - Un médicament peut avoir plusieurs lots.
    - Le stock total d'un médicament correspond à la somme
      des stocks de tous ses lots.
    - Les lots sont affichés séparément.
    - Les dates d'expiration sont contrôlées lot par lot.
    - Les lots expirés sont signalés.
    - Les lots proches de l'expiration sont signalés.
    - Le stock faible est contrôlé.
    - Le stock est affiché avec :
        Carton
        Boîte
        Plaquette
        Comprimé

    Le système est compatible avec le fonctionnement FEFO :
    First Expired, First Out.
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

        self.scroll_area.setWidgetResizable(
            True
        )

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

        self.page_container.setMinimumWidth(
            850
        )

        # ============================================================
        # LAYOUT PRINCIPAL
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

        layout.setSpacing(
            18
        )

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
            "Suivi des médicaments, des lots, des quantités "
            "et des dates d'expiration"
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        # ============================================================
        # CARTES STATISTIQUES
        # ============================================================

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(
            15
        )

        self.card_total = self._create_stat_card(
            "Médicaments",
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
            "Expirent bientôt",
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

        search_layout.setSpacing(
            7
        )

        search_label = QLabel(
            "Rechercher un médicament ou un lot"
        )

        search_label.setObjectName(
            "searchLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "🔍 Rechercher par nom ou numéro de lot..."
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

        self.table.setColumnCount(
            8
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Médicament",
                "Lot",
                "Stock",
                "Prix Vente",
                "Expiration",
                "État",
                "Stock faible",
                "Fournisseur",
            ]
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setMinimumHeight(
            450
        )

        # Le scroll est assuré par la page principale.

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

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        layout.addWidget(
            self.table
        )

        # ============================================================
        # FOOTER
        # ============================================================

        footer = QLabel(
            "💡 Le stock est géré par lot. "
            "Lors d'une vente, le système utilise en priorité "
            "le lot dont la date d'expiration est la plus proche "
            "(FEFO). Les médicaments expirés ne doivent pas être vendus."
        )

        footer.setObjectName(
            "stockFooter"
        )

        footer.setWordWrap(
            True
        )

        layout.addWidget(
            footer
        )

        layout.addSpacing(
            20
        )

        # ============================================================
        # STYLE
        # ============================================================

        self.apply_styles()

        # ============================================================
        # CHARGEMENT
        # ============================================================

        self.refresh()

    # ================================================================
    # CARTE STATISTIQUE
    # ================================================================

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

        card.setMinimumHeight(
            115
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        card_layout.setSpacing(
            5
        )

        # ------------------------------------------------------------
        # Ligne supérieure
        # ------------------------------------------------------------

        top_layout = QHBoxLayout()

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

        # ------------------------------------------------------------
        # Valeur
        # ------------------------------------------------------------

        value_label = QLabel(
            value
        )

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

        # ------------------------------------------------------------
        # Ligne
        # ------------------------------------------------------------

        line = QFrame()

        line.setFixedHeight(
            4
        )

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

    # ================================================================
    # STYLE
    # ================================================================

    def apply_styles(self):

        self.setStyleSheet(
            """
            /* =====================================================
               PAGE
               ===================================================== */

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

            /* =====================================================
               SCROLLBAR
               ===================================================== */

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

            /* =====================================================
               TITRE
               ===================================================== */

            #pageTitle {
                color: #0F172A;
                font-size: 25px;
                font-weight: bold;
            }

            #pageSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            /* =====================================================
               STAT CARDS
               ===================================================== */

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

            /* =====================================================
               SEARCH
               ===================================================== */

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

            /* =====================================================
               TABLE
               ===================================================== */

            #stockTable {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #E2E8F0;
                color: #1E293B;
                font-size: 13px;
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
                font-size: 12px;
            }

            /* =====================================================
               FOOTER
               ===================================================== */

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

    # ================================================================
    # FORMATAGE DU STOCK
    # ================================================================

    def _format_stock(
        self,
        product,
        stock_units,
    ):
        """
        Transforme le stock de base en :

        Carton
        Boîte
        Plaquette
        Comprimé
        """

        try:
            units_per_plaquette = int(
                getattr(
                    product,
                    "units_per_plaquette",
                    10,
                )
                or 10
            )

            plaquettes_per_box = int(
                getattr(
                    product,
                    "units_per_box",
                    10,
                )
                or 10
            )

            boxes_per_carton = int(
                getattr(
                    product,
                    "boxes_per_carton",
                    10,
                )
                or 10
            )

            units_per_box = (
                units_per_plaquette
                * plaquettes_per_box
            )

            units_per_carton = (
                units_per_box
                * boxes_per_carton
            )

            stock = max(
                0,
                int(stock_units or 0),
            )

            cartons = (
                stock
                // units_per_carton
            )

            remainder = (
                stock
                % units_per_carton
            )

            boxes = (
                remainder
                // units_per_box
            )

            remainder = (
                remainder
                % units_per_box
            )

            plaquettes = (
                remainder
                // units_per_plaquette
            )

            comprimes = (
                remainder
                % units_per_plaquette
            )

            parts = []

            if cartons:
                parts.append(
                    f"{cartons} carton"
                    + ("s" if cartons > 1 else "")
                )

            if boxes:
                parts.append(
                    f"{boxes} boîte"
                    + ("s" if boxes > 1 else "")
                )

            if plaquettes:
                parts.append(
                    f"{plaquettes} plaquette"
                    + ("s" if plaquettes > 1 else "")
                )

            if comprimes:
                parts.append(
                    f"{comprimes} comprimé"
                    + ("s" if comprimes > 1 else "")
                )

            if not parts:
                return "0"

            return " + ".join(parts)

        except Exception:
            return str(
                int(stock_units or 0)
            )

    # ================================================================
    # RÉCUPÉRER LES LOTS
    # ================================================================

    def _get_batches(
        self,
        session,
        product,
    ):
        """
        Retourne les lots du produit.

        Les lots sont triés par date d'expiration.
        Le premier lot est donc celui qui doit être vendu en priorité.
        """

        try:
            batches = (
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

            return batches

        except Exception:
            return []

    # ================================================================
    # STOCK TOTAL D'UN PRODUIT
    # ================================================================

    def _get_product_stock(
        self,
        product,
        batches,
    ):
        """
        Calcule le stock total à partir des lots.
        """

        if batches:
            total = 0

            for batch in batches:
                total += int(
                    getattr(
                        batch,
                        "stock_units",
                        0,
                    )
                    or 0
                )

            return total

        # Compatibilité avec ancienne base.
        return int(
            getattr(
                product,
                "stock_units",
                0,
            )
            or 0
        )

    # ================================================================
    # ÉTAT EXPIRATION
    # ================================================================

    def _get_expiry_status(
        self,
        expiry_date,
        today,
        alert_limit,
    ):
        """
        Retourne :

        texte
        couleur
        catégorie
        """

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

    # ================================================================
    # RECHERCHE / ACTUALISATION
    # ================================================================

    def refresh(self):

        session = SessionLocal()

        try:

            # ========================================================
            # RECHERCHE
            # ========================================================

            search_text = (
                self.search_input
                .text()
                .strip()
                .lower()
            )

            query = (
                session.query(Product)
                .order_by(
                    Product.name.asc()
                )
            )

            products = query.all()

            # ========================================================
            # DATES
            # ========================================================

            today = date.today()

            alert_limit = (
                today
                + timedelta(
                    days=self.EXPIRY_WARNING_DAYS
                )
            )

            # ========================================================
            # COMPTEURS
            # ========================================================

            c_total_products = 0
            c_total_batches = 0
            c_expired = 0
            c_warning = 0
            c_low_stock = 0

            # ========================================================
            # VIDER TABLEAU
            # ========================================================

            self.table.setRowCount(
                0
            )

            # ========================================================
            # PRODUITS
            # ========================================================

            for product in products:

                batches = self._get_batches(
                    session,
                    product,
                )

                # ----------------------------------------------------
                # Compatibilité ancienne base
                # ----------------------------------------------------

                if not batches:

                    product_name = (
                        product.name
                        or "-"
                    )

                    batch_number = (
                        getattr(
                            product,
                            "batch_number",
                            None,
                        )
                        or "-"
                    )

                    combined_search = (
                        f"{product_name} "
                        f"{batch_number}"
                    ).lower()

                    if (
                        search_text
                        and search_text
                        not in combined_search
                    ):
                        continue

                    c_total_products += 1

                    stock_units = int(
                        getattr(
                            product,
                            "stock_units",
                            0,
                        )
                        or 0
                    )

                    expiry_date = getattr(
                        product,
                        "expiry_date",
                        None,
                    )

                    status_text, status_color, category = (
                        self._get_expiry_status(
                            expiry_date,
                            today,
                            alert_limit,
                        )
                    )

                    if category == "expired":
                        c_expired += 1

                    elif category == "warning":
                        c_warning += 1

                    # Stock faible
                    minimum_stock = int(
                        getattr(
                            product,
                            "min_quantity",
                            0,
                        )
                        or 0
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
                        batch_number=batch_number,
                        status_text=status_text,
                        status_color=status_color,
                        low_stock=low_stock,
                        minimum_stock=minimum_stock,
                    )

                    continue

                # ----------------------------------------------------
                # Nouveau système par lots
                # ----------------------------------------------------

                visible_batches = []

                for batch in batches:

                    batch_number = (
                        getattr(
                            batch,
                            "batch_number",
                            None,
                        )
                        or "-"
                    )

                    combined_search = (
                        f"{product.name or ''} "
                        f"{batch_number}"
                    ).lower()

                    if (
                        search_text
                        and search_text
                        not in combined_search
                    ):
                        continue

                    visible_batches.append(
                        batch
                    )

                if not visible_batches:
                    continue

                c_total_products += 1

                c_total_batches += len(
                    visible_batches
                )

                # ----------------------------------------------------
                # Stock total
                # ----------------------------------------------------

                total_stock = (
                    self._get_product_stock(
                        product,
                        batches,
                    )
                )

                minimum_stock = int(
                    getattr(
                        product,
                        "min_quantity",
                        0,
                    )
                    or 0
                )

                low_stock = (
                    total_stock
                    <= minimum_stock
                )

                if low_stock:
                    c_low_stock += 1

                # ----------------------------------------------------
                # Chaque lot
                # ----------------------------------------------------

                for batch in visible_batches:

                    stock_units = int(
                        getattr(
                            batch,
                            "stock_units",
                            0,
                        )
                        or 0
                    )

                    expiry_date = getattr(
                        batch,
                        "expiry_date",
                        None,
                    )

                    status_text, status_color, category = (
                        self._get_expiry_status(
                            expiry_date,
                            today,
                            alert_limit,
                        )
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
                        batch_number=(
                            getattr(
                                batch,
                                "batch_number",
                                None,
                            )
                            or "-"
                        ),
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
                + 10
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
                "Erreur lors du chargement "
                f"des stocks : {error}"
            )

        finally:

            session.close()

    # ================================================================
    # AJOUT D'UNE LIGNE
    # ================================================================

    def _add_stock_row(
        self,
        product,
        batch,
        stock_units,
        expiry_date,
        batch_number,
        status_text,
        status_color,
        low_stock,
        minimum_stock,
    ):

        row = (
            self.table.rowCount()
        )

        self.table.insertRow(
            row
        )

        self.table.setRowHeight(
            row,
            52,
        )

        # ============================================================
        # MÉDICAMENT
        # ============================================================

        product_item = QTableWidgetItem(
            product.name
            or "-"
        )

        self.table.setItem(
            row,
            0,
            product_item,
        )

        # ============================================================
        # LOT
        # ============================================================

        lot_item = QTableWidgetItem(
            batch_number
        )

        lot_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            1,
            lot_item,
        )

        # ============================================================
        # STOCK
        # ============================================================

        stock_text = self._format_stock(
            product,
            stock_units,
        )

        stock_item = QTableWidgetItem(
            stock_text
        )

        stock_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            2,
            stock_item,
        )

        # ============================================================
        # PRIX
        # ============================================================

        try:

            price = get_price_for_packaging(
                product,
                "Boîte",
            )

            price_text = (
                f"{float(price):,.2f} CDF"
            )

        except Exception:

            try:

                price = float(
                    getattr(
                        product,
                        "price",
                        0,
                    )
                    or 0
                )

                price_text = (
                    f"{price:,.2f} CDF"
                )

            except (
                TypeError,
                ValueError,
            ):

                price_text = (
                    "0.00 CDF"
                )

        price_item = QTableWidgetItem(
            price_text
        )

        price_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            3,
            price_item,
        )

        # ============================================================
        # EXPIRATION
        # ============================================================

        if expiry_date:

            try:

                exp_text = (
                    expiry_date.strftime(
                        "%d/%m/%Y"
                    )
                )

            except AttributeError:

                exp_text = str(
                    expiry_date
                )

        else:

            exp_text = (
                "N/A"
            )

        expiry_item = QTableWidgetItem(
            exp_text
        )

        expiry_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            4,
            expiry_item,
        )

        # ============================================================
        # ÉTAT EXPIRATION
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
            5,
            status_item,
        )

        # ============================================================
        # STOCK FAIBLE
        # ============================================================

        if low_stock:

            stock_status = (
                f"🟡 FAIBLE "
                f"(≤ {minimum_stock})"
            )

            stock_color = QColor(
                "#FEF3C7"
            )

        else:

            stock_status = (
                "🟢 OK"
            )

            stock_color = QColor(
                "#DCFCE7"
            )

        stock_alert_item = QTableWidgetItem(
            stock_status
        )

        stock_alert_item.setBackground(
            stock_color
        )

        stock_alert_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            6,
            stock_alert_item,
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
            supplier
            or "-"
        )

        self.table.setItem(
            row,
            7,
            supplier_item,
        )

        # ============================================================
        # DONNÉES INTERNES
        # ============================================================

        if batch is not None:

            product_item.setData(
                Qt.ItemDataRole.UserRole,
                product.id,
            )

            product_item.setData(
                Qt.ItemDataRole.UserRole + 1,
                batch.id,
            )

    # ================================================================
    # VALEUR D'UNE CARTE
    # ================================================================

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
        1250,
        800,
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()