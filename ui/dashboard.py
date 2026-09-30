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
    get_stock_display,
    get_units_for_packaging,
)

from database.models import (
    Product,
    ProductBatch,
    Sale,
    SaleItem,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DashboardPage(QWidget):
    """
    Tableau de bord professionnel de la pharmacie.

    Gestion compatible avec :

        Carton
            ↓
        Boîte
            ↓
        Plaquette
            ↓
        Comprimé

    Le stock réel est exprimé dans l'unité de base
    (généralement le comprimé).

    Les stocks sont gérés par LOT afin de pouvoir :

    - connaître la date d'expiration de chaque lot ;
    - détecter les lots expirés ;
    - détecter les lots qui expirent bientôt ;
    - calculer le stock disponible ;
    - appliquer une logique FEFO lors des ventes ;
    - afficher correctement les stocks dans le dashboard.
    """

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
        # SCROLL AREA
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

        self.scroll_area.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        # =========================================================
        # CONTENU
        # =========================================================

        self.dashboard_content = QWidget()

        self.dashboard_content.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum,
        )

        self.dashboard_layout = QVBoxLayout(
            self.dashboard_content
        )

        self.dashboard_layout.setContentsMargins(
            24,
            24,
            24,
            40,
        )

        self.dashboard_layout.setSpacing(20)

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
        header_layout.setSpacing(12)

        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel("Tableau de bord")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Vue générale de l'activité de votre pharmacie"
        )

        subtitle.setObjectName("pageSubtitle")

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header_layout.addLayout(
            title_container
        )

        header_layout.addStretch()

        # =========================================================
        # FILTRE PERIODE
        # =========================================================

        self.period_combo = QComboBox()
        self.period_combo.setMinimumWidth(180)

        self.period_combo.addItems([
            "Aujourd'hui",
            "7 derniers jours",
            "30 derniers jours",
            "Cette année",
        ])

        self.period_combo.currentIndexChanged.connect(
            self.refresh
        )

        # =========================================================
        # BOUTON ACTUALISER
        # =========================================================

        self.refresh_button = QPushButton(
            "↻  Actualiser"
        )

        self.refresh_button.setMinimumHeight(40)

        self.refresh_button.clicked.connect(
            self.refresh
        )

        header_layout.addWidget(
            self.period_combo
        )

        header_layout.addWidget(
            self.refresh_button
        )

        self.dashboard_layout.addLayout(
            header_layout
        )

        # =========================================================
        # KPI
        # =========================================================

        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(15)

        self.dashboard_layout.addLayout(
            self.kpi_grid
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
            "Produits ayant généré le plus de ventes",
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

        self.top_products_table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.top_products_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.top_products_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
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

        # =========================================================
        # ESPACE FINAL
        # =========================================================

        self.dashboard_layout.addSpacing(30)

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
        """
        Supprime proprement les widgets d'un layout.
        """

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
                background: #f5f7fa;
            }

            QLabel#pageTitle {
                color: #10233f;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #667085;
                font-size: 13px;
            }

            QComboBox {
                background: white;
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                padding: 8px 12px;
                color: #344054;
                min-height: 22px;
            }

            QComboBox:hover {
                border: 1px solid #98a2b3;
            }

            QPushButton {
                background: #10233f;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
            }

            QPushButton:hover {
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
                border-radius: 8px;
                gridline-color: #f2f4f7;
                color: #344054;
                selection-background-color: #eef4ff;
                selection-color: #10233f;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QHeaderView::section {
                background: #f9fafb;
                color: #475467;
                border: none;
                border-bottom: 1px solid #eaecf0;
                padding: 10px;
                font-weight: 600;
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
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(10)

        title = QLabel(
            title_text
        )

        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
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
    # KPI CARD
    # =============================================================

    def create_kpi_card(
        self,
        title,
        value,
        icon,
    ):

        card = QFrame()

        card.setMinimumHeight(
            115
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #eaecf0;
                border-radius: 12px;
            }
        """)

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(14)

        icon_label = QLabel(
            icon
        )

        icon_label.setFixedSize(
            48,
            48,
        )

        icon_label.setAlignment(
            Qt.AlignCenter
        )

        icon_label.setStyleSheet("""
            background: #eef4ff;
            border-radius: 10px;
            font-size: 22px;
        """)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            color: #667085;
            font-size: 12px;
            font-weight: 500;
        """)

        value_label = QLabel(
            str(value)
        )

        value_label.setStyleSheet("""
            color: #10233f;
            font-size: 24px;
            font-weight: 700;
        """)

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            value_label
        )

        layout.addWidget(
            icon_label
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

            # -----------------------------------------------------
            # KPI
            # -----------------------------------------------------

            self.update_kpis(
                products,
                batches,
                sales,
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

    def get_sale_date(self, sale):

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
    # DATE EXPIRATION
    # =============================================================

    def normalize_date(self, value):

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
    # STOCK TOTAL D'UN PRODUIT
    # =============================================================

    def get_product_stock(
        self,
        product,
        batches,
        include_expired=False,
    ):
        """
        Retourne le stock réel en unité de base.

        Exemple :

        1 carton = 10 boîtes
        1 boîte = 10 plaquettes
        1 plaquette = 10 comprimés

        Si un lot possède 1000 comprimés,
        le stock retourné est 1000.

        Les lots expirés sont exclus par défaut.
        """

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

        # ---------------------------------------------------------
        # Compatibilité avec l'ancien système
        # ---------------------------------------------------------

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
        """
        Transforme le stock de base en :

        cartons + boîtes + plaquettes + comprimés.
        """

        try:

            tablets_per_blister = int(
                getattr(
                    product,
                    "units_per_plaquette",
                    1,
                )
                or 1
            )

            blisters_per_box = int(
                getattr(
                    product,
                    "units_per_box",
                    1,
                )
                or 1
            )

            boxes_per_carton = int(
                getattr(
                    product,
                    "boxes_per_carton",
                    1,
                )
                or 1
            )

            tablets_per_blister = max(
                tablets_per_blister,
                1,
            )

            blisters_per_box = max(
                blisters_per_box,
                1,
            )

            boxes_per_carton = max(
                boxes_per_carton,
                1,
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
    # KPI
    # =============================================================

    def update_kpis(
        self,
        products,
        batches,
        sales,
    ):

        total_products = len(
            products
        )

        today = date.today()

        # ---------------------------------------------------------
        # STOCK TOTAL
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

        # ---------------------------------------------------------
        # VENTES DE LA PERIODE
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
        # AFFICHAGE KPI
        # ---------------------------------------------------------

        self.clear_layout(
            self.kpi_grid
        )

        cards = [

            (
                "Produits",
                total_products,
                "💊",
            ),

            (
                "Stock disponible",
                self.format_total_stock(
                    total_stock_units
                ),
                "📦",
            ),

            (
                "Ventes",
                total_sales,
                "🛒",
            ),

            (
                "Chiffre d'affaires",
                f"{revenue:,.2f}",
                "💰",
            ),

            (
                "Stock faible",
                low_stock,
                "⚠️",
            ),

            (
                "Lots expirés",
                expired_batches,
                "⛔",
            ),
        ]

        for index, (
            title,
            value,
            icon,
        ) in enumerate(cards):

            card = self.create_kpi_card(
                title,
                value,
                icon,
            )

            row = index // 3
            column = index % 3

            self.kpi_grid.addWidget(
                card,
                row,
                column,
            )

    # =============================================================
    # FORMAT STOCK TOTAL
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
                "💰 Chiffre d'affaires",
                "Évolution du chiffre d'affaires",
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
                linewidth=2,
            )

            ax.fill_between(
                range(len(values)),
                values,
                alpha=0.10,
            )

        ax.set_title(
            "Évolution du chiffre d'affaires"
        )

        ax.set_ylabel(
            "Montant"
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
                linewidth=2,
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
                "Répartition des produits",
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

            # -----------------------------------------------------
            # Examiner les lots du produit
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Priorité : expiré
            # -----------------------------------------------------

            if product_has_expired:

                expired += 1

                continue

            # -----------------------------------------------------
            # Expiration prochaine
            # -----------------------------------------------------

            if product_expires_soon:

                expiring += 1

            # -----------------------------------------------------
            # Stock
            # -----------------------------------------------------

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

        # ---------------------------------------------------------
        # FILTRE DES VENTES
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # ARTICLES VENDUS
        # ---------------------------------------------------------

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

                # -------------------------------------------------
                # IMPORTANT
                #
                # quantity = quantité vendue dans l'unité choisie
                #
                # Exemple :
                #
                # 2 boîtes
                # 5 plaquettes
                # 10 comprimés
                #
                # On conserve ici la quantité commerciale
                # enregistrée dans la vente.
                # -------------------------------------------------

                quantities[
                    product_id
                ] += quantity

                revenues[
                    product_id
                ] += (
                    quantity
                    * unit_price
                )

        # ---------------------------------------------------------
        # TRI
        # ---------------------------------------------------------

        sorted_products = sorted(
            quantities.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        self.top_products_table.setRowCount(
            len(sorted_products)
        )

        # ---------------------------------------------------------
        # AFFICHAGE
        # ---------------------------------------------------------

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
                f"{price:,.2f}"
            )

            item_revenue = QTableWidgetItem(
                f"{revenue:,.2f}"
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

        # ---------------------------------------------------------
        # ALERTES PAR LOT
        # ---------------------------------------------------------

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

                # Aucun stock dans ce lot
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

                # -------------------------------------------------
                # LOT EXPIRE
                # -------------------------------------------------

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
                        color: #d92d20;
                        border: 1px solid #d92d20;
                        border-radius: 6px;
                        padding: 8px 12px;
                        font-size: 13px;
                        font-weight: 500;
                    """)

                    self.alerts_layout.addWidget(
                        lbl
                    )

                    continue

                # -------------------------------------------------
                # LOT EXPIRE DANS 30 JOURS
                # -------------------------------------------------

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
                        color: #f79009;
                        border: 1px solid #f79009;
                        border-radius: 6px;
                        padding: 8px 12px;
                        font-size: 13px;
                        font-weight: 500;
                    """)

                    self.alerts_layout.addWidget(
                        lbl
                    )

        # ---------------------------------------------------------
        # ALERTES STOCK FAIBLE
        # ---------------------------------------------------------

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
                    color: #f79009;
                    border: 1px solid #f79009;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                    font-weight: 500;
                """)

                self.alerts_layout.addWidget(
                    lbl
                )

        # ---------------------------------------------------------
        # AUCUNE ALERTE
        # ---------------------------------------------------------

        if not alerts_found:

            no_alert = QLabel(
                "✅ Aucune alerte pour le moment."
            )

            no_alert.setStyleSheet("""
                color: #027a48;
                background: #ecfdf3;
                border: 1px solid #12b76a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 500;
            """)

            self.alerts_layout.addWidget(
                no_alert
            )