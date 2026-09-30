# ui/products.py

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
# CONDITIONNEMENTS
# =============================================================

PACKAGING_OPTIONS = [
    "Comprimé",
    "Plaquette",
    "Boîte",
    "Carton",
]


class ProductsPage(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_product_id = None

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

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # =========================================================
        # CONTENU
        # =========================================================

        self.content_widget = QWidget()

        self.content_widget.setObjectName(
            "productsContent"
        )

        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        self.layout = QVBoxLayout(
            self.content_widget
        )

        self.layout.setContentsMargins(
            24,
            24,
            24,
            40
        )

        self.layout.setSpacing(18)

        self.scroll_area.setWidget(
            self.content_widget
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # =========================================================
        # TITRE
        # =========================================================

        title = QLabel(
            "💊 Gestion des produits pharmaceutiques"
        )

        title.setObjectName(
            "pageTitle"
        )

        self.layout.addWidget(
            title
        )

        # =========================================================
        # SOUS-TITRE
        # =========================================================

        subtitle = QLabel(
            "Gérez les médicaments, leurs conditionnements, "
            "leurs lots, leurs prix et leurs dates d'expiration."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(True)

        self.layout.addWidget(
            subtitle
        )

        # =========================================================
        # CARTE FORMULAIRE
        # =========================================================

        form_card = QFrame()

        form_card.setObjectName(
            "formCard"
        )

        form_card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        form = QFormLayout(
            form_card
        )

        form.setContentsMargins(
            22,
            22,
            22,
            22
        )

        form.setSpacing(
            14
        )

        # =========================================================
        # NOM
        # =========================================================

        self.name_in = QLineEdit()

        self.name_in.setPlaceholderText(
            "Ex : Paracétamol 500 mg"
        )

        self.name_in.setMinimumHeight(
            42
        )

        # =========================================================
        # NUMÉRO DE LOT
        # =========================================================

        self.batch_in = QLineEdit()

        self.batch_in.setPlaceholderText(
            "Ex : PARA-2026-001"
        )

        self.batch_in.setMinimumHeight(
            42
        )

        # =========================================================
        # FOURNISSEUR
        # =========================================================

        self.supplier_in = QLineEdit()

        self.supplier_in.setPlaceholderText(
            "Ex : Pharmadistribution"
        )

        self.supplier_in.setMinimumHeight(
            42
        )

        # =========================================================
        # CONDITIONNEMENT PRINCIPAL
        # =========================================================

        self.packaging_in = QComboBox()

        self.packaging_in.addItems(
            PACKAGING_OPTIONS
        )

        self.packaging_in.setMinimumHeight(
            42
        )

        self.packaging_in.currentTextChanged.connect(
            self.update_price_label
        )

        # =========================================================
        # COMPRIMÉS PAR PLAQUETTE
        # =========================================================

        self.units_per_plaquette_in = QSpinBox()

        self.units_per_plaquette_in.setRange(
            1,
            1000
        )

        self.units_per_plaquette_in.setValue(
            10
        )

        self.units_per_plaquette_in.setMinimumHeight(
            42
        )

        # =========================================================
        # PLAQUETTES PAR BOÎTE
        # =========================================================

        self.units_per_box_in = QSpinBox()

        self.units_per_box_in.setRange(
            1,
            1000
        )

        self.units_per_box_in.setValue(
            10
        )

        self.units_per_box_in.setMinimumHeight(
            42
        )

        # =========================================================
        # BOÎTES PAR CARTON
        # =========================================================

        self.boxes_per_carton_in = QSpinBox()

        self.boxes_per_carton_in.setRange(
            1,
            1000
        )

        self.boxes_per_carton_in.setValue(
            10
        )

        self.boxes_per_carton_in.setMinimumHeight(
            42
        )

        # =========================================================
        # QUANTITÉ INITIALE
        # =========================================================

        self.qty_in = QSpinBox()

        self.qty_in.setRange(
            0,
            1000000
        )

        self.qty_in.setValue(
            1
        )

        self.qty_in.setMinimumHeight(
            42
        )

        # =========================================================
        # PRIX DU CONDITIONNEMENT
        # =========================================================

        self.price_in = QDoubleSpinBox()

        self.price_in.setRange(
            0,
            1000000000
        )

        self.price_in.setDecimals(
            2
        )

        self.price_in.setSuffix(
            " CDF"
        )

        self.price_in.setMinimumHeight(
            42
        )

        # =========================================================
        # DATE EXPIRATION
        # =========================================================

        self.expiry_in = QDateEdit()

        self.expiry_in.setCalendarPopup(
            True
        )

        self.expiry_in.setDate(
            QDate.currentDate().addYears(1)
        )

        self.expiry_in.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.expiry_in.setMinimumHeight(
            42
        )

        # =========================================================
        # INFORMATION CONVERSION
        # =========================================================

        self.conversion_label = QLabel()

        self.conversion_label.setObjectName(
            "conversionLabel"
        )

        self.conversion_label.setWordWrap(
            True
        )

        self.update_conversion_label()

        self.units_per_plaquette_in.valueChanged.connect(
            self.update_conversion_label
        )

        self.units_per_box_in.valueChanged.connect(
            self.update_conversion_label
        )

        self.boxes_per_carton_in.valueChanged.connect(
            self.update_conversion_label
        )

        # =========================================================
        # CHAMPS
        # =========================================================

        form.addRow(
            "Nom du médicament * :",
            self.name_in
        )

        form.addRow(
            "Numéro de lot * :",
            self.batch_in
        )

        form.addRow(
            "Fournisseur :",
            self.supplier_in
        )

        form.addRow(
            "Conditionnement initial * :",
            self.packaging_in
        )

        form.addRow(
            "Comprimés / plaquette :",
            self.units_per_plaquette_in
        )

        form.addRow(
            "Plaquettes / boîte :",
            self.units_per_box_in
        )

        form.addRow(
            "Boîtes / carton :",
            self.boxes_per_carton_in
        )

        form.addRow(
            "Quantité initiale * :",
            self.qty_in
        )

        self.price_label = QLabel(
            "Prix du conditionnement * :"
        )

        form.addRow(
            self.price_label,
            self.price_in
        )

        form.addRow(
            "Date d'expiration * :",
            self.expiry_in
        )

        form.addRow(
            "",
            self.conversion_label
        )

        # =========================================================
        # BOUTONS
        # =========================================================

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            10
        )

        # ---------------------------------------------------------
        # ENREGISTRER
        # ---------------------------------------------------------

        self.btn_save = QPushButton(
            "➕ Ajouter le produit"
        )

        self.btn_save.setProperty(
            "class",
            "btn-primary"
        )

        self.btn_save.setMinimumHeight(
            44
        )

        self.btn_save.clicked.connect(
            self.save_product
        )

        # ---------------------------------------------------------
        # ANNULER
        # ---------------------------------------------------------

        self.btn_cancel = QPushButton(
            "↩ Annuler / Réinitialiser"
        )

        self.btn_cancel.setMinimumHeight(
            44
        )

        self.btn_cancel.clicked.connect(
            self.clear_form
        )

        self.btn_cancel.setVisible(
            False
        )

        buttons_layout.addWidget(
            self.btn_save
        )

        buttons_layout.addWidget(
            self.btn_cancel
        )

        form.addRow(
            "",
            buttons_layout
        )

        self.layout.addWidget(
            form_card
        )

        # =========================================================
        # TITRE TABLEAU
        # =========================================================

        table_header = QHBoxLayout()

        table_title_box = QVBoxLayout()

        table_title = QLabel(
            "📋 Produits et lots enregistrés"
        )

        table_title.setObjectName(
            "tableTitle"
        )

        table_subtitle = QLabel(
            "Chaque lot possède sa propre date d'expiration."
        )

        table_subtitle.setObjectName(
            "tableSubtitle"
        )

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
        # TABLEAU
        # =========================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            9
        )

        self.table.setHorizontalHeaderLabels([
            "Médicament",
            "Lot",
            "Conditionnement",
            "Stock",
            "Prix comprimé",
            "Prix plaquette",
            "Prix boîte",
            "Prix carton",
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

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setWordWrap(
            False
        )

        self.table.setMinimumHeight(
            400
        )

        self.table.setMaximumHeight(
            600
        )

        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # =========================================================
        # COLONNES
        # =========================================================

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        for column in range(1, 9):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents
            )

        self.table.verticalHeader().setDefaultSectionSize(
            48
        )

        self.layout.addWidget(
            self.table
        )

        # =========================================================
        # INFORMATION
        # =========================================================

        info = QLabel(
            "💡 Le stock est enregistré en unité de base "
            "(comprimé). Les ventes peuvent ensuite être faites "
            "en comprimés, plaquettes, boîtes ou cartons."
        )

        info.setObjectName(
            "infoLabel"
        )

        info.setWordWrap(
            True
        )

        self.layout.addWidget(
            info
        )

        self.layout.addSpacing(
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

            QComboBox {
                min-height: 24px;
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

            QPushButton[class="btn-danger"] {
                background: #D92D20;
            }

            QPushButton[class="btn-danger"]:hover {
                background: #B42318;
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
    # CALCULER UNITÉS PAR CONDITIONNEMENT
    # =============================================================

    def get_units_per_package(
        self,
        packaging=None
    ):

        if packaging is None:
            packaging = self.packaging_in.currentText()

        tablets_per_blister = max(
            1,
            self.units_per_plaquette_in.value()
        )

        blisters_per_box = max(
            1,
            self.units_per_box_in.value()
        )

        boxes_per_carton = max(
            1,
            self.boxes_per_carton_in.value()
        )

        if packaging == "Comprimé":
            return 1

        if packaging == "Plaquette":
            return tablets_per_blister

        if packaging == "Boîte":
            return (
                tablets_per_blister
                * blisters_per_box
            )

        if packaging == "Carton":
            return (
                tablets_per_blister
                * blisters_per_box
                * boxes_per_carton
            )

        return 1

    # =============================================================
    # FORMAT STOCK
    # =============================================================

    def format_stock(
        self,
        product,
        stock_units
    ):

        stock_units = int(
            stock_units or 0
        )

        tablets_per_blister = max(
            1,
            int(
                getattr(
                    product,
                    "units_per_plaquette",
                    1
                ) or 1
            )
        )

        blisters_per_box = max(
            1,
            int(
                getattr(
                    product,
                    "units_per_box",
                    1
                ) or 1
            )
        )

        boxes_per_carton = max(
            1,
            int(
                getattr(
                    product,
                    "boxes_per_carton",
                    1
                ) or 1
            )
        )

        tablets_per_box = (
            tablets_per_blister
            * blisters_per_box
        )

        tablets_per_carton = (
            tablets_per_box
            * boxes_per_carton
        )

        cartons = (
            stock_units
            // tablets_per_carton
        )

        remainder = (
            stock_units
            % tablets_per_carton
        )

        boxes = (
            remainder
            // tablets_per_box
        )

        remainder %= tablets_per_box

        blisters = (
            remainder
            // tablets_per_blister
        )

        tablets = (
            remainder
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

    # =============================================================
    # MISE À JOUR INFORMATION CONVERSION
    # =============================================================

    def update_conversion_label(self):

        tablets_per_blister = (
            self.units_per_plaquette_in.value()
        )

        blisters_per_box = (
            self.units_per_box_in.value()
        )

        boxes_per_carton = (
            self.boxes_per_carton_in.value()
        )

        tablets_per_box = (
            tablets_per_blister
            * blisters_per_box
        )

        tablets_per_carton = (
            tablets_per_box
            * boxes_per_carton
        )

        self.conversion_label.setText(
            "📦 Conversion : "
            f"1 plaquette = {tablets_per_blister} comprimés   |   "
            f"1 boîte = {blisters_per_box} plaquette(s) = "
            f"{tablets_per_box} comprimés   |   "
            f"1 carton = {boxes_per_carton} boîte(s) = "
            f"{tablets_per_carton} comprimés"
        )

    # =============================================================
    # MISE À JOUR LABEL PRIX
    # =============================================================

    def update_price_label(
        self,
        packaging
    ):

        self.price_label.setText(
            f"Prix de {packaging.lower()} * :"
        )

    # =============================================================
    # CONVERTIR DATE
    # =============================================================

    def get_expiry_date(self):

        qdate = self.expiry_in.date()

        try:
            return qdate.toPython()

        except AttributeError:

            return datetime(
                qdate.year(),
                qdate.month(),
                qdate.day
            ).date()

    # =============================================================
    # CALCUL DES PRIX
    # =============================================================

    def calculate_prices(
        self,
        packaging,
        entered_price
    ):

        tablets_per_blister = max(
            1,
            self.units_per_plaquette_in.value()
        )

        blisters_per_box = max(
            1,
            self.units_per_box_in.value()
        )

        boxes_per_carton = max(
            1,
            self.boxes_per_carton_in.value()
        )

        tablets_per_box = (
            tablets_per_blister
            * blisters_per_box
        )

        tablets_per_carton = (
            tablets_per_box
            * boxes_per_carton
        )

        if packaging == "Comprimé":

            price_per_comprime = entered_price

            price_per_plaquette = (
                price_per_comprime
                * tablets_per_blister
            )

            price_per_box = (
                price_per_plaquette
                * blisters_per_box
            )

            price_per_carton = (
                price_per_box
                * boxes_per_carton
            )

        elif packaging == "Plaquette":

            price_per_plaquette = entered_price

            price_per_comprime = (
                price_per_plaquette
                / tablets_per_blister
            )

            price_per_box = (
                price_per_plaquette
                * blisters_per_box
            )

            price_per_carton = (
                price_per_box
                * boxes_per_carton
            )

        elif packaging == "Boîte":

            price_per_box = entered_price

            price_per_plaquette = (
                price_per_box
                / blisters_per_box
            )

            price_per_comprime = (
                price_per_plaquette
                / tablets_per_blister
            )

            price_per_carton = (
                price_per_box
                * boxes_per_carton
            )

        else:

            price_per_carton = entered_price

            price_per_box = (
                price_per_carton
                / boxes_per_carton
            )

            price_per_plaquette = (
                price_per_box
                / blisters_per_box
            )

            price_per_comprime = (
                price_per_plaquette
                / tablets_per_blister
            )

        return {
            "price_per_comprime": price_per_comprime,
            "price_per_plaquette": price_per_plaquette,
            "price_per_box": price_per_box,
            "price_per_carton": price_per_carton,
        }

    # =============================================================
    # ENREGISTRER
    # =============================================================

    def save_product(self):

        name = self.name_in.text().strip()

        batch_number = self.batch_in.text().strip()

        supplier = self.supplier_in.text().strip()

        packaging = (
            self.packaging_in.currentText().strip()
        )

        quantity = self.qty_in.value()

        entered_price = self.price_in.value()

        expiry_date = self.get_expiry_date()

        # =========================================================
        # VALIDATION NOM
        # =========================================================

        if not name:

            QMessageBox.warning(
                self,
                "Champ requis",
                "Veuillez renseigner le nom du médicament."
            )

            self.name_in.setFocus()

            return

        # =========================================================
        # VALIDATION LOT
        # =========================================================

        if not batch_number:

            QMessageBox.warning(
                self,
                "Numéro de lot requis",
                "Chaque médicament doit avoir un numéro de lot."
            )

            self.batch_in.setFocus()

            return

        # =========================================================
        # VALIDATION QUANTITÉ
        # =========================================================

        if quantity < 0:

            QMessageBox.warning(
                self,
                "Quantité invalide",
                "La quantité ne peut pas être négative."
            )

            return

        # =========================================================
        # VALIDATION PRIX
        # =========================================================

        if entered_price <= 0:

            QMessageBox.warning(
                self,
                "Prix invalide",
                "Veuillez renseigner un prix supérieur à 0."
            )

            self.price_in.setFocus()

            return

        # =========================================================
        # VALIDATION EXPIRATION
        # =========================================================

        if expiry_date <= datetime.now().date():

            reply = QMessageBox.question(
                self,
                "Date d'expiration",
                (
                    "La date d'expiration est aujourd'hui "
                    "ou déjà dépassée.\n\n"
                    "Voulez-vous vraiment continuer ?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # =========================================================
        # CONVERSIONS
        # =========================================================

        units_per_plaquette = (
            self.units_per_plaquette_in.value()
        )

        units_per_box = (
            self.units_per_box_in.value()
        )

        boxes_per_carton = (
            self.boxes_per_carton_in.value()
        )

        units_per_package = (
            self.get_units_per_package(
                packaging
            )
        )

        stock_units = (
            quantity
            * units_per_package
        )

        prices = self.calculate_prices(
            packaging,
            entered_price
        )

        # =========================================================
        # DATABASE
        # =========================================================

        session = SessionLocal()

        try:

            # =====================================================
            # MODIFICATION
            # =====================================================

            if self.selected_product_id:

                product = session.get(
                    Product,
                    self.selected_product_id
                )

                if not product:

                    QMessageBox.warning(
                        self,
                        "Produit introuvable",
                        "Le produit sélectionné n'existe plus."
                    )

                    self.clear_form()

                    return

                # -------------------------------------------------
                # MODIFIER LES INFORMATIONS DU PRODUIT
                # -------------------------------------------------

                product.name = name
                product.packaging = packaging

                # Configuration du conditionnement
                if hasattr(
                    product,
                    "units_per_plaquette"
                ):
                    product.units_per_plaquette = (
                        units_per_plaquette
                    )

                if hasattr(
                    product,
                    "units_per_box"
                ):
                    product.units_per_box = (
                        units_per_box
                    )

                if hasattr(
                    product,
                    "boxes_per_carton"
                ):
                    product.boxes_per_carton = (
                        boxes_per_carton
                    )

                # Prix
                if hasattr(
                    product,
                    "price_per_comprime"
                ):
                    product.price_per_comprime = (
                        prices["price_per_comprime"]
                    )

                if hasattr(
                    product,
                    "price_per_plaquette"
                ):
                    product.price_per_plaquette = (
                        prices["price_per_plaquette"]
                    )

                if hasattr(
                    product,
                    "price_per_box"
                ):
                    product.price_per_box = (
                        prices["price_per_box"]
                    )

                if hasattr(
                    product,
                    "price_per_carton"
                ):
                    product.price_per_carton = (
                        prices["price_per_carton"]
                    )

                # Prix principal
                product.price = entered_price

                # -------------------------------------------------
                # NE PAS MODIFIER DIRECTEMENT LE STOCK
                # -------------------------------------------------
                #
                # Le stock réel appartient maintenant aux lots.
                #
                # Une modification du produit ne doit pas écraser
                # les stocks existants.
                #
                # Si l'utilisateur veut ajouter du stock,
                # cela doit passer par les achats / entrées de stock.
                # -------------------------------------------------

                session.commit()

                QMessageBox.information(
                    self,
                    "Succès",
                    (
                        "Les informations du médicament "
                        "ont été modifiées avec succès.\n\n"
                        "Le stock des lots existants "
                        "n'a pas été modifié."
                    )
                )

            # =====================================================
            # NOUVEAU PRODUIT
            # =====================================================

            else:

                product = Product(
                    name=name,
                    packaging=packaging,
                    price=entered_price,
                )

                # -------------------------------------------------
                # CONDITIONNEMENT
                # -------------------------------------------------

                if hasattr(
                    product,
                    "units_per_plaquette"
                ):
                    product.units_per_plaquette = (
                        units_per_plaquette
                    )

                if hasattr(
                    product,
                    "units_per_box"
                ):
                    product.units_per_box = (
                        units_per_box
                    )

                if hasattr(
                    product,
                    "boxes_per_carton"
                ):
                    product.boxes_per_carton = (
                        boxes_per_carton
                    )

                # -------------------------------------------------
                # PRIX
                # -------------------------------------------------

                if hasattr(
                    product,
                    "price_per_comprime"
                ):
                    product.price_per_comprime = (
                        prices["price_per_comprime"]
                    )

                if hasattr(
                    product,
                    "price_per_plaquette"
                ):
                    product.price_per_plaquette = (
                        prices["price_per_plaquette"]
                    )

                if hasattr(
                    product,
                    "price_per_box"
                ):
                    product.price_per_box = (
                        prices["price_per_box"]
                    )

                if hasattr(
                    product,
                    "price_per_carton"
                ):
                    product.price_per_carton = (
                        prices["price_per_carton"]
                    )

                # -------------------------------------------------
                # COMPATIBILITÉ ANCIENNES COLONNES
                # -------------------------------------------------

                if hasattr(
                    product,
                    "quantity"
                ):
                    product.quantity = quantity

                if hasattr(
                    product,
                    "stock_units"
                ):
                    product.stock_units = stock_units

                if hasattr(
                    product,
                    "expiry_date"
                ):
                    product.expiry_date = expiry_date

                if hasattr(
                    product,
                    "batch_number"
                ):
                    product.batch_number = batch_number

                if hasattr(
                    product,
                    "supplier"
                ):
                    product.supplier = supplier

                session.add(
                    product
                )

                session.flush()

                # =================================================
                # CRÉER LE LOT
                # =================================================

                batch = ProductBatch(
                    product_id=product.id,
                    batch_number=batch_number,
                    expiry_date=expiry_date,
                    stock_units=stock_units,
                    purchase_price=0,
                    supplier=supplier or None,
                )

                session.add(
                    batch
                )

                session.commit()

                QMessageBox.information(
                    self,
                    "Produit ajouté",
                    (
                        f"Le médicament « {name} » a été ajouté.\n\n"
                        f"Lot : {batch_number}\n"
                        f"Stock : {self.format_stock(product, stock_units)}\n"
                        f"Expiration : "
                        f"{expiry_date.strftime('%d/%m/%Y')}"
                    )
                )

            # =====================================================
            # RESET
            # =====================================================

            self.clear_form()

            self.refresh()

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                (
                    "Impossible d'enregistrer le produit.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()

    # =============================================================
    # CHARGER POUR MODIFICATION
    # =============================================================

    def load_for_edit(
        self,
        product_id
    ):

        session = SessionLocal()

        try:

            product = session.get(
                Product,
                product_id
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Introuvable",
                    "Ce produit n'existe plus."
                )

                return

            self.selected_product_id = product.id

            # =====================================================
            # NOM
            # =====================================================

            self.name_in.setText(
                product.name or ""
            )

            # =====================================================
            # CONDITIONNEMENT
            # =====================================================

            packaging = getattr(
                product,
                "packaging",
                "Boîte"
            )

            index = self.packaging_in.findText(
                packaging
            )

            if index >= 0:

                self.packaging_in.setCurrentIndex(
                    index
                )

            # =====================================================
            # CONFIGURATION
            # =====================================================

            self.units_per_plaquette_in.setValue(
                max(
                    1,
                    int(
                        getattr(
                            product,
                            "units_per_plaquette",
                            10
                        ) or 10
                    )
                )
            )

            self.units_per_box_in.setValue(
                max(
                    1,
                    int(
                        getattr(
                            product,
                            "units_per_box",
                            10
                        ) or 10
                    )
                )
            )

            self.boxes_per_carton_in.setValue(
                max(
                    1,
                    int(
                        getattr(
                            product,
                            "boxes_per_carton",
                            10
                        ) or 10
                    )
                )
            )

            # =====================================================
            # LOT
            # =====================================================

            batch_number = getattr(
                product,
                "batch_number",
                ""
            )

            # Chercher le premier lot
            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id == product.id
                )
                .order_by(
                    ProductBatch.id.desc()
                )
                .all()
            )

            if batches:

                batch = batches[0]

                batch_number = (
                    batch.batch_number
                    or batch_number
                    or ""
                )

                if batch.expiry_date:

                    self.expiry_in.setDate(
                        QDate(
                            batch.expiry_date.year,
                            batch.expiry_date.month,
                            batch.expiry_date.day
                        )
                    )

                self.supplier_in.setText(
                    batch.supplier or ""
                )

            else:

                self.supplier_in.setText(
                    getattr(
                        product,
                        "supplier",
                        ""
                    ) or ""
                )

                if product.expiry_date:

                    self.expiry_in.setDate(
                        QDate(
                            product.expiry_date.year,
                            product.expiry_date.month,
                            product.expiry_date.day
                        )
                    )

            self.batch_in.setText(
                batch_number
            )

            # =====================================================
            # PRIX
            # =====================================================

            price = getattr(
                product,
                "price",
                0
            ) or 0

            self.price_in.setValue(
                float(price)
            )

            # =====================================================
            # QUANTITÉ
            # =====================================================
            #
            # Pour une modification, on ne recharge pas le stock
            # comme une nouvelle entrée.
            #
            # On affiche 0 afin d'éviter de réinjecter le stock
            # existant si l'utilisateur sauvegarde.
            # =====================================================

            self.qty_in.setValue(
                0
            )

            # =====================================================
            # BOUTON
            # =====================================================

            self.btn_save.setText(
                "✓ Enregistrer les modifications"
            )

            self.btn_save.setProperty(
                "class",
                "btn-success"
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

            # =====================================================
            # REMONTER
            # =====================================================

            self.scroll_area.verticalScrollBar().setValue(
                0
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger le produit.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()

    # =============================================================
    # SUPPRIMER
    # =============================================================

    def delete_product(
        self,
        product_id
    ):

        reply = QMessageBox.question(
            self,
            "Confirmation",
            (
                "Êtes-vous sûr de vouloir supprimer ce médicament ?\n\n"
                "Tous ses lots seront également supprimés.\n\n"
                "Cette opération peut être irréversible."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:

            return

        session = SessionLocal()

        try:

            product = session.get(
                Product,
                product_id
            )

            if not product:

                QMessageBox.warning(
                    self,
                    "Introuvable",
                    "Le produit n'existe plus."
                )

                self.refresh()

                return

            # =====================================================
            # SUPPRESSION DES LOTS
            # =====================================================

            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id == product.id
                )
                .all()
            )

            for batch in batches:

                session.delete(
                    batch
                )

            # =====================================================
            # SUPPRESSION PRODUIT
            # =====================================================

            session.delete(
                product
            )

            session.commit()

            QMessageBox.information(
                self,
                "Produit supprimé",
                (
                    "Le médicament et ses lots "
                    "ont été supprimés avec succès."
                )
            )

            self.refresh()

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de supprimer le produit.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()

    # =============================================================
    # RESET
    # =============================================================

    def clear_form(self):

        self.selected_product_id = None

        # Nom
        self.name_in.clear()

        # Lot
        self.batch_in.clear()

        # Fournisseur
        self.supplier_in.clear()

        # Conditionnement
        self.packaging_in.setCurrentIndex(
            0
        )

        # Conversion
        self.units_per_plaquette_in.setValue(
            10
        )

        self.units_per_box_in.setValue(
            10
        )

        self.boxes_per_carton_in.setValue(
            10
        )

        # Quantité
        self.qty_in.setValue(
            1
        )

        # Prix
        self.price_in.setValue(
            0
        )

        # Date
        self.expiry_in.setDate(
            QDate.currentDate().addYears(1)
        )

        # Bouton
        self.btn_save.setText(
            "➕ Ajouter le produit"
        )

        self.btn_save.setProperty(
            "class",
            "btn-primary"
        )

        self.btn_save.style().unpolish(
            self.btn_save
        )

        self.btn_save.style().polish(
            self.btn_save
        )

        # Cacher annuler
        self.btn_cancel.setVisible(
            False
        )

        self.update_conversion_label()

    # =============================================================
    # ACTUALISER TABLEAU
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

                # =================================================
                # LOTS
                # =================================================

                batches = (
                    session.query(ProductBatch)
                    .filter(
                        ProductBatch.product_id == product.id
                    )
                    .order_by(
                        ProductBatch.expiry_date.asc()
                    )
                    .all()
                )

                # -------------------------------------------------
                # Si aucun lot
                # -------------------------------------------------

                if not batches:

                    self.add_product_row(
                        product,
                        None
                    )

                    continue

                # -------------------------------------------------
                # Un médicament peut avoir plusieurs lots
                # -------------------------------------------------

                for batch in batches:

                    self.add_product_row(
                        product,
                        batch
                    )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger les produits.\n\n"
                    f"{type(error).__name__}: {error}"
                )
            )

        finally:

            session.close()

    # =============================================================
    # AJOUTER UNE LIGNE
    # =============================================================

    def add_product_row(
        self,
        product,
        batch
    ):

        row = self.table.rowCount()

        self.table.insertRow(
            row
        )

        # =========================================================
        # NOM
        # =========================================================

        name_item = QTableWidgetItem(
            product.name or ""
        )

        self.table.setItem(
            row,
            0,
            name_item
        )

        # =========================================================
        # LOT
        # =========================================================

        if batch:

            batch_number = (
                batch.batch_number
                or "N/A"
            )

        else:

            batch_number = getattr(
                product,
                "batch_number",
                None
            ) or "N/A"

        batch_item = QTableWidgetItem(
            batch_number
        )

        batch_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            1,
            batch_item
        )

        # =========================================================
        # CONDITIONNEMENT
        # =========================================================

        packaging = getattr(
            product,
            "packaging",
            "N/A"
        ) or "N/A"

        packaging_item = QTableWidgetItem(
            packaging
        )

        packaging_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            2,
            packaging_item
        )

        # =========================================================
        # STOCK
        # =========================================================

        if batch:

            stock_units = int(
                batch.stock_units or 0
            )

        else:

            stock_units = int(
                getattr(
                    product,
                    "stock_units",
                    0
                ) or 0
            )

        stock_text = self.format_stock(
            product,
            stock_units
        )

        stock_item = QTableWidgetItem(
            stock_text
        )

        stock_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            3,
            stock_item
        )

        # =========================================================
        # PRIX COMPRIMÉ
        # =========================================================

        price_comprime = float(
            getattr(
                product,
                "price_per_comprime",
                0
            ) or 0
        )

        if price_comprime <= 0:

            # Compatibilité ancienne base
            price_comprime = float(
                getattr(
                    product,
                    "price",
                    0
                ) or 0
            )

        self.set_price_item(
            row,
            4,
            price_comprime
        )

        # =========================================================
        # PRIX PLAQUETTE
        # =========================================================

        price_plaquette = float(
            getattr(
                product,
                "price_per_plaquette",
                0
            ) or 0
        )

        self.set_price_item(
            row,
            5,
            price_plaquette
        )

        # =========================================================
        # PRIX BOÎTE
        # =========================================================

        price_box = float(
            getattr(
                product,
                "price_per_box",
                0
            ) or 0
        )

        self.set_price_item(
            row,
            6,
            price_box
        )

        # =========================================================
        # PRIX CARTON
        # =========================================================

        price_carton = float(
            getattr(
                product,
                "price_per_carton",
                0
            ) or 0
        )

        self.set_price_item(
            row,
            7,
            price_carton
        )

        # =========================================================
        # EXPIRATION
        # =========================================================

        expiry_date = None

        if batch:

            expiry_date = batch.expiry_date

        if not expiry_date:

            expiry_date = getattr(
                product,
                "expiry_date",
                None
            )

        if expiry_date:

            expiry_text = expiry_date.strftime(
                "%d/%m/%Y"
            )

            expiry_item = QTableWidgetItem(
                expiry_text
            )

            expiry_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            # -----------------------------------------------------
            # COULEUR EXPIRATION
            # -----------------------------------------------------

            today = datetime.now().date()

            if expiry_date < today:

                expiry_item.setText(
                    f"🔴 {expiry_text}"
                )

            else:

                days = (
                    expiry_date - today
                ).days

                if days <= 90:

                    expiry_item.setText(
                        f"🟠 {expiry_text}"
                    )

                else:

                    expiry_item.setText(
                        f"🟢 {expiry_text}"
                    )

        else:

            expiry_item = QTableWidgetItem(
                "⚠️ N/A"
            )

            expiry_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

        self.table.setItem(
            row,
            8,
            expiry_item
        )

        # =========================================================
        # DOUBLE-CLICK POUR MODIFIER
        # =========================================================

        self.table.itemDoubleClicked.connect(
            self.handle_table_double_click
        )

    # =============================================================
    # PRIX TABLEAU
    # =============================================================

    def set_price_item(
        self,
        row,
        column,
        price
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
            item
        )

    # =============================================================
    # DOUBLE CLICK
    # =============================================================

    def handle_table_double_click(
        self,
        item
    ):

        row = item.row()

        if row < 0:
            return

        name_item = self.table.item(
            row,
            0
        )

        if not name_item:
            return

        name = name_item.text()

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

        finally:

            session.close()