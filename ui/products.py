# ui/products.py
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QComboBox,
)

from database.database import SessionLocal
from database.models import Product, ProductBatch


# =============================================================
# CONDITIONS DISPONIBLES
# =============================================================

PACKAGING_OPTIONS = [
    "Plaquette",
    "Boîte",
    "Carton",
    "Autre produit",
]


class ProductsPage(QWidget):
    """
    Gestion des produits et médicaments.

    Règles :

    Tous les produits :
        - Nom du produit
        - Fournisseur

    Plaquette :
        - Quantité de plaquettes
        - Prix de vente par plaquette
        - Date d'expiration

    Boîte :
        - Nombre de boîtes
        - Prix de vente par boîte
        - Date d'expiration

    Carton :
        - Nombre de boîtes dans un carton
        - Nombre de plaquettes dans une boîte
        - Quantité de cartons
        - Prix de vente par plaquette
        - Date d'expiration

    Autre produit :
        - Quantité
        - Prix de vente par unité
        - Date d'expiration
    """

    def __init__(self):
        super().__init__()

        self.selected_product_id = None

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.content_widget = QWidget()
        self.content_widget.setObjectName("productsContent")
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(24, 24, 24, 40)
        self.layout.setSpacing(18)

        self.scroll_area.setWidget(self.content_widget)
        outer_layout.addWidget(self.scroll_area)

        # =========================================================
        # TITRE
        # =========================================================

        title = QLabel("💊 Ajout des produits")
        title.setObjectName("pageTitle")
        self.layout.addWidget(title)

        subtitle = QLabel(
            "Ajoutez les médicaments et produits avec leur fournisseur "
            "et définissez leur conditionnement initial."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        self.layout.addWidget(subtitle)

        # =========================================================
        # CARTE FORMULAIRE
        # =========================================================

        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        form = QFormLayout(form_card)
        form.setContentsMargins(22, 22, 22, 22)
        form.setSpacing(14)

        self.form_layout = form

        # =========================================================
        # NOM DU PRODUIT
        # =========================================================

        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText(
            "Ex : Paracétamol 500 mg"
        )
        self.name_in.setMinimumHeight(44)

        # =========================================================
        # FOURNISSEUR
        # =========================================================

        self.supplier_in = QLineEdit()
        self.supplier_in.setPlaceholderText(
            "Ex : Pharmacie XYZ / Jean Mukendi"
        )
        self.supplier_in.setMinimumHeight(44)

        # =========================================================
        # CONDITION INITIALE
        # =========================================================

        self.packaging_in = QComboBox()
        self.packaging_in.addItems(PACKAGING_OPTIONS)
        self.packaging_in.setMinimumHeight(44)

        self.packaging_in.currentTextChanged.connect(
            self.update_packaging_fields
        )

        # =========================================================
        # NOMBRE DE BOÎTES DANS UN CARTON
        # =========================================================

        self.boxes_per_carton_in = QSpinBox()
        self.boxes_per_carton_in.setRange(1, 100000)
        self.boxes_per_carton_in.setValue(1)
        self.boxes_per_carton_in.setMinimumHeight(44)

        # =========================================================
        # NOMBRE DE PLAQUETTES DANS UNE BOÎTE
        # =========================================================

        self.units_per_box_in = QSpinBox()
        self.units_per_box_in.setRange(1, 100000)
        self.units_per_box_in.setValue(1)
        self.units_per_box_in.setMinimumHeight(44)

        # =========================================================
        # QUANTITÉ
        # =========================================================

        self.qty_in = QSpinBox()
        self.qty_in.setRange(1, 100000000)
        self.qty_in.setValue(1)
        self.qty_in.setMinimumHeight(44)

        # =========================================================
        # PRIX DE VENTE
        # =========================================================

        self.price_in = QDoubleSpinBox()
        self.price_in.setRange(0.01, 100000000000.0)
        self.price_in.setDecimals(2)
        self.price_in.setSuffix(" CDF")
        self.price_in.setMinimumHeight(44)

        # =========================================================
        # DATE D'EXPIRATION
        # =========================================================

        self.expiry_in = QDateEdit()
        self.expiry_in.setCalendarPopup(True)
        self.expiry_in.setDate(
            QDate.currentDate().addYears(1)
        )
        self.expiry_in.setDisplayFormat("dd/MM/yyyy")
        self.expiry_in.setMinimumHeight(44)

        # =========================================================
        # LABELS DYNAMIQUES
        # =========================================================

        self.label_boxes_per_carton = QLabel(
            "Nombre de boîtes dans un carton * :"
        )

        self.label_units_per_box = QLabel(
            "Nombre de plaquettes dans une boîte * :"
        )

        self.label_quantity = QLabel(
            "Quantité * :"
        )

        self.label_price = QLabel(
            "Prix de vente * :"
        )

        self.label_expiry = QLabel(
            "Date d'expiration * :"
        )

        # =========================================================
        # AJOUT DES LIGNES
        # =========================================================

        form.addRow(
            "Nom du produit / médicament * :",
            self.name_in,
        )

        form.addRow(
            "Nom du fournisseur * :",
            self.supplier_in,
        )

        form.addRow(
            "Condition initiale * :",
            self.packaging_in,
        )

        # IMPORTANT :
        # Pour CARTON :
        # 1. Nombre de boîtes dans un carton
        # 2. Nombre de plaquettes dans une boîte
        # 3. Quantité de cartons
        # 4. Prix de vente par plaquette
        # 5. Date expiration

        self.row_boxes_per_carton = form.rowCount()

        form.addRow(
            self.label_boxes_per_carton,
            self.boxes_per_carton_in,
        )

        self.row_units_per_box = form.rowCount()

        form.addRow(
            self.label_units_per_box,
            self.units_per_box_in,
        )

        self.row_quantity = form.rowCount()

        form.addRow(
            self.label_quantity,
            self.qty_in,
        )

        self.row_price = form.rowCount()

        form.addRow(
            self.label_price,
            self.price_in,
        )

        self.row_expiry = form.rowCount()

        form.addRow(
            self.label_expiry,
            self.expiry_in,
        )

        # =========================================================
        # MESSAGE CONVERSION
        # =========================================================

        self.conversion_label = QLabel()
        self.conversion_label.setObjectName(
            "conversionLabel"
        )
        self.conversion_label.setWordWrap(True)
        self.conversion_label.setMinimumHeight(45)

        self.row_conversion = form.rowCount()

        form.addRow(
            "",
            self.conversion_label,
        )

        # =========================================================
        # BOUTONS
        # =========================================================

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.btn_save = QPushButton(
            "➕ Ajouter le produit"
        )

        self.btn_save.setProperty(
            "class",
            "btn-primary",
        )

        self.btn_save.setMinimumHeight(46)

        self.btn_save.clicked.connect(
            self.save_product
        )

        self.btn_cancel = QPushButton(
            "↩ Annuler / Réinitialiser"
        )

        self.btn_cancel.setMinimumHeight(46)

        self.btn_cancel.clicked.connect(
            self.clear_form
        )

        self.btn_cancel.setVisible(False)

        buttons_layout.addWidget(
            self.btn_save
        )

        buttons_layout.addWidget(
            self.btn_cancel
        )

        self.row_buttons = form.rowCount()

        form.addRow(
            "",
            buttons_layout,
        )

        self.layout.addWidget(form_card)

        # =========================================================
        # TABLEAU
        # =========================================================

        table_header = QHBoxLayout()

        table_title_box = QVBoxLayout()

        table_title = QLabel(
            "📋 Produits et stocks enregistrés"
        )

        table_title.setObjectName(
            "tableTitle"
        )

        table_subtitle = QLabel(
            "Les produits enregistrés apparaissent ici "
            "avec leur fournisseur, stock et date d'expiration."
        )

        table_subtitle.setObjectName(
            "tableSubtitle"
        )

        table_subtitle.setWordWrap(True)

        table_title_box.addWidget(
            table_title
        )

        table_title_box.addWidget(
            table_subtitle
        )

        table_header.addLayout(
            table_title_box
        )

        table_header.addStretch()

        self.layout.addLayout(
            table_header
        )

        # =========================================================
        # TABLE
        # =========================================================

        self.table = QTableWidget()

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "Produit",
            "Fournisseur",
            "Condition",
            "Stock",
            "Prix / unité",
            "Prix / plaquette",
            "Prix / boîte",
            "Prix / carton",
            "Expiration",
        ])

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(True)

        self.table.setWordWrap(False)

        self.table.setMinimumHeight(400)

        self.table.setMaximumHeight(650)

        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.table.itemDoubleClicked.connect(
            self.handle_table_double_click
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(1, 9):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.table.verticalHeader().setDefaultSectionSize(
            48
        )

        self.layout.addWidget(
            self.table
        )

        # =========================================================
        # INFO
        # =========================================================

        info = QLabel(
            "💡 Le prix d'achat n'est pas demandé au travailleur. "
            "Le fournisseur est enregistré pour chaque produit."
        )

        info.setObjectName(
            "infoLabel"
        )

        info.setWordWrap(True)

        self.layout.addWidget(
            info
        )

        self.layout.addSpacing(30)

        # =========================================================
        # STYLE
        # =========================================================

        self.apply_styles()

        self.update_packaging_fields(
            self.packaging_in.currentText()
        )

        self.refresh()

    # =============================================================
    # STYLE
    # =============================================================

    def apply_styles(self):

        self.setStyleSheet("""
            QWidget {
                color: #344054;
            }

            QWidget#productsContent {
                background: #F8FAFC;
            }

            QLabel#pageTitle {
                color: #10233F;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #667085;
                font-size: 13px;
                padding-bottom: 5px;
            }

            QFrame#formCard {
                background: white;
                border: 1px solid #EAECF0;
                border-radius: 12px;
            }

            QLineEdit,
            QSpinBox,
            QDoubleSpinBox,
            QDateEdit,
            QComboBox {
                background: white;
                border: 1px solid #D0D5DD;
                border-radius: 8px;
                padding: 8px 10px;
                color: #344054;
                font-size: 13px;
            }

            QLineEdit:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QDateEdit:focus,
            QComboBox:focus {
                border: 1px solid #10233F;
            }

            QComboBox::drop-down {
                border: none;
                width: 35px;
            }

            QComboBox QAbstractItemView {
                background: white;
                color: #344054;
                border: 1px solid #D0D5DD;
                selection-background-color: #EEF4FF;
                selection-color: #10233F;
                padding: 5px;
            }

            QPushButton {
                background: #10233F;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #1D3557;
            }

            QPushButton[class="btn-primary"] {
                background: #10233F;
            }

            QPushButton[class="btn-primary"]:hover {
                background: #1D3557;
            }

            QPushButton[class="btn-success"] {
                background: #039855;
            }

            QPushButton[class="btn-success"]:hover {
                background: #027A48;
            }

            QLabel#tableTitle {
                font-size: 17px;
                font-weight: 700;
                color: #10233F;
            }

            QLabel#tableSubtitle {
                font-size: 12px;
                color: #667085;
            }

            QLabel#conversionLabel {
                background: #F2F4F7;
                border: 1px solid #EAECF0;
                border-radius: 8px;
                padding: 10px;
                color: #475467;
                font-size: 12px;
            }

            QLabel#infoLabel {
                color: #667085;
                font-size: 12px;
                padding: 5px;
            }

            QTableWidget {
                background: white;
                border: 1px solid #EAECF0;
                border-radius: 10px;
                gridline-color: #F2F4F7;
                color: #344054;
                font-size: 13px;
                selection-background-color: #EEF4FF;
                selection-color: #10233F;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QHeaderView::section {
                background: #F9FAFB;
                color: #475467;
                border: none;
                border-bottom: 1px solid #EAECF0;
                padding: 11px;
                font-weight: 700;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                background: #EEF1F5;
                width: 10px;
                margin: 0px;
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
    # VISIBILITÉ
    # =============================================================

    def set_form_row_visible(
        self,
        row,
        visible,
    ):
        self.form_layout.setRowVisible(
            row,
            visible,
        )

    # =============================================================
    # CHAMPS DYNAMIQUES
    # =============================================================

    def update_packaging_fields(
        self,
        packaging=None,
    ):
        """
        Change les champs selon la condition initiale.
        """

        if packaging is None:
            packaging = (
                self.packaging_in.currentText()
            )

        packaging = packaging.strip()

        # ---------------------------------------------------------
        # LE FOURNISSEUR EST TOUJOURS VISIBLE
        # ---------------------------------------------------------

        self.set_form_row_visible(
            self.row_boxes_per_carton,
            packaging == "Carton",
        )

        self.set_form_row_visible(
            self.row_units_per_box,
            packaging == "Carton",
        )

        # ---------------------------------------------------------
        # PLAQUETTE
        # ---------------------------------------------------------

        if packaging == "Plaquette":

            self.label_quantity.setText(
                "Nombre de plaquettes * :"
            )

            self.label_price.setText(
                "Prix de vente / plaquette * :"
            )

            self.conversion_label.setText(
                "💊 Condition : plaquette. "
                "La quantité correspond directement au nombre "
                "de plaquettes disponibles."
            )

        # ---------------------------------------------------------
        # BOÎTE
        # ---------------------------------------------------------

        elif packaging == "Boîte":

            self.label_quantity.setText(
                "Nombre de boîtes * :"
            )

            self.label_price.setText(
                "Prix de vente / boîte * :"
            )

            self.conversion_label.setText(
                "📦 Condition : boîte. "
                "La quantité correspond au nombre de boîtes."
            )

        # ---------------------------------------------------------
        # CARTON
        # ---------------------------------------------------------

        elif packaging == "Carton":

            # ORDRE EXACT DEMANDÉ :
            #
            # 1. Nombre de boîtes dans un carton
            # 2. Nombre de plaquettes dans une boîte
            # 3. Nombre de cartons
            # 4. Prix de vente par plaquette
            # 5. Date expiration

            self.label_boxes_per_carton.setText(
                "1. Nombre de boîtes dans un carton * :"
            )

            self.label_units_per_box.setText(
                "2. Nombre de plaquettes dans une boîte * :"
            )

            self.label_quantity.setText(
                "3. Nombre de cartons * :"
            )

            self.label_price.setText(
                "4. Prix de vente / plaquette * :"
            )

            total_plaquettes = (
                self.boxes_per_carton_in.value()
                * self.units_per_box_in.value()
            )

            self.conversion_label.setText(
                f"📦 1 carton = "
                f"{self.boxes_per_carton_in.value()} boîte(s) = "
                f"{total_plaquettes} plaquette(s). "
                f"La quantité correspond au nombre de cartons."
            )

        # ---------------------------------------------------------
        # AUTRE PRODUIT
        # ---------------------------------------------------------

        else:

            self.label_quantity.setText(
                "Quantité * :"
            )

            self.label_price.setText(
                "Prix de vente / unité * :"
            )

            self.conversion_label.setText(
                "📦 Autre produit : "
                "fournisseur + produit + quantité + "
                "prix par unité + date d'expiration."
            )

        self.update_conversion_label()

    # =============================================================
    # CONVERSION
    # =============================================================

    def update_conversion_label(self):

        packaging = (
            self.packaging_in.currentText().strip()
        )

        if packaging == "Plaquette":

            self.conversion_label.setText(
                "💊 La quantité saisie correspond au nombre "
                "de plaquettes."
            )

        elif packaging == "Boîte":

            self.conversion_label.setText(
                "📦 La quantité saisie correspond au nombre "
                "de boîtes."
            )

        elif packaging == "Carton":

            boxes = max(
                1,
                self.boxes_per_carton_in.value(),
            )

            plaquettes = max(
                1,
                self.units_per_box_in.value(),
            )

            total = boxes * plaquettes

            self.conversion_label.setText(
                f"📦 1 carton = {boxes} boîte(s) = "
                f"{total} plaquette(s). "
                f"La quantité saisie correspond au nombre "
                f"de cartons."
            )

        else:

            self.conversion_label.setText(
                "📦 Produit vendu directement à l'unité."
            )

    # =============================================================
    # UNITÉS DE STOCK
    # =============================================================

    def get_units_per_package(
        self,
        packaging=None,
    ):

        if packaging is None:
            packaging = (
                self.packaging_in.currentText().strip()
            )

        plaquettes_per_box = max(
            1,
            self.units_per_box_in.value(),
        )

        boxes_per_carton = max(
            1,
            self.boxes_per_carton_in.value(),
        )

        if packaging == "Plaquette":
            return 1

        if packaging == "Boîte":
            return 1

        if packaging == "Carton":
            return (
                plaquettes_per_box
                * boxes_per_carton
            )

        return 1

    # =============================================================
    # STOCK
    # =============================================================

    def format_stock(
        self,
        product,
        stock_units,
    ):

        stock_units = int(
            stock_units or 0
        )

        packaging = (
            getattr(
                product,
                "packaging",
                "Plaquette",
            )
            or "Plaquette"
        )

        plaquettes_per_box = max(
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

        if packaging == "Autre produit":
            return (
                f"{stock_units} unité(s)"
            )

        if packaging == "Plaquette":
            return (
                f"{stock_units} plaquette(s)"
            )

        if packaging == "Boîte":
            return (
                f"{stock_units} boîte(s)"
            )

        plaquettes_per_carton = (
            plaquettes_per_box
            * boxes_per_carton
        )

        cartons = (
            stock_units
            // plaquettes_per_carton
        )

        remainder = (
            stock_units
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
                f"{cartons} carton(s)"
            )

        if boxes:
            parts.append(
                f"{boxes} boîte(s)"
            )

        if plaquettes:
            parts.append(
                f"{plaquettes} plaquette(s)"
            )

        return (
            " + ".join(parts)
            if parts
            else "0 carton"
        )

    # =============================================================
    # CALCUL DES PRIX
    # =============================================================

    def calculate_prices(
        self,
        packaging,
        entered_price,
    ):

        plaquettes_per_box = max(
            1,
            self.units_per_box_in.value(),
        )

        boxes_per_carton = max(
            1,
            self.boxes_per_carton_in.value(),
        )

        # ---------------------------------------------------------
        # PLAQUETTE
        # ---------------------------------------------------------

        if packaging == "Plaquette":

            price_per_plaquette = (
                entered_price
            )

            price_per_box = (
                entered_price
                * plaquettes_per_box
            )

            price_per_carton = (
                price_per_box
                * boxes_per_carton
            )

        # ---------------------------------------------------------
        # BOÎTE
        # ---------------------------------------------------------

        elif packaging == "Boîte":

            price_per_box = (
                entered_price
            )

            price_per_plaquette = (
                entered_price
                / max(
                    1,
                    plaquettes_per_box,
                )
            )

            price_per_carton = (
                entered_price
                * boxes_per_carton
            )

        # ---------------------------------------------------------
        # CARTON
        # ---------------------------------------------------------

        elif packaging == "Carton":

            # L'utilisateur saisit :
            # prix de vente par plaquette

            price_per_plaquette = (
                entered_price
            )

            price_per_box = (
                entered_price
                * plaquettes_per_box
            )

            price_per_carton = (
                price_per_box
                * boxes_per_carton
            )

        # ---------------------------------------------------------
        # AUTRE
        # ---------------------------------------------------------

        else:

            price_per_plaquette = (
                entered_price
            )

            price_per_box = (
                entered_price
            )

            price_per_carton = (
                entered_price
            )

        return {
            "price_per_comprime": entered_price,
            "price_per_plaquette": (
                price_per_plaquette
            ),
            "price_per_box": (
                price_per_box
            ),
            "price_per_carton": (
                price_per_carton
            ),
        }

    # =============================================================
    # ASSIGNATION PRIX
    # =============================================================

    def assign_product_prices(
        self,
        product,
        prices,
    ):

        for field, value in prices.items():

            if hasattr(product, field):
                setattr(
                    product,
                    field,
                    value,
                )

    # =============================================================
    # ENREGISTREMENT
    # =============================================================

    def save_product(self):

        name = (
            self.name_in.text().strip()
        )

        supplier = (
            self.supplier_in.text().strip()
        )

        packaging = (
            self.packaging_in.currentText().strip()
        )

        quantity = (
            self.qty_in.value()
        )

        sale_price = (
            self.price_in.value()
        )

        expiry_date = (
            self.get_expiry_date()
        )

        # =========================================================
        # VALIDATION NOM
        # =========================================================

        if not name:

            QMessageBox.warning(
                self,
                "Champ requis",
                "Veuillez renseigner le nom du médicament ou du produit.",
            )

            self.name_in.setFocus()

            return

        # =========================================================
        # VALIDATION FOURNISSEUR
        # =========================================================

        if not supplier:

            QMessageBox.warning(
                self,
                "Champ requis",
                "Veuillez renseigner le nom du fournisseur.",
            )

            self.supplier_in.setFocus()

            return

        # =========================================================
        # VALIDATION QUANTITÉ
        # =========================================================

        if quantity <= 0:

            QMessageBox.warning(
                self,
                "Quantité invalide",
                "La quantité doit être supérieure à 0.",
            )

            self.qty_in.setFocus()

            return

        # =========================================================
        # VALIDATION PRIX
        # =========================================================

        if sale_price <= 0:

            QMessageBox.warning(
                self,
                "Prix invalide",
                "Veuillez renseigner un prix de vente supérieur à 0.",
            )

            self.price_in.setFocus()

            return

        # =========================================================
        # CONDITIONNEMENT
        # =========================================================

        boxes_per_carton = (
            self.boxes_per_carton_in.value()
        )

        plaquettes_per_box = (
            self.units_per_box_in.value()
        )

        if packaging == "Carton":

            if boxes_per_carton <= 0:

                QMessageBox.warning(
                    self,
                    "Conditionnement incomplet",
                    "Veuillez renseigner le nombre de boîtes dans le carton.",
                )

                self.boxes_per_carton_in.setFocus()

                return

            if plaquettes_per_box <= 0:

                QMessageBox.warning(
                    self,
                    "Conditionnement incomplet",
                    "Veuillez renseigner le nombre de plaquettes dans une boîte.",
                )

                self.units_per_box_in.setFocus()

                return

        # =========================================================
        # DATE EXPIRATION
        # =========================================================

        if expiry_date <= datetime.now().date():

            reply = QMessageBox.question(
                self,
                "Date d'expiration",
                "La date d'expiration est aujourd'hui "
                "ou déjà dépassée.\n\n"
                "Voulez-vous vraiment continuer ?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if (
                reply
                != QMessageBox.StandardButton.Yes
            ):
                return

        # =========================================================
        # STOCK
        # =========================================================

        units_per_package = (
            self.get_units_per_package(
                packaging
            )
        )

        stock_units = (
            quantity
            * units_per_package
        )

        prices = (
            self.calculate_prices(
                packaging,
                sale_price,
            )
        )

        session = SessionLocal()

        try:

            # =====================================================
            # MODIFICATION
            # =====================================================

            if self.selected_product_id:

                product = session.get(
                    Product,
                    self.selected_product_id,
                )

                if not product:

                    QMessageBox.warning(
                        self,
                        "Produit introuvable",
                        "Le produit sélectionné n'existe plus.",
                    )

                    self.clear_form()

                    return

                product.name = name

                product.packaging = packaging

                # -------------------------------------------------
                # FOURNISSEUR
                # -------------------------------------------------

                if hasattr(
                    product,
                    "supplier",
                ):
                    product.supplier = supplier

                # -------------------------------------------------
                # CONDITIONNEMENT
                # -------------------------------------------------

                if hasattr(
                    product,
                    "units_per_plaquette",
                ):
                    product.units_per_plaquette = 1

                if hasattr(
                    product,
                    "units_per_box",
                ):
                    product.units_per_box = (
                        plaquettes_per_box
                        if packaging in (
                            "Boîte",
                            "Carton",
                        )
                        else 1
                    )

                if hasattr(
                    product,
                    "boxes_per_carton",
                ):
                    product.boxes_per_carton = (
                        boxes_per_carton
                        if packaging == "Carton"
                        else 1
                    )

                # -------------------------------------------------
                # PRIX
                # -------------------------------------------------

                self.assign_product_prices(
                    product,
                    prices,
                )

                if hasattr(
                    product,
                    "price",
                ):
                    product.price = sale_price

                # -------------------------------------------------
                # EXPIRATION
                # -------------------------------------------------

                if hasattr(
                    product,
                    "expiry_date",
                ):
                    product.expiry_date = (
                        expiry_date
                    )

                session.commit()

                QMessageBox.information(
                    self,
                    "Succès",
                    f"Le produit « {name} » "
                    "a été modifié avec succès.",
                )

            # =====================================================
            # NOUVEAU PRODUIT
            # =====================================================

            else:

                product = Product(
                    name=name,
                    packaging=packaging,
                    price=sale_price,
                )

                # -------------------------------------------------
                # FOURNISSEUR
                # -------------------------------------------------

                if hasattr(
                    product,
                    "supplier",
                ):
                    product.supplier = supplier

                # -------------------------------------------------
                # CONDITIONNEMENT
                # -------------------------------------------------

                if hasattr(
                    product,
                    "units_per_plaquette",
                ):
                    product.units_per_plaquette = 1

                if hasattr(
                    product,
                    "units_per_box",
                ):
                    product.units_per_box = (
                        plaquettes_per_box
                        if packaging in (
                            "Boîte",
                            "Carton",
                        )
                        else 1
                    )

                if hasattr(
                    product,
                    "boxes_per_carton",
                ):
                    product.boxes_per_carton = (
                        boxes_per_carton
                        if packaging == "Carton"
                        else 1
                    )

                # -------------------------------------------------
                # PRIX
                # -------------------------------------------------

                self.assign_product_prices(
                    product,
                    prices,
                )

                # -------------------------------------------------
                # STOCK
                # -------------------------------------------------

                if hasattr(
                    product,
                    "quantity",
                ):
                    product.quantity = (
                        quantity
                    )

                if hasattr(
                    product,
                    "stock_units",
                ):
                    product.stock_units = (
                        stock_units
                    )

                # -------------------------------------------------
                # EXPIRATION
                # -------------------------------------------------

                if hasattr(
                    product,
                    "expiry_date",
                ):
                    product.expiry_date = (
                        expiry_date
                    )

                # -------------------------------------------------
                # LOT INTERNE
                # -------------------------------------------------

                generated_batch_number = (
                    "AUTO-"
                    + datetime.now().strftime(
                        "%Y%m%d%H%M%S%f"
                    )
                )

                if hasattr(
                    product,
                    "batch_number",
                ):
                    product.batch_number = (
                        generated_batch_number
                    )

                session.add(product)

                session.flush()

                # -------------------------------------------------
                # PRODUCT BATCH
                # -------------------------------------------------

                batch = ProductBatch(
                    product_id=product.id,
                    batch_number=(
                        generated_batch_number
                    ),
                    expiry_date=expiry_date,
                    stock_units=stock_units,
                    purchase_price=0,
                    supplier=supplier,
                )

                session.add(batch)

                session.commit()

                # -------------------------------------------------
                # MESSAGE
                # -------------------------------------------------

                QMessageBox.information(
                    self,
                    "Produit ajouté",
                    f"Le produit « {name} » a été ajouté avec succès.\n\n"
                    f"Fournisseur : {supplier}\n"
                    f"Condition : {packaging}\n"
                    f"Quantité : {quantity}\n"
                    f"Prix de vente : {sale_price:,.2f} CDF\n"
                    f"Expiration : {expiry_date.strftime('%d/%m/%Y')}",
                )

            self.clear_form()

            self.refresh()

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                "Impossible d'enregistrer le produit.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:

            session.close()

    # =============================================================
    # DATE
    # =============================================================

    def get_expiry_date(self):

        qdate = (
            self.expiry_in.date()
        )

        try:

            return qdate.toPython()

        except AttributeError:

            return datetime(
                qdate.year(),
                qdate.month(),
                qdate.day(),
            ).date()

    # =============================================================
    # MODIFICATION
    # =============================================================

    def load_for_edit(
        self,
        product_id,
    ):

        session = SessionLocal()

        try:

            product = session.get(
                Product,
                product_id,
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Introuvable",
                    "Ce produit n'existe plus.",
                )

                return

            self.selected_product_id = (
                product.id
            )

            # -----------------------------------------------------
            # NOM
            # -----------------------------------------------------

            self.name_in.setText(
                getattr(
                    product,
                    "name",
                    "",
                )
                or ""
            )

            # -----------------------------------------------------
            # FOURNISSEUR
            # -----------------------------------------------------

            self.supplier_in.setText(
                getattr(
                    product,
                    "supplier",
                    "",
                )
                or ""
            )

            # -----------------------------------------------------
            # CONDITION
            # -----------------------------------------------------

            packaging = (
                getattr(
                    product,
                    "packaging",
                    "Plaquette",
                )
                or "Plaquette"
            )

            if packaging not in PACKAGING_OPTIONS:

                packaging = (
                    "Autre produit"
                )

            index = (
                self.packaging_in.findText(
                    packaging
                )
            )

            if index < 0:
                index = 0

            self.packaging_in.setCurrentIndex(
                index
            )

            # -----------------------------------------------------
            # BOÎTES / CARTON
            # -----------------------------------------------------

            self.boxes_per_carton_in.setValue(
                max(
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
            )

            # -----------------------------------------------------
            # PLAQUETTES / BOÎTE
            # -----------------------------------------------------

            self.units_per_box_in.setValue(
                max(
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
            )

            # -----------------------------------------------------
            # PRIX
            # -----------------------------------------------------

            if packaging == "Carton":

                price = getattr(
                    product,
                    "price_per_plaquette",
                    getattr(
                        product,
                        "price",
                        0,
                    ),
                ) or 0

            elif packaging == "Boîte":

                price = getattr(
                    product,
                    "price_per_box",
                    getattr(
                        product,
                        "price",
                        0,
                    ),
                ) or 0

            else:

                price = getattr(
                    product,
                    "price_per_plaquette",
                    getattr(
                        product,
                        "price",
                        0,
                    ),
                ) or 0

            self.price_in.setValue(
                float(price)
            )

            # -----------------------------------------------------
            # EXPIRATION
            # -----------------------------------------------------

            expiry_date = getattr(
                product,
                "expiry_date",
                None,
            )

            batches = (
                session.query(
                    ProductBatch
                )
                .filter(
                    ProductBatch.product_id
                    == product.id
                )
                .order_by(
                    ProductBatch.expiry_date.asc()
                )
                .all()
            )

            if batches:

                batch = batches[0]

                if batch.expiry_date:
                    expiry_date = (
                        batch.expiry_date
                    )

            if expiry_date:

                self.expiry_in.setDate(
                    QDate(
                        expiry_date.year,
                        expiry_date.month,
                        expiry_date.day,
                    )
                )

            self.update_packaging_fields(
                packaging
            )

            # -----------------------------------------------------
            # BOUTON
            # -----------------------------------------------------

            self.btn_save.setText(
                "✓ Enregistrer les modifications"
            )

            self.btn_save.setProperty(
                "class",
                "btn-success",
            )

            self.btn_save.style().unpolish(
                self.btn_save
            )

            self.btn_save.style().polish(
                self.btn_save
            )

            self.btn_cancel.setVisible(
                True
            )

            self.scroll_area.verticalScrollBar().setValue(
                0
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de charger le produit.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:

            session.close()

    # =============================================================
    # SUPPRESSION
    # =============================================================

    def delete_product(
        self,
        product_id,
    ):

        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer ce produit ?\n\n"
            "Tous ses lots seront également supprimés.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            reply
            != QMessageBox.StandardButton.Yes
        ):
            return

        session = SessionLocal()

        try:

            product = session.get(
                Product,
                product_id,
            )

            if not product:

                self.refresh()

                return

            batches = (
                session.query(
                    ProductBatch
                )
                .filter(
                    ProductBatch.product_id
                    == product.id
                )
                .all()
            )

            for batch in batches:
                session.delete(
                    batch
                )

            session.delete(
                product
            )

            session.commit()

            QMessageBox.information(
                self,
                "Produit supprimé",
                "Le produit et ses lots ont été supprimés avec succès.",
            )

            self.refresh()

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de supprimer le produit.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:

            session.close()

    # =============================================================
    # RÉINITIALISATION
    # =============================================================

    def clear_form(self):

        self.selected_product_id = None

        self.name_in.clear()

        self.supplier_in.clear()

        self.packaging_in.setCurrentIndex(
            0
        )

        self.boxes_per_carton_in.setValue(
            1
        )

        self.units_per_box_in.setValue(
            1
        )

        self.qty_in.setValue(
            1
        )

        self.price_in.setValue(
            0.01
        )

        self.expiry_in.setDate(
            QDate.currentDate().addYears(
                1
            )
        )

        self.btn_save.setText(
            "➕ Ajouter le produit"
        )

        self.btn_save.setProperty(
            "class",
            "btn-primary",
        )

        self.btn_save.style().unpolish(
            self.btn_save
        )

        self.btn_save.style().polish(
            self.btn_save
        )

        self.btn_cancel.setVisible(
            False
        )

        self.update_packaging_fields(
            self.packaging_in.currentText()
        )

    # =============================================================
    # TABLEAU
    # =============================================================

    def refresh(self):

        session = SessionLocal()

        try:

            products = (
                session.query(Product)
                .order_by(
                    Product.id.desc()
                )
                .all()
            )

            self.table.setRowCount(
                0
            )

            for product in products:

                batches = (
                    session.query(
                        ProductBatch
                    )
                    .filter(
                        ProductBatch.product_id
                        == product.id
                    )
                    .order_by(
                        ProductBatch.expiry_date.asc()
                    )
                    .all()
                )

                if not batches:

                    self.add_product_row(
                        product,
                        None,
                    )

                else:

                    for batch in batches:

                        self.add_product_row(
                            product,
                            batch,
                        )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de charger les produits.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:

            session.close()

    # =============================================================
    # AJOUT LIGNE TABLEAU
    # =============================================================

    def add_product_row(
        self,
        product,
        batch,
    ):

        row = (
            self.table.rowCount()
        )

        self.table.insertRow(
            row
        )

        # ---------------------------------------------------------
        # PRODUIT
        # ---------------------------------------------------------

        self.table.setItem(
            row,
            0,
            QTableWidgetItem(
                getattr(
                    product,
                    "name",
                    "",
                )
                or ""
            ),
        )

        # ---------------------------------------------------------
        # FOURNISSEUR
        # ---------------------------------------------------------

        self.table.setItem(
            row,
            1,
            QTableWidgetItem(
                getattr(
                    product,
                    "supplier",
                    "",
                )
                or ""
            ),
        )

        # ---------------------------------------------------------
        # CONDITION
        # ---------------------------------------------------------

        packaging = (
            getattr(
                product,
                "packaging",
                "Autre produit",
            )
            or "Autre produit"
        )

        packaging_item = (
            QTableWidgetItem(
                packaging
            )
        )

        packaging_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            2,
            packaging_item,
        )

        # ---------------------------------------------------------
        # STOCK
        # ---------------------------------------------------------

        stock_units = int(
            (
                batch.stock_units
                if batch is not None
                else getattr(
                    product,
                    "stock_units",
                    0,
                )
            )
            or 0
        )

        stock_item = (
            QTableWidgetItem(
                self.format_stock(
                    product,
                    stock_units,
                )
            )
        )

        stock_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            3,
            stock_item,
        )

        # ---------------------------------------------------------
        # PRIX UNITÉ
        # ---------------------------------------------------------

        price_unite = float(
            getattr(
                product,
                "price_per_comprime",
                0,
            )
            or 0
        )

        if price_unite <= 0:

            price_unite = float(
                getattr(
                    product,
                    "price",
                    0,
                )
                or 0
            )

        self.set_price_item(
            row,
            4,
            price_unite,
        )

        # ---------------------------------------------------------
        # PRIX PLAQUETTE
        # ---------------------------------------------------------

        self.set_price_item(
            row,
            5,
            float(
                getattr(
                    product,
                    "price_per_plaquette",
                    0,
                )
                or 0
            ),
        )

        # ---------------------------------------------------------
        # PRIX BOÎTE
        # ---------------------------------------------------------

        self.set_price_item(
            row,
            6,
            float(
                getattr(
                    product,
                    "price_per_box",
                    0,
                )
                or 0
            ),
        )

        # ---------------------------------------------------------
        # PRIX CARTON
        # ---------------------------------------------------------

        self.set_price_item(
            row,
            7,
            float(
                getattr(
                    product,
                    "price_per_carton",
                    0,
                )
                or 0
            ),
        )

        # ---------------------------------------------------------
        # EXPIRATION
        # ---------------------------------------------------------

        expiry_date = (
            batch.expiry_date
            if batch is not None
            else getattr(
                product,
                "expiry_date",
                None,
            )
        )

        if expiry_date:

            expiry_text = (
                expiry_date.strftime(
                    "%d/%m/%Y"
                )
            )

            expiry_item = (
                QTableWidgetItem(
                    expiry_text
                )
            )

            today = (
                datetime.now().date()
            )

            if expiry_date < today:

                expiry_item.setText(
                    f"🔴 {expiry_text}"
                )

            elif (
                expiry_date - today
            ).days <= 90:

                expiry_item.setText(
                    f"🟠 {expiry_text}"
                )

            else:

                expiry_item.setText(
                    f"🟢 {expiry_text}"
                )

        else:

            expiry_item = (
                QTableWidgetItem(
                    "⚠️ N/A"
                )
            )

        expiry_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            8,
            expiry_item,
        )

    # =============================================================
    # PRIX TABLEAU
    # =============================================================

    def set_price_item(
        self,
        row,
        column,
        price,
    ):

        item = QTableWidgetItem(
            f"{price:,.2f} CDF"
        )

        item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            column,
            item,
        )

    # =============================================================
    # DOUBLE CLIC
    # =============================================================

    def handle_table_double_click(
        self,
        item,
    ):

        row = item.row()

        if row < 0:
            return

        name_item = (
            self.table.item(
                row,
                0,
            )
        )

        if not name_item:
            return

        name = (
            name_item.text().strip()
        )

        if not name:
            return

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.name == name
                )
                .order_by(
                    Product.id.desc()
                )
                .first()
            )

            if product:

                self.load_for_edit(
                    product.id
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'ouvrir le produit.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:

            session.close()