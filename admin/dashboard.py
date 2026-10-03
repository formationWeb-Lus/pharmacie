from __future__ import annotations

import importlib
import inspect

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QSizePolicy,
    QScrollArea,
    QComboBox,
)

from database.database import SessionLocal
from database.models import (
    Product,
    ProductBatch,
    Sale,
    SaleItem,
    Expense,
)


# ============================================================
# COULEURS
# ============================================================

BG = "#F1F5F9"

SIDEBAR = "#0F3D3E"
SIDEBAR_DARK = "#0B2F30"

PRIMARY = "#14B8A6"
PRIMARY_DARK = "#0F766E"

WHITE = "#FFFFFF"

TEXT = "#0F172A"
TEXT_LIGHT = "#64748B"

BORDER = "#E2E8F0"

SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
INFO = "#2563EB"

EXPENSE_COLOR = "#9333EA"
EXPENSE_LIGHT = "#F3E8FF"


# ============================================================
# OUTILS
# ============================================================

def safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def money(value: Any) -> str:
    try:
        number = float(value or 0)
        return f"{number:,.0f} CDF".replace(",", " ")
    except Exception:
        return "0 CDF"


# ============================================================
# CARTE STATISTIQUE
# ============================================================

class StatCard(QFrame):

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str,
        icon: str,
        accent: str,
    ):
        super().__init__()

        self.setObjectName("statCard")
        self.setMinimumHeight(155)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        layout.setSpacing(8)

        # ----------------------------------------------------
        # TITRE + ICONE
        # ----------------------------------------------------

        top = QHBoxLayout()
        top.setSpacing(10)

        title_label = QLabel(title)

        title_label.setObjectName("statTitle")
        title_label.setWordWrap(True)

        title_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        icon_label = QLabel(icon)

        icon_label.setObjectName("statIcon")
        icon_label.setAlignment(Qt.AlignCenter)

        icon_label.setFixedSize(
            42,
            42,
        )

        top.addWidget(
            title_label,
            1,
        )

        top.addWidget(
            icon_label,
            0,
            Qt.AlignRight,
        )

        layout.addLayout(top)

        # ----------------------------------------------------
        # VALEUR
        # ----------------------------------------------------

        value_label = QLabel(str(value))

        value_label.setObjectName("statValue")
        value_label.setWordWrap(True)
        value_label.setMinimumHeight(40)

        value_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout.addWidget(value_label)

        # ----------------------------------------------------
        # SOUS-TITRE
        # ----------------------------------------------------

        subtitle_label = QLabel(subtitle)

        subtitle_label.setObjectName("statSubtitle")
        subtitle_label.setWordWrap(True)

        subtitle_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout.addWidget(subtitle_label)

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}

            QFrame#statCard:hover {{
                border: 1px solid {accent};
            }}

            QLabel#statTitle {{
                color: {TEXT_LIGHT};
                font-size: 13px;
                font-weight: 700;
            }}

            QLabel#statValue {{
                color: {TEXT};
                font-size: 25px;
                font-weight: 900;
                padding-top: 2px;
                padding-bottom: 2px;
            }}

            QLabel#statSubtitle {{
                color: {TEXT_LIGHT};
                font-size: 11px;
            }}

            QLabel#statIcon {{
                background: {accent};
                color: white;
                border-radius: 21px;
                font-size: 18px;
                font-weight: 900;
            }}
            """
        )


# ============================================================
# CARTE ALERTE
# ============================================================

class AlertCard(QFrame):

    def __init__(
        self,
        title: str,
        value: str,
        description: str,
        accent: str,
    ):
        super().__init__()

        self.setObjectName("alertCard")

        self.setMinimumHeight(110)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )

        layout.setSpacing(5)

        top = QHBoxLayout()

        title_label = QLabel(title)

        title_label.setStyleSheet(
            f"""
            color: {TEXT_LIGHT};
            font-size: 12px;
            font-weight: 700;
            """
        )

        value_label = QLabel(value)

        value_label.setStyleSheet(
            f"""
            color: {accent};
            font-size: 25px;
            font-weight: 900;
            """
        )

        top.addWidget(
            title_label,
            1,
        )

        top.addWidget(value_label)

        description_label = QLabel(description)

        description_label.setWordWrap(True)

        description_label.setStyleSheet(
            f"""
            color: {TEXT_LIGHT};
            font-size: 11px;
            """
        )

        layout.addLayout(top)
        layout.addWidget(description_label)

        self.setStyleSheet(
            f"""
            QFrame#alertCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-left: 4px solid {accent};
                border-radius: 13px;
            }}
            """
        )


# ============================================================
# DASHBOARD STATISTIQUES
# ============================================================

class DashboardOverview(QWidget):

    def __init__(
        self,
        current_user=None,
    ):
        super().__init__()

        self.current_user = current_user

        self.selected_period = "today"

        self.period_start: date | None = None
        self.period_end: date | None = None

        self.setObjectName(
            "dashboardOverview"
        )

        self.build_ui()

        self.update_period()

    # ========================================================
    # INTERFACE
    # ========================================================

    def build_ui(self):

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer_layout.setSpacing(0)

        # ====================================================
        # SCROLL
        # ====================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        outer_layout.addWidget(
            self.scroll
        )

        # ====================================================
        # CONTENU
        # ====================================================

        content = QWidget()

        content.setObjectName(
            "dashboardContent"
        )

        self.scroll.setWidget(content)

        main_layout = QVBoxLayout(content)

        main_layout.setContentsMargins(
            30,
            28,
            30,
            40,
        )

        main_layout.setSpacing(24)

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        header.setSpacing(20)

        title_container = QVBoxLayout()

        title_container.setSpacing(5)

        title = QLabel(
            "Tableau de bord"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Vue générale de votre pharmacie et de votre activité"
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(True)

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header.addLayout(
            title_container,
            1,
        )

        # ====================================================
        # FILTRE PERIODE
        # ====================================================

        period_container = QVBoxLayout()

        period_container.setSpacing(5)

        period_label = QLabel(
            "Période"
        )

        period_label.setObjectName(
            "periodLabel"
        )

        self.period_combo = QComboBox()

        self.period_combo.setObjectName(
            "periodCombo"
        )

        self.period_combo.addItem(
            "Aujourd'hui",
            "today",
        )

        self.period_combo.addItem(
            "Hier",
            "yesterday",
        )

        self.period_combo.addItem(
            "7 derniers jours",
            "last_7_days",
        )

        self.period_combo.addItem(
            "30 derniers jours",
            "last_30_days",
        )

        self.period_combo.addItem(
            "Mois en cours",
            "current_month",
        )

        self.period_combo.addItem(
            "Mois passé",
            "previous_month",
        )

        self.period_combo.addItem(
            "Année en cours",
            "current_year",
        )

        self.period_combo.addItem(
            "Année passée",
            "previous_year",
        )

        self.period_combo.addItem(
            "Toutes les données",
            "all",
        )

        self.period_combo.currentIndexChanged.connect(
            self.on_period_changed
        )

        period_container.addWidget(
            period_label
        )

        period_container.addWidget(
            self.period_combo
        )

        header.addLayout(
            period_container
        )

        # ====================================================
        # BOUTON ACTUALISER
        # ====================================================

        refresh_button = QPushButton(
            "↻  Actualiser"
        )

        refresh_button.setObjectName(
            "refreshButton"
        )

        refresh_button.setCursor(
            Qt.PointingHandCursor
        )

        refresh_button.clicked.connect(
            self.load_data
        )

        header.addWidget(
            refresh_button,
            0,
            Qt.AlignBottom,
        )

        main_layout.addLayout(header)

        # ====================================================
        # PERIODE ACTIVE
        # ====================================================

        self.period_info = QLabel()

        self.period_info.setObjectName(
            "periodInfo"
        )

        self.period_info.setWordWrap(True)

        main_layout.addWidget(
            self.period_info
        )

        # ====================================================
        # STOCK
        # ====================================================

        stock_title = QLabel("Stock")

        stock_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(stock_title)

        self.stock_grid = QGridLayout()

        self.stock_grid.setHorizontalSpacing(18)
        self.stock_grid.setVerticalSpacing(18)

        main_layout.addLayout(
            self.stock_grid
        )

        # ====================================================
        # VENTES
        # ====================================================

        sales_title = QLabel("Ventes")

        sales_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            sales_title
        )

        self.sales_grid = QGridLayout()

        self.sales_grid.setHorizontalSpacing(18)
        self.sales_grid.setVerticalSpacing(18)

        main_layout.addLayout(
            self.sales_grid
        )

        # ====================================================
        # DEPENSES
        # ====================================================

        expenses_title = QLabel("Dépenses")

        expenses_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            expenses_title
        )

        self.expenses_grid = QGridLayout()

        self.expenses_grid.setHorizontalSpacing(18)
        self.expenses_grid.setVerticalSpacing(18)

        main_layout.addLayout(
            self.expenses_grid
        )

        # ====================================================
        # RESULTAT
        # ====================================================

        result_title = QLabel(
            "Situation financière"
        )

        result_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            result_title
        )

        self.result_grid = QGridLayout()

        self.result_grid.setHorizontalSpacing(18)
        self.result_grid.setVerticalSpacing(18)

        main_layout.addLayout(
            self.result_grid
        )

        # ====================================================
        # ALERTES
        # ====================================================

        alerts_title = QLabel("Alertes")

        alerts_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            alerts_title
        )

        self.alerts_grid = QGridLayout()

        self.alerts_grid.setHorizontalSpacing(18)
        self.alerts_grid.setVerticalSpacing(18)

        main_layout.addLayout(
            self.alerts_grid
        )

        # ====================================================
        # VENTES DE LA PERIODE
        # ====================================================

        recent_title = QLabel(
            "Ventes de la période"
        )

        recent_title.setObjectName(
            "sectionTitle"
        )

        main_layout.addWidget(
            recent_title
        )

        table_card = QFrame()

        table_card.setObjectName(
            "tableCard"
        )

        table_card.setMinimumHeight(
            330
        )

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        self.sales_table = QTableWidget()

        self.sales_table.setColumnCount(6)

        self.sales_table.setHorizontalHeaderLabels(
            [
                "Facture",
                "Client",
                "Montant",
                "Paiement",
                "Date",
                "Articles",
            ]
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.sales_table.verticalHeader().setVisible(False)

        self.sales_table.setAlternatingRowColors(True)

        self.sales_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.sales_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.sales_table.setMinimumHeight(280)

        table_layout.addWidget(
            self.sales_table
        )

        main_layout.addWidget(
            table_card
        )

        main_layout.addSpacing(30)

        # ====================================================
        # STYLE
        # ====================================================

        self.setStyleSheet(
            f"""
            QWidget#dashboardOverview {{
                background: {BG};
            }}

            QWidget#dashboardContent {{
                background: {BG};
            }}

            QLabel#pageTitle {{
                color: {TEXT};
                font-size: 28px;
                font-weight: 900;
            }}

            QLabel#pageSubtitle {{
                color: {TEXT_LIGHT};
                font-size: 13px;
            }}

            QLabel#sectionTitle {{
                color: {TEXT};
                font-size: 18px;
                font-weight: 850;
                padding-top: 5px;
                padding-bottom: 2px;
            }}

            QLabel#periodLabel {{
                color: {TEXT_LIGHT};
                font-size: 11px;
                font-weight: 800;
            }}

            QLabel#periodInfo {{
                background: #ECFEFF;
                color: {PRIMARY_DARK};
                border: 1px solid #99F6E4;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: 700;
            }}

            QComboBox#periodCombo {{
                background: white;
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 9px;
                padding: 10px 35px 10px 12px;
                min-width: 175px;
                font-size: 12px;
                font-weight: 700;
            }}

            QComboBox#periodCombo:hover {{
                border: 1px solid {PRIMARY};
            }}

            QComboBox#periodCombo:focus {{
                border: 1px solid {PRIMARY};
            }}

            QComboBox#periodCombo QAbstractItemView {{
                background: white;
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: #CCFBF1;
                selection-color: {TEXT};
                padding: 5px;
            }}

            QPushButton#refreshButton {{
                background: {PRIMARY};
                color: white;
                border: none;
                border-radius: 9px;
                padding: 12px 20px;
                font-size: 12px;
                font-weight: 800;
            }}

            QPushButton#refreshButton:hover {{
                background: {PRIMARY_DARK};
            }}

            QFrame#tableCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 15px;
            }}

            QTableWidget {{
                background: white;
                border: none;
                gridline-color: {BORDER};
                color: {TEXT};
                font-size: 12px;
                selection-background-color: #CCFBF1;
                selection-color: {TEXT};
            }}

            QTableWidget::item {{
                padding: 8px;
            }}

            QHeaderView::section {{
                background: #F8FAFC;
                color: {TEXT_LIGHT};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 12px;
                font-weight: 800;
            }}

            QScrollBar:vertical {{
                background: #E2E8F0;
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical {{
                background: #94A3B8;
                min-height: 40px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {PRIMARY};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

    # ========================================================
    # CHANGEMENT DE PERIODE
    # ========================================================

    def on_period_changed(self):

        self.selected_period = (
            self.period_combo.currentData()
        )

        self.update_period()

    # ========================================================
    # CALCUL DE LA PERIODE
    # ========================================================

    def update_period(self):

        today = date.today()

        period = self.selected_period

        # ----------------------------------------------------
        # AUJOURD'HUI
        # ----------------------------------------------------

        if period == "today":

            start = today
            end = today

            label = (
                f"Aujourd'hui — "
                f"{today.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # HIER
        # ----------------------------------------------------

        elif period == "yesterday":

            yesterday = today - timedelta(days=1)

            start = yesterday
            end = yesterday

            label = (
                f"Hier — "
                f"{yesterday.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # 7 DERNIERS JOURS
        # ----------------------------------------------------

        elif period == "last_7_days":

            start = today - timedelta(days=6)
            end = today

            label = (
                f"7 derniers jours — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # 30 DERNIERS JOURS
        # ----------------------------------------------------

        elif period == "last_30_days":

            start = today - timedelta(days=29)
            end = today

            label = (
                f"30 derniers jours — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # MOIS COURANT
        # ----------------------------------------------------

        elif period == "current_month":

            start = date(
                today.year,
                today.month,
                1,
            )

            end = today

            label = (
                f"Mois en cours — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # MOIS PASSE
        # ----------------------------------------------------

        elif period == "previous_month":

            first_current = date(
                today.year,
                today.month,
                1,
            )

            last_previous = (
                first_current
                - timedelta(days=1)
            )

            start = date(
                last_previous.year,
                last_previous.month,
                1,
            )

            end = last_previous

            label = (
                f"Mois passé — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # ANNEE COURANTE
        # ----------------------------------------------------

        elif period == "current_year":

            start = date(
                today.year,
                1,
                1,
            )

            end = today

            label = (
                f"Année en cours — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # ANNEE PASSEE
        # ----------------------------------------------------

        elif period == "previous_year":

            start = date(
                today.year - 1,
                1,
                1,
            )

            end = date(
                today.year - 1,
                12,
                31,
            )

            label = (
                f"Année passée — "
                f"{start.strftime('%d/%m/%Y')} "
                f"au "
                f"{end.strftime('%d/%m/%Y')}"
            )

        # ----------------------------------------------------
        # TOUT
        # ----------------------------------------------------

        else:

            start = None
            end = None

            label = (
                "Toutes les données enregistrées"
            )

        self.period_start = start
        self.period_end = end

        self.period_info.setText(
            f"📅  Période sélectionnée : {label}"
        )

        self.load_data()

    # ========================================================
    # VERIFIER SI UNE DATE EST DANS LA PERIODE
    # ========================================================

    def date_in_period(
        self,
        value,
    ) -> bool:

        if value is None:
            return False

        if isinstance(
            value,
            datetime,
        ):

            value_date = value.date()

        elif isinstance(
            value,
            date,
        ):

            value_date = value

        else:

            return False

        if self.period_start is None:
            return True

        if value_date < self.period_start:
            return False

        if (
            self.period_end is not None
            and value_date > self.period_end
        ):

            return False

        return True

    # ========================================================
    # NETTOYAGE
    # ========================================================

    def clear_grid(
        self,
        grid,
    ):

        while grid.count():

            item = grid.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

    # ========================================================
    # CHARGEMENT DES DONNEES
    # ========================================================

    def load_data(self):

        if not hasattr(
            self,
            "stock_grid",
        ):

            return

        self.clear_grid(
            self.stock_grid
        )

        self.clear_grid(
            self.sales_grid
        )

        self.clear_grid(
            self.expenses_grid
        )

        self.clear_grid(
            self.result_grid
        )

        self.clear_grid(
            self.alerts_grid
        )

        db = SessionLocal()

        try:

            # =================================================
            # DONNEES GENERALES
            # =================================================

            products = (
                db.query(Product)
                .all()
            )

            batches = (
                db.query(ProductBatch)
                .all()
            )

            all_sales = (
                db.query(Sale)
                .all()
            )

            all_expenses = (
                db.query(Expense)
                .all()
            )

            # =================================================
            # FILTRAGE DES VENTES
            # =================================================

            sales = []

            for sale in all_sales:

                sale_date = self.get_sale_date(
                    sale
                )

                if not sale_date:
                    continue

                if self.date_in_period(
                    sale_date
                ):

                    sales.append(
                        sale
                    )

            # =================================================
            # FILTRAGE DES DEPENSES
            # =================================================

            expenses = []

            for expense in all_expenses:

                expense_date = (
                    self.get_expense_date(
                        expense
                    )
                )

                if not expense_date:
                    continue

                if self.date_in_period(
                    expense_date
                ):

                    expenses.append(
                        expense
                    )

            # =================================================
            # STOCK
            #
            # Le stock est un état actuel.
            # Il ne dépend donc pas du filtre de période.
            # =================================================

            total_products = len(products)

            total_stock = 0

            stock_value = 0

            sale_value = 0

            for product in products:

                stock = self.get_product_stock(
                    product,
                    batches,
                )

                total_stock += stock

                purchase_price = safe_float(
                    getattr(
                        product,
                        "purchase_price",
                        0,
                    )
                )

                selling_price = safe_float(
                    getattr(
                        product,
                        "price",
                        0,
                    )
                )

                stock_value += (
                    stock
                    * purchase_price
                )

                sale_value += (
                    stock
                    * selling_price
                )

            self.add_grid_card(
                self.stock_grid,
                StatCard(
                    "Produits enregistrés",
                    f"{total_products:,}".replace(
                        ",",
                        " ",
                    ),
                    "Nombre total de produits",
                    "P",
                    PRIMARY,
                ),
                0,
            )

            self.add_grid_card(
                self.stock_grid,
                StatCard(
                    "Stock total",
                    f"{total_stock:,}".replace(
                        ",",
                        " ",
                    ),
                    "Unités actuellement disponibles",
                    "S",
                    INFO,
                ),
                1,
            )

            self.add_grid_card(
                self.stock_grid,
                StatCard(
                    "Valeur du stock",
                    money(stock_value),
                    "Valeur actuelle au prix d'achat",
                    "₣",
                    WARNING,
                ),
                2,
            )

            self.add_grid_card(
                self.stock_grid,
                StatCard(
                    "Valeur de vente",
                    money(sale_value),
                    "Valeur potentielle actuelle",
                    "₣",
                    SUCCESS,
                ),
                3,
            )

            # =================================================
            # VENTES DE LA PERIODE
            # =================================================

            sales_amount = sum(
                self.get_sale_total(sale)
                for sale in sales
            )

            sales_count = len(sales)

            # =================================================
            # DEPENSES DE LA PERIODE
            # =================================================

            expense_amount = sum(
                self.get_expense_amount(
                    expense
                )
                for expense in expenses
            )

            expense_count = len(expenses)

            # =================================================
            # VENTES
            # =================================================

            period_name = (
                self.get_period_short_name()
            )

            self.add_grid_card(
                self.sales_grid,
                StatCard(
                    "Nombre de ventes",
                    f"{sales_count:,}".replace(
                        ",",
                        " ",
                    ),
                    f"Transactions — {period_name}",
                    "V",
                    PRIMARY,
                ),
                0,
            )

            self.add_grid_card(
                self.sales_grid,
                StatCard(
                    "Chiffre d'affaires",
                    money(sales_amount),
                    f"Ventes encaissées — {period_name}",
                    "₣",
                    SUCCESS,
                ),
                1,
            )

            # -------------------------------------------------
            # PANIER MOYEN
            # -------------------------------------------------

            average_sale = (
                sales_amount / sales_count
                if sales_count > 0
                else 0
            )

            self.add_grid_card(
                self.sales_grid,
                StatCard(
                    "Vente moyenne",
                    money(average_sale),
                    f"Montant moyen par vente — {period_name}",
                    "M",
                    INFO,
                ),
                2,
            )

            # -------------------------------------------------
            # NOMBRE D'ARTICLES
            # -------------------------------------------------

            total_items = 0

            for sale in sales:

                total_items += (
                    self.get_sale_items_count(
                        db,
                        sale,
                    )
                )

            self.add_grid_card(
                self.sales_grid,
                StatCard(
                    "Articles vendus",
                    f"{total_items:,}".replace(
                        ",",
                        " ",
                    ),
                    f"Articles vendus — {period_name}",
                    "A",
                    WARNING,
                ),
                3,
            )

            # =================================================
            # DEPENSES
            # =================================================

            self.add_grid_card(
                self.expenses_grid,
                StatCard(
                    "Total des dépenses",
                    money(expense_amount),
                    f"Dépenses — {period_name}",
                    "D",
                    EXPENSE_COLOR,
                ),
                0,
            )

            self.add_grid_card(
                self.expenses_grid,
                StatCard(
                    "Nombre de dépenses",
                    str(expense_count),
                    f"Enregistrements — {period_name}",
                    "N",
                    INFO,
                ),
                1,
            )

            # -------------------------------------------------
            # DEPENSE MOYENNE
            # -------------------------------------------------

            average_expense = (
                expense_amount / expense_count
                if expense_count > 0
                else 0
            )

            self.add_grid_card(
                self.expenses_grid,
                StatCard(
                    "Dépense moyenne",
                    money(average_expense),
                    f"Moyenne par dépense — {period_name}",
                    "M",
                    WARNING,
                ),
                2,
            )

            # -------------------------------------------------
            # SOLDE
            # -------------------------------------------------

            self.add_grid_card(
                self.expenses_grid,
                StatCard(
                    "Solde",
                    money(
                        sales_amount
                        - expense_amount
                    ),
                    "Ventes - dépenses",
                    "S",
                    (
                        SUCCESS
                        if sales_amount
                        - expense_amount
                        >= 0
                        else DANGER
                    ),
                ),
                3,
            )

            # =================================================
            # SITUATION FINANCIERE
            # =================================================

            result = (
                sales_amount
                - expense_amount
            )

            self.add_grid_card(
                self.result_grid,
                StatCard(
                    "Chiffre d'affaires",
                    money(sales_amount),
                    f"Total des ventes — {period_name}",
                    "₣",
                    SUCCESS,
                ),
                0,
            )

            self.add_grid_card(
                self.result_grid,
                StatCard(
                    "Dépenses",
                    money(expense_amount),
                    f"Total des dépenses — {period_name}",
                    "₣",
                    EXPENSE_COLOR,
                ),
                1,
            )

            self.add_grid_card(
                self.result_grid,
                StatCard(
                    "Résultat",
                    money(result),
                    "Chiffre d'affaires - dépenses",
                    "R",
                    (
                        SUCCESS
                        if result >= 0
                        else DANGER
                    ),
                ),
                2,
            )

            margin = (
                (result / sales_amount) * 100
                if sales_amount > 0
                else 0
            )

            self.add_grid_card(
                self.result_grid,
                StatCard(
                    "Marge après dépenses",
                    f"{margin:.1f} %",
                    f"Pourcentage — {period_name}",
                    "%",
                    (
                        SUCCESS
                        if margin >= 0
                        else DANGER
                    ),
                ),
                3,
            )

            # =================================================
            # ALERTES
            #
            # Ces informations restent actuelles.
            # =================================================

            low_stock_count = 0
            expiring_count = 0
            expired_count = 0

            today_date = date.today()

            limit_date = (
                today_date
                + timedelta(days=30)
            )

            for product in products:

                stock = self.get_product_stock(
                    product,
                    batches,
                )

                min_quantity = safe_int(
                    getattr(
                        product,
                        "min_quantity",
                        0,
                    )
                )

                if (
                    min_quantity > 0
                    and stock <= min_quantity
                ):

                    low_stock_count += 1

            for batch in batches:

                expiry = self.get_expiry_date(
                    batch
                )

                if not expiry:
                    continue

                if expiry < today_date:

                    expired_count += 1

                elif expiry <= limit_date:

                    expiring_count += 1

            self.add_grid_card(
                self.alerts_grid,
                AlertCard(
                    "Stock faible",
                    str(low_stock_count),
                    "Produits actuellement à réapprovisionner",
                    WARNING,
                ),
                0,
            )

            self.add_grid_card(
                self.alerts_grid,
                AlertCard(
                    "Expire bientôt",
                    str(expiring_count),
                    "Produits expirant dans les 30 prochains jours",
                    INFO,
                ),
                1,
            )

            self.add_grid_card(
                self.alerts_grid,
                AlertCard(
                    "Produits expirés",
                    str(expired_count),
                    "Produits actuellement expirés",
                    DANGER,
                ),
                2,
            )

            # =================================================
            # VENTES DE LA PERIODE
            # =================================================

            recent_sales = sorted(
                sales,
                key=lambda sale:
                self.get_sale_date(sale)
                or datetime.min,
                reverse=True,
            )[:20]

            self.sales_table.setRowCount(
                len(recent_sales)
            )

            for row, sale in enumerate(
                recent_sales
            ):

                invoice = (
                    getattr(
                        sale,
                        "invoice_number",
                        None,
                    )
                    or f"V-{getattr(sale, 'id', '')}"
                )

                customer = (
                    getattr(
                        sale,
                        "client_name",
                        None,
                    )
                    or "Client comptoir"
                )

                amount = self.get_sale_total(
                    sale
                )

                payment = (
                    getattr(
                        sale,
                        "payment_method",
                        None,
                    )
                    or "—"
                )

                sale_date = self.get_sale_date(
                    sale
                )

                date_text = (
                    sale_date.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    if sale_date
                    else "—"
                )

                article_count = (
                    self.get_sale_items_count(
                        db,
                        sale,
                    )
                )

                values = [
                    str(invoice),
                    str(customer),
                    money(amount),
                    str(payment),
                    date_text,
                    str(article_count),
                ]

                for column, value in enumerate(
                    values
                ):

                    item = QTableWidgetItem(
                        value
                    )

                    item.setTextAlignment(
                        Qt.AlignVCenter
                        | Qt.AlignLeft
                    )

                    self.sales_table.setItem(
                        row,
                        column,
                        item,
                    )

        except Exception as error:

            print(
                "\n"
                + "=" * 70
            )

            print(
                "ERREUR CHARGEMENT DASHBOARD"
            )

            print(
                str(error)
            )

            print(
                "=" * 70
            )

            self.sales_table.setRowCount(0)

        finally:

            db.close()

    # ========================================================
    # NOM COURT DE LA PERIODE
    # ========================================================

    def get_period_short_name(self):

        names = {
            "today": "aujourd'hui",
            "yesterday": "hier",
            "last_7_days": "7 derniers jours",
            "last_30_days": "30 derniers jours",
            "current_month": "mois en cours",
            "previous_month": "mois passé",
            "current_year": "année en cours",
            "previous_year": "année passée",
            "all": "toute la période",
        }

        return names.get(
            self.selected_period,
            "période sélectionnée",
        )

    # ========================================================
    # MONTANT VENTE
    # ========================================================

    def get_sale_total(
        self,
        sale,
    ) -> float:

        value = getattr(
            sale,
            "total",
            None,
        )

        if value is not None:
            return safe_float(value)

        value = getattr(
            sale,
            "total_amount",
            None,
        )

        return safe_float(value)

    # ========================================================
    # MONTANT DEPENSE
    # ========================================================

    def get_expense_amount(
        self,
        expense,
    ) -> float:

        return safe_float(
            getattr(
                expense,
                "amount",
                0,
            )
        )

    # ========================================================
    # DATE DEPENSE
    # ========================================================

    def get_expense_date(
        self,
        expense,
    ):

        value = getattr(
            expense,
            "expense_date",
            None,
        )

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

        if isinstance(
            value,
            str,
        ):

            for fmt in (
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
            ):

                try:

                    return datetime.strptime(
                        value,
                        fmt,
                    ).date()

                except Exception:

                    continue

        return None

    # ========================================================
    # AJOUT CARTE
    # ========================================================

    def add_grid_card(
        self,
        grid,
        widget,
        index,
    ):

        row = index // 2
        column = index % 2

        grid.addWidget(
            widget,
            row,
            column,
        )

        grid.setColumnStretch(
            column,
            1,
        )

    # ========================================================
    # STOCK PRODUIT
    # ========================================================

    def get_product_stock(
        self,
        product,
        batches,
    ):

        product_id = getattr(
            product,
            "id",
            None,
        )

        stock = 0

        product_stock = getattr(
            product,
            "stock_units",
            None,
        )

        if product_stock is not None:

            try:

                stock = int(
                    product_stock
                )

            except Exception:

                stock = 0

        if stock == 0:

            product_quantity = getattr(
                product,
                "quantity",
                None,
            )

            if product_quantity is not None:

                try:

                    stock = int(
                        product_quantity
                    )

                except Exception:

                    pass

        batch_stock = 0

        for batch in batches:

            batch_product_id = getattr(
                batch,
                "product_id",
                None,
            )

            if (
                batch_product_id
                != product_id
            ):
                continue

            quantity = getattr(
                batch,
                "stock_units",
                None,
            )

            if quantity is None:

                quantity = getattr(
                    batch,
                    "quantity",
                    0,
                )

            try:

                batch_stock += int(
                    quantity or 0
                )

            except Exception:

                pass

        if batch_stock > 0:

            return batch_stock

        return stock

    # ========================================================
    # DATE VENTE
    # ========================================================

    def get_sale_date(
        self,
        sale,
    ):

        for field in (
            "created_at",
            "sale_date",
            "date",
        ):

            value = getattr(
                sale,
                field,
                None,
            )

            if isinstance(
                value,
                datetime,
            ):

                return value

            if isinstance(
                value,
                date,
            ):

                return datetime.combine(
                    value,
                    datetime.min.time(),
                )

            if isinstance(
                value,
                str,
            ):

                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M",
                    "%d/%m/%Y",
                ]

                for fmt in formats:

                    try:

                        return datetime.strptime(
                            value,
                            fmt,
                        )

                    except Exception:

                        continue

        return None

    # ========================================================
    # DATE EXPIRATION
    # ========================================================

    def get_expiry_date(
        self,
        batch,
    ):

        value = getattr(
            batch,
            "expiry_date",
            None,
        )

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

        if isinstance(
            value,
            str,
        ):

            for fmt in (
                "%Y-%m-%d",
                "%d/%m/%Y",
            ):

                try:

                    return datetime.strptime(
                        value,
                        fmt,
                    ).date()

                except Exception:

                    continue

        return None

    # ========================================================
    # ARTICLES VENTE
    # ========================================================

    def get_sale_items_count(
        self,
        db,
        sale,
    ):

        try:

            items = (
                db.query(
                    SaleItem
                )
                .filter(
                    SaleItem.sale_id
                    == sale.id
                )
                .all()
            )

            return sum(
                safe_int(
                    getattr(
                        item,
                        "quantity",
                        0,
                    )
                )
                for item in items
            )

        except Exception:

            return 0


# ============================================================
# BOUTON MENU
# ============================================================

class MenuButton(QPushButton):

    def __init__(
        self,
        text,
        icon,
    ):

        super().__init__(
            f"{icon}   {text}"
        )

        self.setCheckable(True)

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setMinimumHeight(48)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )


# ============================================================
# DASHBOARD ADMIN
# ============================================================

class DashboardPage(QWidget):

    def __init__(
        self,
        current_user=None,
        parent=None,
    ):

        super().__init__(parent)

        self.current_user = current_user

        self.pages = {}
        self.menu_buttons = {}

        self.setWindowTitle(
            "Pharmacie - Administration"
        )

        self.setMinimumSize(
            1150,
            700,
        )

        self.build_ui()

        self.open_dashboard()

    # ========================================================
    # INTERFACE
    # ========================================================

    def build_ui(self):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(0)

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(255)

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            18,
            22,
            18,
            20,
        )

        sidebar_layout.setSpacing(10)

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        logo = QLabel("PHARMACIE")

        logo.setObjectName("logo")

        subtitle = QLabel(
            "Administration"
        )

        subtitle.setObjectName(
            "logoSubtitle"
        )

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)

        sidebar_layout.addSpacing(20)

        # ----------------------------------------------------
        # UTILISATEUR
        # ----------------------------------------------------

        user_card = QFrame()

        user_card.setObjectName(
            "userCard"
        )

        user_layout = QVBoxLayout(
            user_card
        )

        user_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        user_name = self.get_user_value(
            "name",
            "Nom",
            "Administrateur",
        )

        user_role = self.get_user_value(
            "role",
            "Rôle",
            "ADMIN",
        )

        name_label = QLabel(
            str(user_name)
        )

        name_label.setObjectName(
            "userName"
        )

        role_label = QLabel(
            str(user_role).upper()
        )

        role_label.setObjectName(
            "userRole"
        )

        user_layout.addWidget(
            name_label
        )

        user_layout.addWidget(
            role_label
        )

        sidebar_layout.addWidget(
            user_card
        )

        sidebar_layout.addSpacing(18)

        menu_title = QLabel(
            "MENU PRINCIPAL"
        )

        menu_title.setObjectName(
            "menuTitle"
        )

        sidebar_layout.addWidget(
            menu_title
        )

        # ----------------------------------------------------
        # MENUS
        # ----------------------------------------------------

        self.add_menu_button(
            sidebar_layout,
            "dashboard",
            "Tableau de bord",
            "⌂",
        )

        self.add_menu_button(
            sidebar_layout,
            "products",
            "Produits",
            "▣",
        )

        self.add_menu_button(
            sidebar_layout,
            "stock",
            "Stock",
            "▤",
        )

        self.add_menu_button(
            sidebar_layout,
            "sales",
            "Ventes",
            "▰",
        )

        self.add_menu_button(
            sidebar_layout,
            "invoices",
            "Factures",
            "▥",
        )

        self.add_menu_button(
            sidebar_layout,
            "expenses",
            "Dépenses",
            "◆",
        )

        sidebar_layout.addStretch()

        # ----------------------------------------------------
        # DECONNEXION
        # ----------------------------------------------------

        logout = QPushButton(
            "↪   Déconnexion"
        )

        logout.setObjectName(
            "logoutButton"
        )

        logout.setCursor(
            Qt.PointingHandCursor
        )

        logout.clicked.connect(
            self.logout
        )

        sidebar_layout.addWidget(
            logout
        )

        # ====================================================
        # CONTENU
        # ====================================================

        content = QFrame()

        content.setObjectName(
            "contentContainer"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.stack = QStackedWidget()

        content_layout.addWidget(
            self.stack
        )

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            content,
            1,
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.setStyleSheet(
            f"""
            QWidget {{
                font-family: "Segoe UI";
            }}

            QFrame#sidebar {{
                background: {SIDEBAR};
            }}

            QLabel#logo {{
                color: white;
                font-size: 22px;
                font-weight: 900;
            }}

            QLabel#logoSubtitle {{
                color: #99F6E4;
                font-size: 11px;
                font-weight: 600;
            }}

            QFrame#userCard {{
                background: {SIDEBAR_DARK};
                border: 1px solid #1F5D5E;
                border-radius: 12px;
            }}

            QLabel#userName {{
                color: white;
                font-size: 14px;
                font-weight: 700;
            }}

            QLabel#userRole {{
                color: #5EEAD4;
                font-size: 10px;
                font-weight: 800;
            }}

            QLabel#menuTitle {{
                color: #7DD3D0;
                font-size: 10px;
                font-weight: 800;
                padding-left: 8px;
            }}

            QPushButton#menuButton {{
                background: transparent;
                color: #D1FAE5;
                border: none;
                border-radius: 10px;
                padding: 0 15px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }}

            QPushButton#menuButton:hover {{
                background: #145253;
                color: white;
            }}

            QPushButton#menuButton:checked {{
                background: {PRIMARY};
                color: white;
            }}

            QPushButton#logoutButton {{
                background: #153F40;
                color: #FCA5A5;
                border: none;
                border-radius: 10px;
                padding: 13px 15px;
                font-size: 13px;
                font-weight: 700;
                text-align: left;
            }}

            QPushButton#logoutButton:hover {{
                background: #7F1D1D;
                color: white;
            }}

            QFrame#contentContainer {{
                background: {BG};
            }}
            """
        )

    # ========================================================
    # BOUTON MENU
    # ========================================================

    def add_menu_button(
        self,
        layout,
        key,
        text,
        icon,
    ):

        button = MenuButton(
            text,
            icon,
        )

        button.setObjectName(
            "menuButton"
        )

        button.clicked.connect(
            lambda checked=False, k=key:
            self.navigate(k)
        )

        layout.addWidget(button)

        self.menu_buttons[key] = button

    # ========================================================
    # NAVIGATION
    # ========================================================

    def navigate(
        self,
        key,
    ):

        for name, button in self.menu_buttons.items():

            button.setChecked(
                name == key
            )

        if key == "dashboard":

            self.open_dashboard()

        elif key == "products":

            self.open_page(
                key,
                [
                    "admin.products"
                ],
                [
                    "ProductsPage",
                    "ProductPage",
                    "Products",
                    "ProductManager",
                ],
            )

        elif key == "stock":

            self.open_page(
                key,
                [
                    "admin.stock"
                ],
                [
                    "StockPage"
                ],
            )

        elif key == "sales":

            self.open_page(
                key,
                [
                    "admin.sales"
                ],
                [
                    "SalesPage"
                ],
            )

        elif key == "invoices":

            self.open_page(
                key,
                [
                    "ui.invoices",
                    "admin.invoices",
                    "invoices",
                ],
                [
                    "InvoicesPage",
                    "InvoicePage",
                ],
            )

        elif key == "expenses":

            self.open_page(
                key,
                [
                    "admin.expenses"
                ],
                [
                    "ExpensesPage"
                ],
            )

    # ========================================================
    # ACCUEIL
    # ========================================================

    def open_dashboard(self):

        for name, button in self.menu_buttons.items():

            button.setChecked(
                name == "dashboard"
            )

        if "dashboard" in self.pages:

            page = self.pages["dashboard"]

            self.stack.setCurrentWidget(
                page
            )

            if hasattr(
                page,
                "load_data",
            ):

                page.load_data()

            return

        page = DashboardOverview(
            self.current_user
        )

        self.pages["dashboard"] = page

        self.stack.addWidget(page)

        self.stack.setCurrentWidget(page)

    # ========================================================
    # OUVRIR PAGE
    # ========================================================

    def open_page(
        self,
        key,
        modules,
        preferred_names,
    ):

        if key in self.pages:

            page = self.pages[key]

            self.stack.setCurrentWidget(
                page
            )

            if hasattr(
                page,
                "load_statistics",
            ):

                try:
                    page.load_statistics()
                except Exception:
                    pass

            if (
                hasattr(
                    page,
                    "load_expenses",
                )
                and key == "expenses"
            ):

                try:
                    page.load_expenses()
                except Exception:
                    pass

            return

        try:

            module = None
            last_error = None

            for module_name in modules:

                try:

                    module = importlib.import_module(
                        module_name
                    )

                    break

                except Exception as error:

                    last_error = error

            if module is None:

                raise ImportError(
                    f"Impossible de charger {modules}: "
                    f"{last_error}"
                )

            page_class = self.find_page_class(
                module,
                preferred_names,
            )

            if page_class is None:

                raise ImportError(
                    f"Aucune page QWidget trouvée "
                    f"dans {module.__name__}"
                )

            page = self.create_page_instance(
                page_class
            )

            self.pages[key] = page

            self.stack.addWidget(page)

            self.stack.setCurrentWidget(page)

        except Exception as error:

            print(
                f"Erreur page {key}: {error}"
            )

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    f"Impossible d'ouvrir la page "
                    f"{key}.\n\n{error}"
                ),
            )

    # ========================================================
    # RECHERCHER CLASSE PAGE
    # ========================================================

    def find_page_class(
        self,
        module,
        preferred_names,
    ):

        for name in preferred_names:

            cls = getattr(
                module,
                name,
                None,
            )

            if (
                inspect.isclass(cls)
                and issubclass(
                    cls,
                    QWidget,
                )
                and cls is not QWidget
            ):

                return cls

        for name, cls in inspect.getmembers(
            module,
            inspect.isclass,
        ):

            if (
                cls.__module__
                == module.__name__
                and issubclass(
                    cls,
                    QWidget,
                )
                and cls is not QWidget
            ):

                return cls

        return None

    # ========================================================
    # CREER PAGE
    # ========================================================

    def create_page_instance(
        self,
        page_class,
    ):

        try:

            signature = inspect.signature(
                page_class.__init__
            )

            parameters = signature.parameters

            if (
                "current_user"
                in parameters
            ):

                return page_class(
                    current_user=self.current_user
                )

            for parameter in parameters.values():

                if (
                    parameter.kind
                    == inspect.Parameter.VAR_KEYWORD
                ):

                    return page_class(
                        current_user=self.current_user
                    )

            return page_class()

        except Exception as error:

            print(
                f"Erreur création page : {error}"
            )

            return page_class()

    # ========================================================
    # UTILISATEUR
    # ========================================================

    def get_user_value(
        self,
        attribute,
        dictionary_key,
        default,
    ):

        user = self.current_user

        if user is None:
            return default

        if isinstance(
            user,
            dict,
        ):

            return (
                user.get(attribute)
                or user.get(dictionary_key)
                or default
            )

        return (
            getattr(
                user,
                attribute,
                None,
            )
            or getattr(
                user,
                dictionary_key,
                None,
            )
            or default
        )

    # ========================================================
    # DECONNEXION
    # ========================================================

    def logout(self):

        answer = QMessageBox.question(
            self,
            "Déconnexion",
            "Voulez-vous vraiment vous déconnecter ?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.close()

        try:

            from ui.login import LoginWindow

            self.login_window = LoginWindow()

            self.login_window.showFullScreen()

        except Exception as error:

            print(
                "Erreur retour connexion:",
                error,
            )


# ============================================================
# TEST DIRECT
# ============================================================

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)

    window = DashboardPage(
        current_user={
            "name": "Administrateur",
            "phone": "0810946352",
            "role": "ADMIN",
        }
    )

    window.showMaximized()

    sys.exit(
        app.exec()
    )