# ui/dashboard.py

from datetime import date, datetime, timedelta
from collections import defaultdict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSizePolicy,
    QScrollArea,
    QMessageBox,
)

from database.database import (
    SessionLocal,
)

from database.models import (
    Product,
    ProductBatch,
    Sale,
    SaleItem,
    Expense,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("dashboardPage")

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # =========================================================
        # SCROLL
        # =========================================================

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.dashboard_content = QWidget()

        self.dashboard_layout = QVBoxLayout(
            self.dashboard_content
        )

        self.dashboard_layout.setContentsMargins(
            28,
            26,
            28,
            40,
        )

        self.dashboard_layout.setSpacing(22)

        self.scroll_area.setWidget(
            self.dashboard_content
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # =========================================================
        # HEADER
        # =========================================================

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel(
            "Tableau de bord"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Vue générale de l'activité de votre pharmacie"
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header_layout.addLayout(
            title_container
        )

        header_layout.addStretch()

        # =========================================================
        # FILTRE PERIODE
        # =========================================================

        period_container = QVBoxLayout()
        period_container.setSpacing(3)

        period_label = QLabel(
            "Période"
        )

        period_label.setStyleSheet("""
            color: #667085;
            font-size: 11px;
            font-weight: 600;
        """)

        self.period_combo = QComboBox()

        self.period_combo.setMinimumWidth(
            190
        )

        self.period_combo.addItems([
            "Aujourd'hui",
            "7 derniers jours",
            "30 derniers jours",
            "Cette année",
        ])

        self.period_combo.currentIndexChanged.connect(
            self.refresh
        )

        period_container.addWidget(
            period_label
        )

        period_container.addWidget(
            self.period_combo
        )

        header_layout.addLayout(
            period_container
        )

        # =========================================================
        # BOUTON ACTUALISER
        # =========================================================

        self.refresh_button = QPushButton(
            "↻  Actualiser"
        )

        self.refresh_button.setObjectName(
            "refreshButton"
        )

        self.refresh_button.setMinimumHeight(
            42
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

        header_layout.addWidget(
            self.refresh_button
        )

        self.dashboard_layout.addLayout(
            header_layout
        )

        # =========================================================
        # PETIT INDICATEUR DE PERIODE
        # =========================================================

        self.period_info = QLabel()

        self.period_info.setStyleSheet("""
            background: #eef4ff;
            color: #175cd3;
            border: 1px solid #b2ddff;
            border-radius: 9px;
            padding: 9px 13px;
            font-size: 12px;
            font-weight: 600;
        """)

        self.dashboard_layout.addWidget(
            self.period_info
        )

        # =========================================================
        # KPI
        # =========================================================

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(16)

        self.dashboard_layout.addLayout(
            self.kpi_grid
        )

        # =========================================================
        # RESUME FINANCIER
        # =========================================================

        self.financial_card = QFrame()
        self.financial_card.setObjectName(
            "financialCard"
        )

        financial_layout = QVBoxLayout(
            self.financial_card
        )

        financial_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        financial_layout.setSpacing(6)

        financial_title = QLabel(
            "Résumé financier"
        )

        financial_title.setStyleSheet("""
            color: #10233f;
            font-size: 16px;
            font-weight: 700;
        """)

        self.financial_text = QLabel()

        self.financial_text.setWordWrap(
            True
        )

        self.financial_text.setStyleSheet("""
            color: #475467;
            font-size: 13px;
            line-height: 1.4;
        """)

        financial_layout.addWidget(
            financial_title
        )

        financial_layout.addWidget(
            self.financial_text
        )

        self.dashboard_layout.addWidget(
            self.financial_card
        )

        # =========================================================
        # GRAPHIQUES
        # =========================================================

        self.charts_grid = QGridLayout()
        self.charts_grid.setSpacing(20)

        self.dashboard_layout.addLayout(
            self.charts_grid
        )

        # =========================================================
        # TOP PRODUITS
        # =========================================================

        top_products_card = self.create_section_card(
            "🏆 Produits les plus vendus",
            "Produits ayant généré le plus de ventes pendant la période sélectionnée",
        )

        top_products_layout = (
            top_products_card.layout()
        )

        self.top_products_table = QTableWidget()

        self.top_products_table.setColumnCount(4)

        self.top_products_table.setHorizontalHeaderLabels([
            "Médicament",
            "Quantité vendue",
            "Prix unitaire",
            "Chiffre d'affaires",
        ])

        self.top_products_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.top_products_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.top_products_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.top_products_table.setAlternatingRowColors(
            True
        )

        self.top_products_table.setMinimumHeight(
            300
        )

        self.top_products_table.setMaximumHeight(
            450
        )

        header = (
            self.top_products_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        top_products_layout.addWidget(
            self.top_products_table
        )

        self.dashboard_layout.addWidget(
            top_products_card
        )

        # =========================================================
        # ALERTES
        # =========================================================

        self.alerts_card = self.create_section_card(
            "⚠️ Alertes",
            "Produits et lots nécessitant une attention particulière",
        )

        self.alerts_layout = QVBoxLayout()
        self.alerts_layout.setSpacing(8)

        self.alerts_card.layout().addLayout(
            self.alerts_layout
        )

        self.dashboard_layout.addWidget(
            self.alerts_card
        )

        self.dashboard_layout.addSpacing(
            30
        )

        # =========================================================
        # STYLE
        # =========================================================

        self.apply_styles()

        # =========================================================
        # CHARGEMENT
        # =========================================================

        self.refresh()

    # =============================================================
    # UTILITAIRES
    # =============================================================

    def clear_layout(self, layout):

        if layout is None:
            return

        while layout.count():

            item = layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

            elif item.layout() is not None:
                self.clear_layout(
                    item.layout()
                )

    # =============================================================
    # STYLE
    # =============================================================

    def apply_styles(self):

        self.setStyleSheet("""
            QWidget#dashboardPage {
                background: #f4f6f9;
            }

            QLabel#pageTitle {
                color: #10233f;
                font-size: 28px;
                font-weight: 800;
            }

            QLabel#pageSubtitle {
                color: #667085;
                font-size: 13px;
            }

            QComboBox {
                background: white;
                border: 1px solid #d0d5dd;
                border-radius: 9px;
                padding: 8px 12px;
                color: #344054;
                min-height: 22px;
                font-size: 13px;
            }

            QComboBox:hover {
                border: 1px solid #98a2b3;
            }

            QComboBox:focus {
                border: 1px solid #2e90fa;
            }

            QPushButton#refreshButton {
                background: #10233f;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 10px 17px;
                font-weight: 700;
            }

            QPushButton#refreshButton:hover {
                background: #1d3557;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                background: #eef1f5;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #98a2b3;
                min-height: 45px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #667085;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QTableWidget {
                background: white;
                border: 1px solid #eaecf0;
                border-radius: 10px;
                gridline-color: #f2f4f7;
                color: #344054;
                selection-background-color: #eef4ff;
                selection-color: #10233f;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 9px;
            }

            QHeaderView::section {
                background: #f9fafb;
                color: #475467;
                border: none;
                border-bottom: 1px solid #eaecf0;
                padding: 11px;
                font-weight: 700;
            }
        """)

    # =============================================================
    # SECTION CARD
    # =============================================================

    def create_section_card(
        self,
        title_text,
        subtitle_text="",
    ):

        card = QFrame()

        card.setObjectName(
            "dashboardCard"
        )

        card.setStyleSheet("""
            QFrame#dashboardCard {
                background: white;
                border: 1px solid #eaecf0;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(8)

        title = QLabel(
            title_text
        )

        title.setStyleSheet("""
            font-size: 17px;
            font-weight: 800;
            color: #10233f;
        """)

        layout.addWidget(
            title
        )

        if subtitle_text:

            subtitle = QLabel(
                subtitle_text
            )

            subtitle.setStyleSheet("""
                font-size: 12px;
                color: #667085;
            """)

            layout.addWidget(
                subtitle
            )

        return card

    # =============================================================
    # KPI CARD PROFESSIONNELLE
    # =============================================================

    def create_kpi_card(
        self,
        title,
        value,
        icon,
        accent="#175cd3",
        background="#eef4ff",
    ):

        card = QFrame()

        card.setMinimumHeight(
            128
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        card.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #eaecf0;
                border-radius: 14px;
            }}
        """)

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(14)

        icon_container = QFrame()

        icon_container.setFixedSize(
            52,
            52,
        )

        icon_container.setStyleSheet(f"""
            QFrame {{
                background: {background};
                border-radius: 12px;
                border: 1px solid {accent};
            }}
        """)

        icon_layout = QVBoxLayout(
            icon_container
        )

        icon_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setAlignment(
            Qt.AlignCenter
        )

        icon_label.setStyleSheet(
            "font-size: 23px; border: none;"
        )

        icon_layout.addWidget(
            icon_label
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(f"""
            color: #667085;
            font-size: 12px;
            font-weight: 600;
            border: none;
        """)

        value_label = QLabel(
            str(value)
        )

        value_label.setStyleSheet(f"""
            color: {accent};
            font-size: 23px;
            font-weight: 800;
            border: none;
        """)

        value_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            value_label
        )

        layout.addWidget(
            icon_container
        )

        layout.addLayout(
            text_layout
        )

        return card

    # =============================================================
    # CHART CARD
    # =============================================================

    def create_chart_card(
        self,
        title,
        subtitle="",
    ):

        card = self.create_section_card(
            title,
            subtitle,
        )

        figure = Figure(
            figsize=(6, 3),
            tight_layout=True,
        )

        canvas = FigureCanvas(
            figure
        )

        canvas.setMinimumHeight(
            280
        )

        canvas.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        card.layout().addWidget(
            canvas
        )

        return (
            card,
            figure,
            canvas,
        )

    # =============================================================
    # REFRESH
    # =============================================================

    def refresh(self):

        session = SessionLocal()

        try:

            products = (
                session.query(Product)
                .all()
            )

            batches = (
                session.query(ProductBatch)
                .all()
            )

            sales = (
                session.query(Sale)
                .all()
            )

            sale_items = (
                session.query(SaleItem)
                .all()
            )

            try:
                expenses = (
                    session.query(Expense)
                    .all()
                )
            except Exception:
                expenses = []

            # -----------------------------------------------------
            # KPI
            # -----------------------------------------------------

            self.update_kpis(
                products,
                batches,
                sales,
                expenses,
            )

            # -----------------------------------------------------
            # GRAPHIQUES
            # -----------------------------------------------------

            self.update_revenue_chart(
                sales
            )

            self.update_sales_chart(
                sales
            )

            self.update_expenses_chart(
                expenses
            )

            self.update_stock_chart(
                products,
                batches,
            )

            # -----------------------------------------------------
            # TOP PRODUITS
            # -----------------------------------------------------

            self.update_top_products(
                session,
                products,
                sales,
                sale_items,
            )

            # -----------------------------------------------------
            # ALERTES
            # -----------------------------------------------------

            self.update_alerts(
                products,
                batches,
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger "
                    "le tableau de bord.\n\n"
                    f"{error}"
                ),
            )

        finally:

            session.close()

    # =============================================================
    # PERIODE
    # =============================================================

    def get_selected_period(self):

        today = date.today()

        index = (
            self.period_combo
            .currentIndex()
        )

        if index == 0:

            return today, today

        if index == 1:

            return (
                today - timedelta(days=6),
                today,
            )

        if index == 2:

            return (
                today - timedelta(days=29),
                today,
            )

        return (
            date(today.year, 1, 1),
            today,
        )

    # =============================================================
    # DATE VENTE
    # =============================================================

    def get_sale_date(
        self,
        sale,
    ):

        possible_fields = [
            "created_at",
            "sale_date",
            "date",
            "createdAt",
        ]

        for field in possible_fields:

            value = getattr(
                sale,
                field,
                None,
            )

            if value is None:
                continue

            if isinstance(
                value,
                datetime,
            ):
                return value.date()

            if isinstance(
                value,
                date,
            ):
                return value

        return None

    # =============================================================
    # DATE DEPENSE
    # =============================================================

    def get_expense_date(
        self,
        expense,
    ):

        possible_fields = [
            "expense_date",
            "created_at",
            "date",
        ]

        for field in possible_fields:

            value = getattr(
                expense,
                field,
                None,
            )

            if value is None:
                continue

            if isinstance(
                value,
                datetime,
            ):
                return value.date()

            if isinstance(
                value,
                date,
            ):
                return value

        return None

    # =============================================================
    # FILTRER DEPENSES
    # =============================================================

    def get_period_expenses(
        self,
        expenses,
    ):

        start_date, end_date = (
            self.get_selected_period()
        )

        result = []

        for expense in expenses:

            expense_date = (
                self.get_expense_date(
                    expense
                )
            )

            if expense_date is None:
                continue

            if (
                start_date
                <= expense_date
                <= end_date
            ):
                result.append(
                    expense
                )

        return result

    # =============================================================
    # NORMALIZE DATE
    # =============================================================

    def normalize_date(
        self,
        value,
    ):

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        return None

    # =============================================================
    # STOCK PRODUIT
    # =============================================================

    def get_product_stock(
        self,
        product,
        batches,
        include_expired=False,
    ):

        today = date.today()

        total = 0

        for batch in batches:

            if (
                getattr(
                    batch,
                    "product_id",
                    None,
                )
                != getattr(
                    product,
                    "id",
                    None,
                )
            ):
                continue

            quantity = int(
                getattr(
                    batch,
                    "stock_units",
                    0,
                )
                or 0
            )

            if quantity <= 0:
                continue

            expiry = self.normalize_date(
                getattr(
                    batch,
                    "expiry_date",
                    None,
                )
            )

            if (
                not include_expired
                and expiry is not None
                and expiry < today
            ):
                continue

            total += quantity

        if total == 0 and not batches:

            total = int(
                getattr(
                    product,
                    "stock_units",
                    0,
                )
                or getattr(
                    product,
                    "quantity",
                    0,
                )
                or 0
            )

        return total

    # =============================================================
    # STOCK AFFICHABLE
    # =============================================================

    def format_stock(
        self,
        product,
        stock_units,
    ):

        try:

            tablets_per_blister = max(
                1,
                int(
                    getattr(
                        product,
                        "units_per_plaquette",
                        1,
                    )
                    or 1
                ),
            )

            blisters_per_box = max(
                1,
                int(
                    getattr(
                        product,
                        "units_per_box",
                        1,
                    )
                    or 1
                ),
            )

            boxes_per_carton = max(
                1,
                int(
                    getattr(
                        product,
                        "boxes_per_carton",
                        1,
                    )
                    or 1
                ),
            )

            tablets_per_box = (
                tablets_per_blister
                * blisters_per_box
            )

            tablets_per_carton = (
                tablets_per_box
                * boxes_per_carton
            )

            remaining = max(
                int(stock_units),
                0,
            )

            cartons = (
                remaining
                // tablets_per_carton
            )

            remaining %= (
                tablets_per_carton
            )

            boxes = (
                remaining
                // tablets_per_box
            )

            remaining %= (
                tablets_per_box
            )

            blisters = (
                remaining
                // tablets_per_blister
            )

            tablets = (
                remaining
                % tablets_per_blister
            )

            parts = []

            if cartons:
                parts.append(
                    f"{cartons} carton(s)"
                )

            if boxes:
                parts.append(
                    f"{boxes} boîte(s)"
                )

            if blisters:
                parts.append(
                    f"{blisters} plaquette(s)"
                )

            if tablets:
                parts.append(
                    f"{tablets} comprimé(s)"
                )

            if not parts:
                return "0 comprimé"

            return " + ".join(parts)

        except Exception:

            return f"{stock_units} unité(s)"

    # =============================================================
    # PRIX UNITE BASE
    # =============================================================

    def get_sale_price_per_base_unit(
        self,
        product,
    ):

        direct_price = getattr(
            product,
            "price_per_comprime",
            None,
        )

        try:
            direct_price = float(
                direct_price or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            direct_price = 0.0

        if direct_price > 0:
            return direct_price

        try:

            price = float(
                getattr(
                    product,
                    "price",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            price = 0.0

        if price <= 0:
            return 0.0

        packaging = str(
            getattr(
                product,
                "packaging",
                "Comprimé",
            )
            or "Comprimé"
        ).strip().lower()

        try:

            tablets_per_blister = max(
                1,
                int(
                    getattr(
                        product,
                        "units_per_plaquette",
                        1,
                    )
                    or 1
                ),
            )

            blisters_per_box = max(
                1,
                int(
                    getattr(
                        product,
                        "units_per_box",
                        1,
                    )
                    or 1
                ),
            )

            boxes_per_carton = max(
                1,
                int(
                    getattr(
                        product,
                        "boxes_per_carton",
                        1,
                    )
                    or 1
                ),
            )

        except (
            TypeError,
            ValueError,
        ):

            tablets_per_blister = 1
            blisters_per_box = 1
            boxes_per_carton = 1

        tablets_per_box = (
            tablets_per_blister
            * blisters_per_box
        )

        tablets_per_carton = (
            tablets_per_box
            * boxes_per_carton
        )

        if "carton" in packaging:
            return (
                price
                / tablets_per_carton
            )

        if (
            "boîte" in packaging
            or "boite" in packaging
        ):
            return (
                price
                / tablets_per_box
            )

        if "plaquette" in packaging:
            return (
                price
                / tablets_per_blister
            )

        return price

    # =============================================================
    # VALEUR STOCK
    # =============================================================

    def calculate_stock_sale_value(
        self,
        products,
        batches,
    ):

        total_value = 0.0

        for product in products:

            stock_units = (
                self.get_product_stock(
                    product,
                    batches,
                    include_expired=False,
                )
            )

            if stock_units <= 0:
                continue

            unit_price = (
                self.get_sale_price_per_base_unit(
                    product
                )
            )

            total_value += (
                stock_units
                * unit_price
            )

        return total_value

    # =============================================================
    # MONEY
    # =============================================================

    def format_money(
        self,
        amount,
    ):

        try:
            amount = float(
                amount or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            amount = 0.0

        return f"{amount:,.2f} CDF"

    # =============================================================
    # KPI
    # =============================================================

    def update_kpis(
        self,
        products,
        batches,
        sales,
        expenses,
    ):

        total_products = len(
            products
        )

        today = date.today()

        # ---------------------------------------------------------
        # STOCK
        # ---------------------------------------------------------

        total_stock_units = 0

        for product in products:

            total_stock_units += (
                self.get_product_stock(
                    product,
                    batches,
                    include_expired=False,
                )
            )

        stock_sale_value = (
            self.calculate_stock_sale_value(
                products,
                batches,
            )
        )

        # ---------------------------------------------------------
        # VENTES PERIODE
        # ---------------------------------------------------------

        start_date, end_date = (
            self.get_selected_period()
        )

        period_sales = []

        for sale in sales:

            sale_date = (
                self.get_sale_date(
                    sale
                )
            )

            if sale_date is None:
                continue

            if (
                start_date
                <= sale_date
                <= end_date
            ):
                period_sales.append(
                    sale
                )

        total_sales = len(
            period_sales
        )

        revenue = sum(
            float(
                getattr(
                    sale,
                    "total",
                    0,
                )
                or 0
            )
            for sale in period_sales
        )

        # ---------------------------------------------------------
        # DEPENSES
        # ---------------------------------------------------------

        period_expenses = (
            self.get_period_expenses(
                expenses
            )
        )

        total_expenses = sum(
            float(
                getattr(
                    expense,
                    "amount",
                    0,
                )
                or 0
            )
            for expense in period_expenses
        )

        expense_count = len(
            period_expenses
        )

        financial_result = (
            revenue
            - total_expenses
        )

        # ---------------------------------------------------------
        # STOCK FAIBLE
        # ---------------------------------------------------------

        low_stock = 0

        for product in products:

            stock = (
                self.get_product_stock(
                    product,
                    batches,
                    include_expired=False,
                )
            )

            minimum = int(
                getattr(
                    product,
                    "min_quantity",
                    0,
                )
                or 0
            )

            if stock <= minimum:
                low_stock += 1

        # ---------------------------------------------------------
        # LOTS EXPIRES
        # ---------------------------------------------------------

        expired_batches = 0

        for batch in batches:

            stock = int(
                getattr(
                    batch,
                    "stock_units",
                    0,
                )
                or 0
            )

            if stock <= 0:
                continue

            expiry = self.normalize_date(
                getattr(
                    batch,
                    "expiry_date",
                    None,
                )
            )

            if (
                expiry is not None
                and expiry < today
            ):
                expired_batches += 1

        # ---------------------------------------------------------
        # KPI
        # ---------------------------------------------------------

        self.clear_layout(
            self.kpi_grid
        )

        cards = [

            (
                "Produits",
                total_products,
                "💊",
                "#175CD3",
                "#EFF8FF",
            ),

            (
                "Stock disponible",
                self.format_total_stock(
                    total_stock_units
                ),
                "📦",
                "#1570EF",
                "#EFF8FF",
            ),

            (
                "Valeur du stock",
                self.format_money(
                    stock_sale_value
                ),
                "💵",
                "#039855",
                "#ECFDF3",
            ),

            (
                "Ventes encaissées",
                total_sales,
                "🛒",
                "#7A5AF8",
                "#F4F3FF",
            ),

            (
                "Montant encaissé",
                self.format_money(
                    revenue
                ),
                "💰",
                "#039855",
                "#ECFDF3",
            ),

            (
                "Dépenses",
                self.format_money(
                    total_expenses
                ),
                "💸",
                "#D92D20",
                "#FEF3F2",
            ),

            (
                "Nombre de dépenses",
                expense_count,
                "🧾",
                "#B54708",
                "#FFFAEB",
            ),

            (
                "Résultat",
                self.format_money(
                    financial_result
                ),
                "📊",
                (
                    "#039855"
                    if financial_result >= 0
                    else "#D92D20"
                ),
                (
                    "#ECFDF3"
                    if financial_result >= 0
                    else "#FEF3F2"
                ),
            ),

            (
                "Stock faible",
                low_stock,
                "⚠️",
                "#B54708",
                "#FFFAEB",
            ),

            (
                "Lots expirés",
                expired_batches,
                "⛔",
                "#D92D20",
                "#FEF3F2",
            ),
        ]

        for index, (
            title,
            value,
            icon,
            accent,
            background,
        ) in enumerate(cards):

            card = self.create_kpi_card(
                title,
                value,
                icon,
                accent,
                background,
            )

            row = index // 4
            column = index % 4

            self.kpi_grid.addWidget(
                card,
                row,
                column,
            )

        # ---------------------------------------------------------
        # PERIODE
        # ---------------------------------------------------------

        period_name = (
            self.period_combo.currentText()
        )

        self.period_info.setText(
            (
                f"📅 Période analysée : "
                f"{period_name}  •  "
                f"{start_date.strftime('%d/%m/%Y')}"
                f" → "
                f"{end_date.strftime('%d/%m/%Y')}"
            )
        )

        # ---------------------------------------------------------
        # RESUME FINANCIER
        # ---------------------------------------------------------

        self.financial_text.setText(
            (
                f"💰 Encaissements : "
                f"{self.format_money(revenue)}"
                f"    •    "
                f"💸 Dépenses : "
                f"{self.format_money(total_expenses)}"
                f"    •    "
                f"📊 Résultat : "
                f"{self.format_money(financial_result)}"
                f"\n\n"
                f"📦 Valeur actuelle du stock : "
                f"{self.format_money(stock_sale_value)}"
            )
        )

    # =============================================================
    # STOCK TOTAL
    # =============================================================

    def format_total_stock(
        self,
        total_units,
    ):

        if total_units <= 0:
            return "0"

        return f"{total_units:,} unités"

    # =============================================================
    # GRAPHIQUE CA
    # =============================================================

    def update_revenue_chart(
        self,
        sales,
    ):

        if not hasattr(
            self,
            "revenue_card",
        ):

            (
                self.revenue_card,
                self.revenue_figure,
                self.revenue_canvas,
            ) = self.create_chart_card(
                "💰 Encaissements",
                "Évolution des ventes encaissées",
            )

            self.charts_grid.addWidget(
                self.revenue_card,
                0,
                0,
            )

        start_date, end_date = (
            self.get_selected_period()
        )

        data = defaultdict(float)

        current = start_date

        while current <= end_date:

            data[current] = 0.0

            current += timedelta(
                days=1
            )

        for sale in sales:

            sale_date = (
                self.get_sale_date(
                    sale
                )
            )

            if sale_date is None:
                continue

            if (
                start_date
                <= sale_date
                <= end_date
            ):

                data[sale_date] += float(
                    getattr(
                        sale,
                        "total",
                        0,
                    )
                    or 0
                )

        dates = sorted(
            data.keys()
        )

        values = [
            data[d]
            for d in dates
        ]

        self.revenue_figure.clear()

        ax = (
            self.revenue_figure
            .add_subplot(111)
        )

        if dates:

            labels = [
                d.strftime("%d/%m")
                for d in dates
            ]

            ax.plot(
                labels,
                values,
                marker="o",
                linewidth=2.5,
            )

            ax.fill_between(
                range(len(values)),
                values,
                alpha=0.10,
            )

        ax.set_title(
            "Montant encaissé par jour"
        )

        ax.set_ylabel(
            "CDF"
        )

        ax.grid(
            True,
            alpha=0.20,
        )

        self.revenue_figure.autofmt_xdate()

        self.revenue_canvas.draw()

    # =============================================================
    # GRAPHIQUE VENTES
    # =============================================================

    def update_sales_chart(
        self,
        sales,
    ):

        if not hasattr(
            self,
            "sales_card",
        ):

            (
                self.sales_card,
                self.sales_figure,
                self.sales_canvas,
            ) = self.create_chart_card(
                "🛒 Ventes",
                "Nombre de ventes par jour",
            )

            self.charts_grid.addWidget(
                self.sales_card,
                0,
                1,
            )

        start_date, end_date = (
            self.get_selected_period()
        )

        data = defaultdict(int)

        current = start_date

        while current <= end_date:

            data[current] = 0

            current += timedelta(
                days=1
            )

        for sale in sales:

            sale_date = (
                self.get_sale_date(
                    sale
                )
            )

            if sale_date is None:
                continue

            if (
                start_date
                <= sale_date
                <= end_date
            ):

                data[sale_date] += 1

        dates = sorted(
            data.keys()
        )

        values = [
            data[d]
            for d in dates
        ]

        self.sales_figure.clear()

        ax = (
            self.sales_figure
            .add_subplot(111)
        )

        if dates:

            labels = [
                d.strftime("%d/%m")
                for d in dates
            ]

            ax.plot(
                labels,
                values,
                marker="o",
                linewidth=2.5,
            )

        ax.set_title(
            "Évolution des ventes"
        )

        ax.set_ylabel(
            "Nombre de ventes"
        )

        ax.grid(
            True,
            alpha=0.20,
        )

        self.sales_figure.autofmt_xdate()

        self.sales_canvas.draw()

    # =============================================================
    # GRAPHIQUE DEPENSES
    # =============================================================

    def update_expenses_chart(
        self,
        expenses,
    ):

        if not hasattr(
            self,
            "expenses_card",
        ):

            (
                self.expenses_card,
                self.expenses_figure,
                self.expenses_canvas,
            ) = self.create_chart_card(
                "💸 Dépenses",
                "Évolution des dépenses par jour",
            )

            self.charts_grid.addWidget(
                self.expenses_card,
                1,
                1,
            )

        start_date, end_date = (
            self.get_selected_period()
        )

        data = defaultdict(float)

        current = start_date

        while current <= end_date:

            data[current] = 0.0

            current += timedelta(
                days=1
            )

        for expense in expenses:

            expense_date = (
                self.get_expense_date(
                    expense
                )
            )

            if expense_date is None:
                continue

            if (
                start_date
                <= expense_date
                <= end_date
            ):

                data[expense_date] += float(
                    getattr(
                        expense,
                        "amount",
                        0,
                    )
                    or 0
                )

        dates = sorted(
            data.keys()
        )

        values = [
            data[d]
            for d in dates
        ]

        self.expenses_figure.clear()

        ax = (
            self.expenses_figure
            .add_subplot(111)
        )

        if dates:

            labels = [
                d.strftime("%d/%m")
                for d in dates
            ]

            ax.bar(
                labels,
                values,
            )

        ax.set_title(
            "Dépenses par jour"
        )

        ax.set_ylabel(
            "CDF"
        )

        ax.grid(
            axis="y",
            alpha=0.20,
        )

        self.expenses_figure.autofmt_xdate()

        self.expenses_canvas.draw()

    # =============================================================
    # GRAPHIQUE STOCK
    # =============================================================

    def update_stock_chart(
        self,
        products,
        batches,
    ):

        if not hasattr(
            self,
            "stock_card",
        ):

            (
                self.stock_card,
                self.stock_figure,
                self.stock_canvas,
            ) = self.create_chart_card(
                "📦 État du stock",
                "Situation actuelle du stock",
            )

            self.charts_grid.addWidget(
                self.stock_card,
                1,
                0,
            )

        today = date.today()

        normal = 0
        low = 0
        expired = 0
        expiring = 0

        for product in products:

            product_has_expired = False
            product_expires_soon = False

            product_batches = [
                batch
                for batch in batches
                if getattr(
                    batch,
                    "product_id",
                    None,
                )
                == getattr(
                    product,
                    "id",
                    None,
                )
            ]

            for batch in product_batches:

                stock = int(
                    getattr(
                        batch,
                        "stock_units",
                        0,
                    )
                    or 0
                )

                if stock <= 0:
                    continue

                expiry = self.normalize_date(
                    getattr(
                        batch,
                        "expiry_date",
                        None,
                    )
                )

                if expiry is None:
                    continue

                if expiry < today:

                    product_has_expired = True

                elif expiry <= (
                    today
                    + timedelta(days=90)
                ):

                    product_expires_soon = True

            if product_has_expired:

                expired += 1

                continue

            if product_expires_soon:

                expiring += 1

            stock = self.get_product_stock(
                product,
                batches,
                include_expired=False,
            )

            minimum = int(
                getattr(
                    product,
                    "min_quantity",
                    0,
                )
                or 0
            )

            if stock <= minimum:

                low += 1

            else:

                normal += 1

        labels = [
            "Normal",
            "Stock faible",
            "Expire bientôt",
            "Expiré",
        ]

        values = [
            normal,
            low,
            expiring,
            expired,
        ]

        self.stock_figure.clear()

        ax = (
            self.stock_figure
            .add_subplot(111)
        )

        ax.bar(
            labels,
            values,
        )

        ax.set_title(
            "État du stock"
        )

        ax.set_ylabel(
            "Nombre de produits"
        )

        ax.grid(
            axis="y",
            alpha=0.20,
        )

        self.stock_canvas.draw()

    # =============================================================
    # TOP PRODUITS
    # =============================================================

    def update_top_products(
        self,
        session,
        products,
        sales,
        sale_items,
    ):

        self.top_products_table.setRowCount(
            0
        )

        product_map = {
            product.id: product
            for product in products
        }

        quantities = defaultdict(int)
        revenues = defaultdict(float)

        start_date, end_date = (
            self.get_selected_period()
        )

        valid_sale_ids = set()

        for sale in sales:

            sale_date = (
                self.get_sale_date(
                    sale
                )
            )

            if sale_date is None:
                continue

            if (
                start_date
                <= sale_date
                <= end_date
            ):

                valid_sale_ids.add(
                    sale.id
                )

        for sale in sales:

            if sale.id not in valid_sale_ids:
                continue

            items = getattr(
                sale,
                "items",
                None,
            )

            if items is None:

                items = [
                    item
                    for item in sale_items
                    if getattr(
                        item,
                        "sale_id",
                        None,
                    )
                    == sale.id
                ]

            for item in items:

                product_id = getattr(
                    item,
                    "product_id",
                    None,
                )

                if product_id not in product_map:
                    continue

                quantity = int(
                    getattr(
                        item,
                        "quantity",
                        0,
                    )
                    or 0
                )

                unit_price = float(
                    getattr(
                        item,
                        "unit_price",
                        0,
                    )
                    or 0
                )

                quantities[
                    product_id
                ] += quantity

                revenues[
                    product_id
                ] += (
                    quantity
                    * unit_price
                )

        sorted_products = sorted(
            quantities.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        self.top_products_table.setRowCount(
            len(sorted_products)
        )

        for row, (
            product_id,
            quantity,
        ) in enumerate(
            sorted_products
        ):

            product = (
                product_map[
                    product_id
                ]
            )

            price = float(
                getattr(
                    product,
                    "price",
                    0,
                )
                or 0
            )

            revenue = revenues[
                product_id
            ]

            item_name = QTableWidgetItem(
                str(
                    getattr(
                        product,
                        "name",
                        "Inconnu",
                    )
                )
            )

            item_qty = QTableWidgetItem(
                str(quantity)
            )

            item_price = QTableWidgetItem(
                f"{price:,.2f} CDF"
            )

            item_revenue = QTableWidgetItem(
                f"{revenue:,.2f} CDF"
            )

            item_qty.setTextAlignment(
                Qt.AlignCenter
            )

            item_price.setTextAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            item_revenue.setTextAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            self.top_products_table.setItem(
                row,
                0,
                item_name,
            )

            self.top_products_table.setItem(
                row,
                1,
                item_qty,
            )

            self.top_products_table.setItem(
                row,
                2,
                item_price,
            )

            self.top_products_table.setItem(
                row,
                3,
                item_revenue,
            )

    # =============================================================
    # ALERTES
    # =============================================================

    def update_alerts(
        self,
        products,
        batches,
    ):

        self.clear_layout(
            self.alerts_layout
        )

        today = date.today()

        alerts_found = False

        for product in products:

            product_name = getattr(
                product,
                "name",
                "Produit inconnu",
            )

            product_batches = [
                batch
                for batch in batches
                if getattr(
                    batch,
                    "product_id",
                    None,
                )
                == getattr(
                    product,
                    "id",
                    None,
                )
            ]

            for batch in product_batches:

                stock = int(
                    getattr(
                        batch,
                        "stock_units",
                        0,
                    )
                    or 0
                )

                if stock <= 0:
                    continue

                expiry = self.normalize_date(
                    getattr(
                        batch,
                        "expiry_date",
                        None,
                    )
                )

                batch_number = str(
                    getattr(
                        batch,
                        "batch_number",
                        "Sans lot",
                    )
                )

                if (
                    expiry is not None
                    and expiry < today
                ):

                    alerts_found = True

                    lbl = QLabel(
                        (
                            f"⛔ {product_name} "
                            f"(Lot {batch_number}) "
                            f"est expiré depuis le "
                            f"{expiry.strftime('%d/%m/%Y')}."
                        )
                    )

                    lbl.setStyleSheet("""
                        background: #fef3f2;
                        color: #b42318;
                        border: 1px solid #fecdca;
                        border-radius: 8px;
                        padding: 10px 13px;
                        font-size: 13px;
                        font-weight: 600;
                    """)

                    self.alerts_layout.addWidget(
                        lbl
                    )

                    continue

                if (
                    expiry is not None
                    and expiry <= (
                        today
                        + timedelta(days=30)
                    )
                ):

                    alerts_found = True

                    lbl = QLabel(
                        (
                            f"⚠️ {product_name} "
                            f"(Lot {batch_number}) "
                            f"expire bientôt : "
                            f"{expiry.strftime('%d/%m/%Y')}."
                        )
                    )

                    lbl.setStyleSheet("""
                        background: #fffaeb;
                        color: #b54708;
                        border: 1px solid #fedf89;
                        border-radius: 8px;
                        padding: 10px 13px;
                        font-size: 13px;
                        font-weight: 600;
                    """)

                    self.alerts_layout.addWidget(
                        lbl
                    )

        for product in products:

            stock = self.get_product_stock(
                product,
                batches,
                include_expired=False,
            )

            minimum = int(
                getattr(
                    product,
                    "min_quantity",
                    0,
                )
                or 0
            )

            if stock <= minimum:

                alerts_found = True

                name = getattr(
                    product,
                    "name",
                    "Produit inconnu",
                )

                stock_display = (
                    self.format_stock(
                        product,
                        stock,
                    )
                )

                lbl = QLabel(
                    (
                        f"⚠️ Stock faible pour "
                        f"{name} : "
                        f"{stock_display} "
                        f"(minimum : {minimum})."
                    )
                )

                lbl.setStyleSheet("""
                    background: #fffaeb;
                    color: #b54708;
                    border: 1px solid #fedf89;
                    border-radius: 8px;
                    padding: 10px 13px;
                    font-size: 13px;
                    font-weight: 600;
                """)

                self.alerts_layout.addWidget(
                    lbl
                )

        if not alerts_found:

            no_alert = QLabel(
                "✅ Aucune alerte pour le moment."
            )

            no_alert.setStyleSheet("""
                color: #027a48;
                background: #ecfdf3;
                border: 1px solid #abefc6;
                border-radius: 8px;
                padding: 10px 13px;
                font-size: 13px;
                font-weight: 600;
            """)

            self.alerts_layout.addWidget(
                no_alert
            )