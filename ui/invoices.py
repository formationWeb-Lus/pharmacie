# ui/invoices.py

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QAbstractItemView,
)

from database.database import SessionLocal
from database.models import Sale
from utils.pdf_generator import generate_invoice_pdf


class InvoicesPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName(
            "invoicesPage"
        )

        # =========================================================
        # SCROLL AREA
        # =========================================================

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # =========================================================
        # CONTENU
        # =========================================================

        content = QWidget()

        content.setObjectName(
            "invoicesContent"
        )

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout(
            content
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            40
        )

        layout.setSpacing(
            18
        )

        # =========================================================
        # TITRE
        # =========================================================

        title = QLabel(
            "🧾 Historique des factures"
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        # =========================================================
        # SOUS-TITRE
        # =========================================================

        subtitle = QLabel(
            "Consultez les ventes enregistrées et générez "
            "à nouveau les factures PDF."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            subtitle
        )

        # =========================================================
        # STATISTIQUES
        # =========================================================

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(
            12
        )

        # ---------------------------------------------------------
        # NOMBRE DE FACTURES
        # ---------------------------------------------------------

        self.stat_invoices = self.create_stat_card(
            "🧾 Factures",
            "0"
        )

        stats_layout.addWidget(
            self.stat_invoices
        )

        # ---------------------------------------------------------
        # CHIFFRE D'AFFAIRES
        # ---------------------------------------------------------

        self.stat_revenue = self.create_stat_card(
            "💰 Chiffre d'affaires",
            "0 CDF"
        )

        stats_layout.addWidget(
            self.stat_revenue
        )

        # ---------------------------------------------------------
        # DERNIÈRE FACTURE
        # ---------------------------------------------------------

        self.stat_last = self.create_stat_card(
            "📅 Dernière vente",
            "Aucune"
        )

        stats_layout.addWidget(
            self.stat_last
        )

        layout.addLayout(
            stats_layout
        )

        # =========================================================
        # TABLEAU
        # =========================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            7
        )

        self.table.setHorizontalHeaderLabels([
            "N° Facture",
            "Date",
            "Client",
            "Articles",
            "Paiement",
            "Total",
            "Action",
        ])

        # =========================================================
        # CONFIGURATION
        # =========================================================

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setWordWrap(
            False
        )

        # La page entière défile
        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.table.setMinimumHeight(
            400
        )

        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        # =========================================================
        # COLONNES
        # =========================================================

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.verticalHeader().setDefaultSectionSize(
            52
        )

        layout.addWidget(
            self.table
        )

        # =========================================================
        # INFORMATION
        # =========================================================

        info = QLabel(
            "💡 Les factures restent enregistrées même après "
            "la fermeture de l'application. Vous pouvez "
            "regénérer leur PDF à tout moment."
        )

        info.setObjectName(
            "infoLabel"
        )

        info.setWordWrap(
            True
        )

        layout.addWidget(
            info
        )

        layout.addStretch()

        # =========================================================
        # INSTALLER CONTENT
        # =========================================================

        scroll_area.setWidget(
            content
        )

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        main_layout.addWidget(
            scroll_area
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
    # CARTE STATISTIQUE
    # =============================================================

    def create_stat_card(
        self,
        title,
        value
    ):

        card = QFrame()

        card.setObjectName(
            "statCard"
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        card_layout.setSpacing(
            5
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "statTitle"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "statValue"
        )

        card_layout.addWidget(
            title_label
        )

        card_layout.addWidget(
            value_label
        )

        # Conserver la référence au label
        card.value_label = value_label

        return card

    # =============================================================
    # STYLE
    # =============================================================

    def apply_styles(self):

        self.setStyleSheet("""
            #invoicesPage {
                background-color: #F8FAFC;
            }

            #invoicesContent {
                background-color: #F8FAFC;
            }

            QLabel#pageTitle {
                font-size: 26px;
                font-weight: 700;
                color: #08192D;
                padding: 5px 0;
            }

            QLabel#pageSubtitle {
                font-size: 13px;
                color: #667085;
                padding-bottom: 5px;
            }

            QFrame#statCard {
                background-color: white;
                border: 1px solid #EAECF0;
                border-radius: 10px;
            }

            QLabel#statTitle {
                color: #667085;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#statValue {
                color: #08192D;
                font-size: 19px;
                font-weight: 700;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #E2E8F0;
                color: #1E293B;
                font-size: 13px;
                selection-background-color: #FEF3C7;
                selection-color: #08192D;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QHeaderView::section {
                background-color: #08192D;
                color: white;
                font-weight: 700;
                padding: 10px;
                border: none;
            }

            QPushButton {
                background-color: #08192D;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #102A43;
            }

            QPushButton:pressed {
                background-color: #061321;
            }

            QPushButton[class="btn-primary"] {
                background-color: #08192D;
            }

            QPushButton[class="btn-primary"]:hover {
                background-color: #102A43;
            }

            QLabel#infoLabel {
                color: #667085;
                font-size: 12px;
                padding: 5px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                background: #EEF1F5;
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #98A2B3;
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
        """)

    # =============================================================
    # ACTUALISER LES FACTURES
    # =============================================================

    def refresh(self):

        session = SessionLocal()

        try:

            sales = (
                session.query(Sale)
                .order_by(
                    Sale.created_at.desc()
                )
                .all()
            )

            self.table.setRowCount(
                0
            )

            # =====================================================
            # STATISTIQUES
            # =====================================================

            number_of_invoices = len(
                sales
            )

            total_revenue = sum(
                float(
                    sale.total or 0
                )
                for sale in sales
            )

            self.stat_invoices.value_label.setText(
                str(number_of_invoices)
            )

            self.stat_revenue.value_label.setText(
                f"{total_revenue:,.2f} CDF"
            )

            if sales and sales[0].created_at:

                self.stat_last.value_label.setText(
                    sales[0].created_at.strftime(
                        "%d/%m/%Y"
                    )
                )

            else:

                self.stat_last.value_label.setText(
                    "Aucune"
                )

            # =====================================================
            # TABLEAU
            # =====================================================

            for sale in sales:

                row = self.table.rowCount()

                self.table.insertRow(
                    row
                )

                # =================================================
                # NUMÉRO
                # =================================================

                invoice_item = QTableWidgetItem(
                    str(
                        sale.invoice_number
                        or "N/A"
                    )
                )

                invoice_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    0,
                    invoice_item
                )

                # =================================================
                # DATE
                # =================================================

                date_text = ""

                if sale.created_at:

                    date_text = sale.created_at.strftime(
                        "%d/%m/%Y %H:%M"
                    )

                date_item = QTableWidgetItem(
                    date_text
                )

                date_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    1,
                    date_item
                )

                # =================================================
                # CLIENT
                # =================================================

                client_name = (
                    sale.client_name
                    if sale.client_name
                    else "Client comptant"
                )

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        client_name
                    )
                )

                # =================================================
                # ARTICLES
                # =================================================

                items = getattr(
                    sale,
                    "items",
                    None
                )

                if items is not None:

                    item_count = sum(
                        int(
                            getattr(
                                item,
                                "quantity",
                                0
                            ) or 0
                        )
                        for item in items
                    )

                    distinct_products = len(
                        items
                    )

                else:

                    item_count = 0
                    distinct_products = 0

                if distinct_products > 0:

                    article_text = (
                        f"{distinct_products} produit(s) "
                        f"/ {item_count} unité(s)"
                    )

                else:

                    article_text = "N/A"

                article_item = QTableWidgetItem(
                    article_text
                )

                article_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    3,
                    article_item
                )

                # =================================================
                # PAIEMENT
                # =================================================

                payment_method = getattr(
                    sale,
                    "payment_method",
                    None
                )

                if payment_method:

                    payment_text = str(
                        payment_method
                    )

                else:

                    payment_text = "N/A"

                payment_item = QTableWidgetItem(
                    payment_text
                )

                payment_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    4,
                    payment_item
                )

                # =================================================
                # TOTAL
                # =================================================

                total = float(
                    sale.total or 0
                )

                total_item = QTableWidgetItem(
                    f"{total:,.2f} CDF"
                )

                total_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    5,
                    total_item
                )

                # =================================================
                # BOUTON PDF
                # =================================================

                btn_pdf = QPushButton(
                    "📄 PDF"
                )

                btn_pdf.setProperty(
                    "class",
                    "btn-primary"
                )

                btn_pdf.setMinimumHeight(
                    34
                )

                btn_pdf.setToolTip(
                    "Générer à nouveau la facture PDF"
                )

                btn_pdf.clicked.connect(
                    lambda checked=False,
                    sale_id=sale.id:
                    self.download_pdf(
                        sale_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    6,
                    btn_pdf
                )

                # =================================================
                # HAUTEUR
                # =================================================

                self.table.setRowHeight(
                    row,
                    52
                )

            # =====================================================
            # HAUTEUR TABLEAU
            # =====================================================

            header_height = (
                self.table.horizontalHeader().height()
            )

            rows_height = sum(
                self.table.rowHeight(row)
                for row in range(
                    self.table.rowCount()
                )
            )

            table_height = (
                header_height
                + rows_height
                + 15
            )

            table_height = max(
                400,
                table_height
            )

            self.table.setMinimumHeight(
                table_height
            )

            self.table.setMaximumHeight(
                table_height
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger les factures.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()

    # =============================================================
    # GÉNÉRER LE PDF
    # =============================================================

    def download_pdf(
        self,
        sale_id
    ):

        session = SessionLocal()

        try:

            sale = session.get(
                Sale,
                sale_id
            )

            if not sale:

                QMessageBox.warning(
                    self,
                    "Facture introuvable",
                    "La facture demandée n'existe plus."
                )

                return

            # =====================================================
            # DOSSIER FACTURES
            # =====================================================

            invoices_directory = os.path.join(
                os.path.expanduser("~"),
                "Pharmacie",
                "Factures"
            )

            os.makedirs(
                invoices_directory,
                exist_ok=True
            )

            # =====================================================
            # NOM DU PDF
            # =====================================================

            invoice_number = (
                str(
                    sale.invoice_number
                    or f"facture_{sale.id}"
                )
                .replace(
                    "/",
                    "_"
                )
                .replace(
                    "\\",
                    "_"
                )
            )

            pdf_path = os.path.join(
                invoices_directory,
                f"{invoice_number}.pdf"
            )

            # =====================================================
            # GÉNÉRATION
            # =====================================================

            generate_invoice_pdf(
                sale,
                pdf_path
            )

            # =====================================================
            # VÉRIFICATION
            # =====================================================

            if not os.path.exists(
                pdf_path
            ):

                QMessageBox.warning(
                    self,
                    "PDF non créé",
                    (
                        "La génération a été exécutée, "
                        "mais le fichier PDF n'a pas été trouvé."
                    )
                )

                return

            # =====================================================
            # CONFIRMATION
            # =====================================================

            QMessageBox.information(
                self,
                "PDF généré",
                (
                    "La facture PDF a été générée avec succès.\n\n"
                    f"{pdf_path}"
                )
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de générer le PDF.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()