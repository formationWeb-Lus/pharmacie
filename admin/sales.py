from datetime import datetime, date
from decimal import Decimal

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
    QTextEdit,
    QAbstractItemView,
)

from database.database import (
    SessionLocal,
    synchronize_product_stock,
)

from database.models import (
    Product,
    ProductBatch,
    Sale,
    SaleItem,
)


# ============================================================
# UTILITAIRES
# ============================================================

def format_money(value):
    """Formate un montant en argent."""
    try:
        value = float(value or 0)
        return f"{value:,.2f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00"


def format_number(value):
    """Formate une quantité."""
    try:
        value = float(value or 0)

        if value.is_integer():
            return f"{int(value):,}".replace(",", " ")

        return f"{value:,.2f}".replace(",", " ").replace(".", ",")

    except Exception:
        return "0"


def format_datetime(value):
    """Formate une date/heure."""
    if not value:
        return "-"

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    return str(value)


def normalize_payment_method(value):
    """Retourne un nom lisible pour le mode de paiement."""
    if not value:
        return "Non précisé"

    value = str(value).strip()

    mapping = {
        "cash": "Espèces",
        "especes": "Espèces",
        "espèces": "Espèces",
        "cash_payment": "Espèces",

        "mobile_money": "Mobile Money",
        "mobile money": "Mobile Money",

        "mpesa": "M-Pesa",
        "m-pesa": "M-Pesa",

        "airtel_money": "Airtel Money",
        "airtel money": "Airtel Money",

        "orange_money": "Orange Money",
        "orange money": "Orange Money",

        "card": "Carte",
        "carte": "Carte",

        "bank": "Banque",
        "banque": "Banque",

        "credit": "Crédit",
        "crédit": "Crédit",
    }

    return mapping.get(value.lower(), value)


# ============================================================
# PAGE DES VENTES
# ============================================================

class SalesPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SalesPage")

        self.setup_ui()
        self.apply_styles()
        self.load_sales()

    # ========================================================
    # INTERFACE
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(18)

        # ----------------------------------------------------
        # TITRE
        # ----------------------------------------------------

        title_layout = QHBoxLayout()

        title_block = QVBoxLayout()

        title = QLabel("Gestion des ventes")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Consultez l'historique des ventes, les paiements et les détails des transactions."
        )
        subtitle.setObjectName("pageSubtitle")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        title_layout.addLayout(title_block)
        title_layout.addStretch()

        refresh_button = QPushButton("↻ Actualiser")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setMinimumHeight(40)
        refresh_button.clicked.connect(self.load_sales)

        title_layout.addWidget(refresh_button)

        main_layout.addLayout(title_layout)

        # ----------------------------------------------------
        # STATISTIQUES
        # ----------------------------------------------------

        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)

        self.sales_count_card = self.create_stat_card(
            "Nombre de ventes",
            "0",
            "Ventes enregistrées"
        )

        self.total_revenue_card = self.create_stat_card(
            "Chiffre d'affaires",
            "0,00",
            "Montant total des ventes"
        )

        self.average_sale_card = self.create_stat_card(
            "Panier moyen",
            "0,00",
            "Montant moyen par vente"
        )

        self.today_revenue_card = self.create_stat_card(
            "Ventes aujourd'hui",
            "0,00",
            "Chiffre d'affaires du jour"
        )

        stats_layout.addWidget(self.sales_count_card, 0, 0)
        stats_layout.addWidget(self.total_revenue_card, 0, 1)
        stats_layout.addWidget(self.average_sale_card, 0, 2)
        stats_layout.addWidget(self.today_revenue_card, 0, 3)

        main_layout.addLayout(stats_layout)

        # ----------------------------------------------------
        # FILTRES
        # ----------------------------------------------------

        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")

        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 12, 15, 12)
        filter_layout.setSpacing(10)

        search_label = QLabel("Recherche :")
        search_label.setObjectName("filterLabel")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Facture ou nom du client..."
        )
        self.search_input.setMinimumHeight(38)
        self.search_input.textChanged.connect(self.load_sales)

        payment_label = QLabel("Paiement :")
        payment_label.setObjectName("filterLabel")

        self.payment_filter = QComboBox()
        self.payment_filter.setMinimumHeight(38)
        self.payment_filter.addItems([
            "Tous",
            "Espèces",
            "Mobile Money",
            "M-Pesa",
            "Airtel Money",
            "Orange Money",
            "Carte",
            "Banque",
            "Crédit",
        ])
        self.payment_filter.currentTextChanged.connect(
            self.load_sales
        )

        clear_button = QPushButton("Effacer")
        clear_button.setObjectName("secondaryButton")
        clear_button.setMinimumHeight(38)
        clear_button.clicked.connect(self.clear_filters)

        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input, 1)

        filter_layout.addWidget(payment_label)
        filter_layout.addWidget(self.payment_filter)

        filter_layout.addWidget(clear_button)

        main_layout.addWidget(filter_frame)

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        self.sales_table = QTableWidget()

        self.sales_table.setColumnCount(8)

        self.sales_table.setHorizontalHeaderLabels([
            "Facture",
            "Date",
            "Client",
            "Articles",
            "Total",
            "Paiement",
            "Détails",
            "Supprimer",
        ])

        self.sales_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.sales_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.sales_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.sales_table.verticalHeader().setVisible(False)

        self.sales_table.horizontalHeader().setStretchLastSection(False)

        self.sales_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            6,
            QHeaderView.ResizeToContents
        )

        self.sales_table.horizontalHeader().setSectionResizeMode(
            7,
            QHeaderView.ResizeToContents
        )

        self.sales_table.setAlternatingRowColors(True)

        main_layout.addWidget(self.sales_table, 1)

    # ========================================================
    # CARTE STATISTIQUE
    # ========================================================

    def create_stat_card(self, title, value, description):

        card = QFrame()
        card.setObjectName("statCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statValue")

        description_label = QLabel(description)
        description_label.setObjectName("statDescription")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(description_label)

        card.value_label = value_label

        return card

    # ========================================================
    # STYLES
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""
            QWidget#SalesPage {
                background-color: #f4f6f8;
                color: #08192d;
            }

            QLabel#pageTitle {
                color: #08192d;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #64748b;
                font-size: 13px;
            }

            QFrame#statCard {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }

            QLabel#statTitle {
                color: #64748b;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#statValue {
                color: #08192d;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#statDescription {
                color: #94a3b8;
                font-size: 11px;
            }

            QFrame#filterFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }

            QLabel#filterLabel {
                color: #334155;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 6px 10px;
                color: #08192d;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #facc15;
            }

            QPushButton {
                border-radius: 7px;
                padding: 7px 14px;
                font-weight: 600;
            }

            QPushButton#secondaryButton {
                background-color: #e2e8f0;
                color: #08192d;
                border: none;
            }

            QPushButton#secondaryButton:hover {
                background-color: #cbd5e1;
            }

            QPushButton#detailsButton {
                background-color: #08192d;
                color: white;
                border: none;
                padding: 6px 12px;
            }

            QPushButton#detailsButton:hover {
                background-color: #102d4d;
            }

            QPushButton#deleteButton {
                background-color: #fee2e2;
                color: #b91c1c;
                border: none;
                padding: 6px 12px;
            }

            QPushButton#deleteButton:hover {
                background-color: #fecaca;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                gridline-color: #e2e8f0;
                color: #08192d;
                selection-background-color: #fff7cc;
                selection-color: #08192d;
            }

            QTableWidget::item {
                padding: 7px;
            }

            QHeaderView::section {
                background-color: #08192d;
                color: white;
                padding: 9px;
                border: none;
                font-weight: 600;
            }

            QScrollBar:vertical {
                background: #f1f5f9;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 5px;
            }
        """)

    # ========================================================
    # EFFACER LES FILTRES
    # ========================================================

    def clear_filters(self):

        self.search_input.clear()
        self.payment_filter.setCurrentIndex(0)

        self.load_sales()

    # ========================================================
    # CHARGER LES VENTES
    # ========================================================

    def load_sales(self):

        session = SessionLocal()

        try:

            search = self.search_input.text().strip().lower()

            payment = self.payment_filter.currentText()

            query = session.query(Sale).order_by(
                Sale.created_at.desc()
            )

            sales = query.all()

            # -----------------------------------------------
            # FILTRE RECHERCHE
            # -----------------------------------------------

            filtered_sales = []

            for sale in sales:

                invoice = str(
                    sale.invoice_number or ""
                ).lower()

                client = str(
                    sale.client_name or ""
                ).lower()

                if search:

                    if (
                        search not in invoice
                        and search not in client
                    ):
                        continue

                # -------------------------------------------
                # FILTRE PAIEMENT
                # -------------------------------------------

                if payment != "Tous":

                    sale_payment = normalize_payment_method(
                        sale.payment_method
                    )

                    if sale_payment != payment:
                        continue

                filtered_sales.append(sale)

            # -----------------------------------------------
            # TABLE
            # -----------------------------------------------

            self.sales_table.setRowCount(
                len(filtered_sales)
            )

            for row, sale in enumerate(filtered_sales):

                # Facture
                self.set_table_item(
                    row,
                    0,
                    sale.invoice_number or "-"
                )

                # Date
                self.set_table_item(
                    row,
                    1,
                    format_datetime(
                        sale.created_at
                    )
                )

                # Client
                self.set_table_item(
                    row,
                    2,
                    sale.client_name or "Client comptoir"
                )

                # Articles
                article_count = len(
                    sale.items or []
                )

                self.set_table_item(
                    row,
                    3,
                    str(article_count),
                    alignment=Qt.AlignCenter
                )

                # Total
                total_item = QTableWidgetItem(
                    f"{format_money(sale.total)}"
                )

                total_item.setTextAlignment(
                    Qt.AlignRight | Qt.AlignVCenter
                )

                self.sales_table.setItem(
                    row,
                    4,
                    total_item
                )

                # Paiement
                self.set_table_item(
                    row,
                    5,
                    normalize_payment_method(
                        sale.payment_method
                    )
                )

                # Détails
                details_button = QPushButton(
                    "Voir"
                )

                details_button.setObjectName(
                    "detailsButton"
                )

                details_button.clicked.connect(
                    lambda checked=False,
                    sale_id=sale.id:
                    self.show_sale_details(sale_id)
                )

                self.sales_table.setCellWidget(
                    row,
                    6,
                    details_button
                )

                # Supprimer
                delete_button = QPushButton(
                    "Supprimer"
                )

                delete_button.setObjectName(
                    "deleteButton"
                )

                delete_button.clicked.connect(
                    lambda checked=False,
                    sale_id=sale.id:
                    self.delete_sale(sale_id)
                )

                self.sales_table.setCellWidget(
                    row,
                    7,
                    delete_button
                )

            # -----------------------------------------------
            # STATISTIQUES
            # -----------------------------------------------

            self.update_statistics(
                session,
                filtered_sales
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger les ventes.\n\n"
                    f"{error}"
                )
            )

        finally:

            session.close()

    # ========================================================
    # ITEM TABLE
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

        self.sales_table.setItem(
            row,
            column,
            item
        )

    # ========================================================
    # STATISTIQUES
    # ========================================================

    def update_statistics(
        self,
        session,
        filtered_sales
    ):

        sales_count = len(filtered_sales)

        total_revenue = sum(
            float(sale.total or 0)
            for sale in filtered_sales
        )

        average_sale = (
            total_revenue / sales_count
            if sales_count > 0
            else 0
        )

        today = date.today()

        today_revenue = 0

        for sale in filtered_sales:

            sale_date = sale.created_at

            if isinstance(
                sale_date,
                datetime
            ):

                if sale_date.date() == today:

                    today_revenue += float(
                        sale.total or 0
                    )

            elif isinstance(
                sale_date,
                date
            ):

                if sale_date == today:

                    today_revenue += float(
                        sale.total or 0
                    )

        self.sales_count_card.value_label.setText(
            format_number(sales_count)
        )

        self.total_revenue_card.value_label.setText(
            f"{format_money(total_revenue)}"
        )

        self.average_sale_card.value_label.setText(
            f"{format_money(average_sale)}"
        )

        self.today_revenue_card.value_label.setText(
            f"{format_money(today_revenue)}"
        )

    # ========================================================
    # DÉTAILS D'UNE VENTE
    # ========================================================

    def show_sale_details(self, sale_id):

        session = SessionLocal()

        try:

            sale = (
                session.query(Sale)
                .filter(Sale.id == sale_id)
                .first()
            )

            if not sale:

                QMessageBox.warning(
                    self,
                    "Vente introuvable",
                    "Cette vente n'existe plus."
                )

                return

            dialog = SaleDetailsDialog(
                sale,
                self
            )

            dialog.exec()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible d'afficher "
                    "les détails de la vente.\n\n"
                    f"{error}"
                )
            )

        finally:

            session.close()

    # ========================================================
    # SUPPRESSION D'UNE VENTE
    # ========================================================

    def delete_sale(self, sale_id):

        session = SessionLocal()

        try:

            sale = (
                session.query(Sale)
                .filter(Sale.id == sale_id)
                .first()
            )

            if not sale:

                QMessageBox.warning(
                    self,
                    "Vente introuvable",
                    "Cette vente n'existe plus."
                )

                return

            invoice = (
                sale.invoice_number
                or f"Vente #{sale.id}"
            )

            total = float(
                sale.total or 0
            )

            confirmation = QMessageBox.question(
                self,
                "Supprimer la vente",
                (
                    f"Voulez-vous vraiment supprimer "
                    f"la vente {invoice} ?\n\n"
                    f"Montant : {format_money(total)}\n\n"
                    "Le stock vendu sera automatiquement "
                    "restauré."
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if confirmation != QMessageBox.Yes:

                return

            # ------------------------------------------------
            # IMPORTANT :
            # On récupère les lignes AVANT de supprimer
            # la vente.
            # ------------------------------------------------

            sale_items = list(
                sale.items or []
            )

            restored_products = set()

            # ------------------------------------------------
            # RESTAURATION DU STOCK
            # ------------------------------------------------

            for item in sale_items:

                product = (
                    session.query(Product)
                    .filter(
                        Product.id == item.product_id
                    )
                    .first()
                )

                if not product:
                    continue

                # Quantité en unités de base.
                stock_units = item.stock_units

                if stock_units is None:

                    # Sécurité si ancienne vente
                    # sans stock_units enregistré.
                    stock_units = self.convert_sale_quantity_to_base_units(
                        product,
                        item
                    )

                try:
                    stock_units = float(
                        stock_units or 0
                    )
                except Exception:
                    stock_units = 0

                if stock_units <= 0:
                    continue

                # ------------------------------------------------
                # SI LA VENTE EST LIÉE À UN LOT :
                # restaurer dans le même lot.
                # ------------------------------------------------

                restored_in_batch = False

                if item.batch_id:

                    batch = (
                        session.query(ProductBatch)
                        .filter(
                            ProductBatch.id
                            == item.batch_id
                        )
                        .first()
                    )

                    if batch:

                        batch.stock_units = float(
                            batch.stock_units or 0
                        ) + stock_units

                        batch.is_active = True

                        restored_in_batch = True

                # ------------------------------------------------
                # SI PAS DE LOT :
                # restaurer directement le stock produit.
                # ------------------------------------------------

                if not restored_in_batch:

                    product.stock_units = float(
                        product.stock_units or 0
                    ) + stock_units

                    product.quantity = float(
                        product.quantity or 0
                    ) + stock_units

                restored_products.add(
                    product.id
                )

            # ------------------------------------------------
            # SYNCHRONISATION DES STOCKS
            # ------------------------------------------------

            session.flush()

            for product_id in restored_products:

                product = (
                    session.query(Product)
                    .filter(
                        Product.id == product_id
                    )
                    .first()
                )

                if not product:
                    continue

                try:

                    synchronize_product_stock(
                        session,
                        product
                    )

                except TypeError:

                    # Si la fonction attend seulement
                    # le produit.
                    try:
                        synchronize_product_stock(
                            product
                        )
                    except Exception:
                        pass

                except Exception:
                    pass

            # ------------------------------------------------
            # SUPPRESSION DE LA VENTE
            # ------------------------------------------------

            session.delete(sale)

            session.commit()

            QMessageBox.information(
                self,
                "Vente supprimée",
                (
                    f"La vente {invoice} a été supprimée.\n\n"
                    "Le stock a été restauré."
                )
            )

            self.load_sales()

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "La vente n'a pas pu être supprimée.\n\n"
                    f"{error}"
                )
            )

        finally:

            session.close()

    # ========================================================
    # CONVERSION DE SÉCURITÉ
    # ========================================================

    def convert_sale_quantity_to_base_units(
        self,
        product,
        sale_item
    ):

        """
        Convertit la quantité vendue en unités de base
        si l'ancien enregistrement ne possède pas
        stock_units.
        """

        quantity = float(
            sale_item.quantity or 0
        )

        unit = (
            str(
                sale_item.sale_unit
                or product.base_unit
                or "Pièce"
            )
            .strip()
            .lower()
        )

        # Unité de base
        if unit in [
            "comprimé",
            "comprime",
            "unité",
            "unite",
            "pièce",
            "piece",
            "flacon",
            "ampoule",
        ]:
            return quantity

        # Plaquette
        if unit == "plaquette":

            per_plaquette = (
                product.units_per_plaquette
                or 1
            )

            return (
                quantity
                * float(per_plaquette)
            )

        # Boîte
        if unit == "boîte" or unit == "boite":

            per_plaquette = (
                product.units_per_plaquette
                or 1
            )

            plaquettes_per_box = (
                product.plaquettes_per_box
                or 1
            )

            return (
                quantity
                * float(per_plaquette)
                * float(plaquettes_per_box)
            )

        # Carton
        if unit == "carton":

            per_plaquette = (
                product.units_per_plaquette
                or 1
            )

            plaquettes_per_box = (
                product.plaquettes_per_box
                or 1
            )

            boxes_per_carton = (
                product.boxes_per_carton
                or 1
            )

            return (
                quantity
                * float(per_plaquette)
                * float(plaquettes_per_box)
                * float(boxes_per_carton)
            )

        return quantity


# ============================================================
# DIALOGUE DÉTAILS VENTE
# ============================================================

class SaleDetailsDialog(QDialog):

    def __init__(
        self,
        sale,
        parent=None
    ):

        super().__init__(parent)

        self.sale = sale

        self.setWindowTitle(
            f"Détails de la vente - "
            f"{sale.invoice_number or sale.id}"
        )

        self.resize(850, 600)

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

        layout.setSpacing(15)

        # ----------------------------------------------------
        # EN-TÊTE
        # ----------------------------------------------------

        header = QFrame()

        header_layout = QGridLayout(header)

        header_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        invoice_label = QLabel("Facture")

        invoice_value = QLabel(
            self.sale.invoice_number
            or "-"
        )

        invoice_value.setObjectName(
            "headerValue"
        )

        date_label = QLabel("Date")

        date_value = QLabel(
            format_datetime(
                self.sale.created_at
            )
        )

        date_value.setObjectName(
            "headerValue"
        )

        client_label = QLabel("Client")

        client_value = QLabel(
            self.sale.client_name
            or "Client comptoir"
        )

        client_value.setObjectName(
            "headerValue"
        )

        payment_label = QLabel(
            "Paiement"
        )

        payment_value = QLabel(
            normalize_payment_method(
                self.sale.payment_method
            )
        )

        payment_value.setObjectName(
            "headerValue"
        )

        header_layout.addWidget(
            invoice_label,
            0,
            0
        )

        header_layout.addWidget(
            invoice_value,
            0,
            1
        )

        header_layout.addWidget(
            date_label,
            0,
            2
        )

        header_layout.addWidget(
            date_value,
            0,
            3
        )

        header_layout.addWidget(
            client_label,
            1,
            0
        )

        header_layout.addWidget(
            client_value,
            1,
            1
        )

        header_layout.addWidget(
            payment_label,
            1,
            2
        )

        header_layout.addWidget(
            payment_value,
            1,
            3
        )

        layout.addWidget(header)

        # ----------------------------------------------------
        # TABLE DES ARTICLES
        # ----------------------------------------------------

        table = QTableWidget()

        table.setColumnCount(8)

        table.setHorizontalHeaderLabels([
            "Produit",
            "Lot",
            "Expiration",
            "Quantité",
            "Unité",
            "Prix unitaire",
            "Total",
            "Stock",
        ])

        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

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
            QHeaderView.Stretch
        )

        for column in range(1, 8):

            table.horizontalHeader().setSectionResizeMode(
                column,
                QHeaderView.ResizeToContents
            )

        items = list(
            self.sale.items or []
        )

        table.setRowCount(
            len(items)
        )

        for row, item in enumerate(items):

            product_name = "-"

            if item.product:

                product_name = (
                    item.product.name
                    or "-"
                )

            self.set_item(
                table,
                row,
                0,
                product_name
            )

            self.set_item(
                table,
                row,
                1,
                item.batch_number or "-"
            )

            self.set_item(
                table,
                row,
                2,
                format_datetime(
                    item.expiry_date
                )
            )

            self.set_item(
                table,
                row,
                3,
                format_number(
                    item.quantity
                ),
                Qt.AlignCenter
            )

            self.set_item(
                table,
                row,
                4,
                item.sale_unit or "-",
                Qt.AlignCenter
            )

            self.set_item(
                table,
                row,
                5,
                format_money(
                    item.unit_price
                ),
                Qt.AlignRight
            )

            self.set_item(
                table,
                row,
                6,
                format_money(
                    item.total_price
                ),
                Qt.AlignRight
            )

            self.set_item(
                table,
                row,
                7,
                format_number(
                    item.stock_units
                ),
                Qt.AlignRight
            )

        layout.addWidget(
            table,
            1
        )

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        total_frame = QFrame()

        total_layout = QHBoxLayout(
            total_frame
        )

        total_layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        total_label = QLabel(
            "TOTAL DE LA VENTE"
        )

        total_label.setObjectName(
            "totalLabel"
        )

        total_value = QLabel(
            format_money(
                self.sale.total
            )
        )

        total_value.setObjectName(
            "totalValue"
        )

        total_layout.addWidget(
            total_label
        )

        total_layout.addStretch()

        total_layout.addWidget(
            total_value
        )

        layout.addWidget(
            total_frame
        )

        # ----------------------------------------------------
        # BOUTON FERMER
        # ----------------------------------------------------

        buttons_layout = QHBoxLayout()

        buttons_layout.addStretch()

        close_button = QPushButton(
            "Fermer"
        )

        close_button.setMinimumWidth(
            110
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
    # ITEM TABLE
    # ========================================================

    def set_item(
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
    # STYLES
    # ========================================================

    def apply_styles(self):

        self.setStyleSheet("""
            QDialog {
                background-color: #f4f6f8;
                color: #08192d;
            }

            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }

            QLabel {
                color: #475569;
                font-size: 13px;
            }

            QLabel#headerValue {
                color: #08192d;
                font-weight: 700;
            }

            QLabel#totalLabel {
                color: #08192d;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#totalValue {
                color: #08192d;
                font-size: 24px;
                font-weight: 700;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                color: #08192d;
                selection-background-color: #fff7cc;
                selection-color: #08192d;
            }

            QTableWidget::item {
                padding: 7px;
            }

            QHeaderView::section {
                background-color: #08192d;
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
            }

            QPushButton {
                background-color: #08192d;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #102d4d;
            }
        """)