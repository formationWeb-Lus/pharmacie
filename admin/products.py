from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QGroupBox,
    QFrame,
    QScrollArea,
    QSizePolicy,
)


from database.database import (
    SessionLocal,
    calculate_product_global_stock,
)

from database.models import Product, ProductBatch


class ProductPage(QWidget):
    """
    Page professionnelle de gestion des produits.

    Colonnes :
        Produit
        Stock
        Prix
        Date d'expiration
        Statut
        Actions

    Fonctionnalités :
        - Recherche
        - Filtre par catégorie
        - Ajout
        - Modification
        - Suppression
        - Consultation
        - Gestion des lots
        - Gestion des prix
        - Gestion des dates d'expiration
    """

    def __init__(
        self,
        parent=None,
        current_user=None,
    ):
        super().__init__(parent)

        self.current_user = current_user

        self.setObjectName("ProductPage")

        self.setup_ui()
        self.apply_styles()

        self.load_categories()
        self.load_products()

    # ============================================================
    # INTERFACE PRINCIPALE
    # ============================================================

    def setup_ui(self):

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(0)

        # ========================================================
        # SCROLL GLOBAL
        # ========================================================

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)

        scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        content = QWidget()

        content.setObjectName(
            "ProductContent"
        )

        content.setMinimumWidth(
            1050
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            28,
            28,
            28,
            28,
        )

        content_layout.setSpacing(
            20
        )

        scroll_area.setWidget(
            content
        )

        root_layout.addWidget(
            scroll_area
        )

        # ========================================================
        # HEADER
        # ========================================================

        header_layout = QHBoxLayout()

        header_layout.setSpacing(
            20
        )

        title_layout = QVBoxLayout()

        title_layout.setSpacing(
            4
        )

        eyebrow = QLabel(
            "ADMINISTRATION  •  PRODUITS"
        )

        eyebrow.setObjectName(
            "pageEyebrow"
        )

        title = QLabel(
            "Gestion des produits"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Gérez votre catalogue, les stocks, les prix et les dates d'expiration."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(
            eyebrow
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        # --------------------------------------------------------
        # BOUTON AJOUT
        # --------------------------------------------------------

        add_button = QPushButton(
            "＋  Ajouter un produit"
        )

        add_button.setObjectName(
            "primaryButton"
        )

        add_button.setMinimumHeight(
            46
        )

        add_button.setMinimumWidth(
            190
        )

        add_button.setCursor(
            Qt.PointingHandCursor
        )

        add_button.clicked.connect(
            self.add_product
        )

        header_layout.addWidget(
            add_button
        )

        content_layout.addLayout(
            header_layout
        )

        # ========================================================
        # INDICATEURS
        # ========================================================

        stats_layout = QGridLayout()

        stats_layout.setSpacing(
            14
        )

        self.total_products_label = (
            self.create_stat_card(
                "Produits",
                "0",
                "Produits enregistrés",
            )
        )

        self.available_stock_label = (
            self.create_stat_card(
                "Stock",
                "0",
                "Unités disponibles",
            )
        )

        self.low_stock_label = (
            self.create_stat_card(
                "Attention",
                "0",
                "Produits en stock faible",
            )
        )

        self.expired_label = (
            self.create_stat_card(
                "Expiration",
                "0",
                "Produits expirés",
            )
        )

        stats_layout.addWidget(
            self.total_products_label.parentWidget(),
            0,
            0,
        )

        stats_layout.addWidget(
            self.available_stock_label.parentWidget(),
            0,
            1,
        )

        stats_layout.addWidget(
            self.low_stock_label.parentWidget(),
            0,
            2,
        )

        stats_layout.addWidget(
            self.expired_label.parentWidget(),
            0,
            3,
        )

        content_layout.addLayout(
            stats_layout
        )

        # ========================================================
        # FILTRES
        # ========================================================

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "filterFrame"
        )

        filter_layout = QHBoxLayout(
            filter_frame
        )

        filter_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        filter_layout.setSpacing(
            10
        )

        # --------------------------------------------------------
        # RECHERCHE
        # --------------------------------------------------------

        search_title = QLabel(
            "Recherche"
        )

        search_title.setObjectName(
            "filterLabel"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Rechercher par nom de produit..."
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.textChanged.connect(
            self.load_products
        )

        # --------------------------------------------------------
        # CATÉGORIE
        # --------------------------------------------------------

        category_title = QLabel(
            "Catégorie"
        )

        category_title.setObjectName(
            "filterLabel"
        )

        self.category_combo = QComboBox()

        self.category_combo.setMinimumHeight(
            42
        )

        self.category_combo.addItem(
            "Toutes les catégories"
        )

        self.category_combo.currentIndexChanged.connect(
            self.load_products
        )

        # --------------------------------------------------------
        # ACTUALISER
        # --------------------------------------------------------

        refresh_button = QPushButton(
            "↻  Actualiser"
        )

        refresh_button.setObjectName(
            "refreshButton"
        )

        refresh_button.setMinimumHeight(
            42
        )

        refresh_button.setCursor(
            Qt.PointingHandCursor
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        filter_layout.addWidget(
            search_title
        )

        filter_layout.addWidget(
            self.search_input,
            3,
        )

        filter_layout.addWidget(
            category_title
        )

        filter_layout.addWidget(
            self.category_combo,
            2,
        )

        filter_layout.addWidget(
            refresh_button
        )

        content_layout.addWidget(
            filter_frame
        )

        # ========================================================
        # TITRE DU TABLEAU
        # ========================================================

        table_header = QHBoxLayout()

        table_title_layout = QVBoxLayout()

        table_title_layout.setSpacing(
            3
        )

        table_title = QLabel(
            "Liste des produits"
        )

        table_title.setObjectName(
            "sectionTitle"
        )

        table_subtitle = QLabel(
            "Sélectionnez un produit pour le consulter ou utiliser les actions."
        )

        table_subtitle.setObjectName(
            "sectionSubtitle"
        )

        table_title_layout.addWidget(
            table_title
        )

        table_title_layout.addWidget(
            table_subtitle
        )

        table_header.addLayout(
            table_title_layout
        )

        table_header.addStretch()

        self.result_count_label = QLabel(
            "0 produit"
        )

        self.result_count_label.setObjectName(
            "resultCount"
        )

        table_header.addWidget(
            self.result_count_label
        )

        content_layout.addLayout(
            table_header
        )

        # ========================================================
        # TABLEAU
        # ========================================================

        self.products_table = QTableWidget()

        # 6 colonnes exactement
        self.products_table.setColumnCount(
            6
        )

        self.products_table.setHorizontalHeaderLabels(
            [
                "Produit",
                "Stock",
                "Prix",
                "Date d'expiration",
                "Statut",
                "Actions",
            ]
        )

        self.products_table.setMinimumHeight(
            520
        )

        self.products_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.products_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.products_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.products_table.setFocusPolicy(
            Qt.NoFocus
        )

        self.products_table.verticalHeader().setVisible(
            False
        )

        self.products_table.setAlternatingRowColors(
            True
        )

        self.products_table.setWordWrap(
            False
        )

        self.products_table.setShowGrid(
            False
        )

        table_header_view = (
            self.products_table.horizontalHeader()
        )

        # Produit
        table_header_view.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        # Stock
        table_header_view.setSectionResizeMode(
            1,
            QHeaderView.Fixed,
        )

        self.products_table.setColumnWidth(
            1,
            150,
        )

        # Prix
        table_header_view.setSectionResizeMode(
            2,
            QHeaderView.Fixed,
        )

        self.products_table.setColumnWidth(
            2,
            170,
        )

        # Expiration
        table_header_view.setSectionResizeMode(
            3,
            QHeaderView.Fixed,
        )

        self.products_table.setColumnWidth(
            3,
            180,
        )

        # Statut
        table_header_view.setSectionResizeMode(
            4,
            QHeaderView.Fixed,
        )

        self.products_table.setColumnWidth(
            4,
            160,
        )

        # Actions
        table_header_view.setSectionResizeMode(
            5,
            QHeaderView.Fixed,
        )

        self.products_table.setColumnWidth(
            5,
            250,
        )

        self.products_table.cellDoubleClicked.connect(
            self.on_table_double_clicked
        )

        content_layout.addWidget(
            self.products_table
        )

        # ========================================================
        # NOTE
        # ========================================================

        info_frame = QFrame()

        info_frame.setObjectName(
            "infoFrame"
        )

        info_layout = QHBoxLayout(
            info_frame
        )

        info_layout.setContentsMargins(
            16,
            12,
            16,
            12,
        )

        info_icon = QLabel(
            "ⓘ"
        )

        info_icon.setObjectName(
            "infoIcon"
        )

        info_text = QLabel(
            "Les prix affichés correspondent au prix de vente unitaire configuré pour le produit."
        )

        info_text.setObjectName(
            "infoText"
        )

        info_layout.addWidget(
            info_icon
        )

        info_layout.addWidget(
            info_text
        )

        info_layout.addStretch()

        content_layout.addWidget(
            info_frame
        )

        content_layout.addStretch()

    # ============================================================
    # CARTE STATISTIQUE
    # ============================================================

    def create_stat_card(
        self,
        title,
        value,
        description,
    ):

        card = QFrame()

        card.setObjectName(
            "statCard"
        )

        card.setMinimumHeight(
            125
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        layout.setSpacing(
            4
        )

        title_label = QLabel(
            title.upper()
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

        value_label.setMinimumHeight(
            38
        )

        value_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "statDescription"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            description_label
        )

        # La valeur est conservée dans l'objet
        value_label._stat_card = card

        return value_label

    # ============================================================
    # CATÉGORIES
    # ============================================================

    def load_categories(self):

        session = SessionLocal()

        try:

            categories = (
                session.query(Product.category)
                .filter(
                    Product.category.isnot(None),
                    Product.category != "",
                )
                .distinct()
                .order_by(
                    Product.category
                )
                .all()
            )

            current = (
                self.category_combo.currentText()
            )

            self.category_combo.blockSignals(
                True
            )

            self.category_combo.clear()

            self.category_combo.addItem(
                "Toutes les catégories"
            )

            for row in categories:

                category = row[0]

                if category:

                    self.category_combo.addItem(
                        str(category)
                    )

            index = (
                self.category_combo.findText(
                    current
                )
            )

            if index >= 0:

                self.category_combo.setCurrentIndex(
                    index
                )

            self.category_combo.blockSignals(
                False
            )

        except Exception as error:

            self.category_combo.blockSignals(
                False
            )

            print(
                "Erreur catégories :",
                error,
            )

        finally:

            session.close()

    # ============================================================
    # CHARGER PRODUITS
    # ============================================================

    def load_products(self):

        session = SessionLocal()

        try:

            search = (
                self.search_input.text()
                .strip()
                .lower()
            )

            category = (
                self.category_combo.currentText()
            )

            products = (
                session.query(Product)
                .order_by(
                    Product.name.asc()
                )
                .all()
            )

            self.products_table.setRowCount(
                0
            )

            # ====================================================
            # STATISTIQUES GLOBALES
            # ====================================================

            total_products = 0
            total_stock = 0
            low_stock = 0
            expired_products = 0

            # ====================================================
            # PRODUITS AFFICHÉS
            # ====================================================

            displayed_products = 0

            for product in products:

                total_products += 1

                # ------------------------------------------------
                # STOCK
                # ------------------------------------------------

                stock = self.get_product_stock(
                    product
                )

                total_stock += stock

                # ------------------------------------------------
                # STATUT GLOBAL
                # ------------------------------------------------

                status = self.get_product_status(
                    product,
                    stock,
                )

                if status == "Stock faible":

                    low_stock += 1

                # ------------------------------------------------
                # EXPIRATION
                # ------------------------------------------------

                expiry = self.get_product_expiry(
                    product
                )

                if (
                    expiry
                    and expiry < date.today()
                ):

                    expired_products += 1

                # =================================================
                # FILTRES
                # =================================================

                if search:

                    name = (
                        product.name or ""
                    ).lower()

                    if search not in name:

                        continue

                if (
                    category
                    != "Toutes les catégories"
                    and (
                        product.category or ""
                    )
                    != category
                ):

                    continue

                # =================================================
                # AJOUT LIGNE
                # =================================================

                row = (
                    self.products_table.rowCount()
                )

                self.products_table.insertRow(
                    row
                )

                self.products_table.setRowHeight(
                    row,
                    58,
                )

                displayed_products += 1

                # ------------------------------------------------
                # PRODUIT
                # ------------------------------------------------

                name_item = QTableWidgetItem(
                    product.name or "-"
                )

                name_item.setTextAlignment(
                    Qt.AlignVCenter
                    | Qt.AlignLeft
                )

                name_item.setToolTip(
                    product.name or "-"
                )

                self.products_table.setItem(
                    row,
                    0,
                    name_item,
                )

                # ------------------------------------------------
                # STOCK
                # ------------------------------------------------

                stock_item = QTableWidgetItem(
                    self.format_number(
                        stock
                    )
                )

                stock_item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.products_table.setItem(
                    row,
                    1,
                    stock_item,
                )

                # ------------------------------------------------
                # PRIX
                # ------------------------------------------------

                price = (
                    getattr(
                        product,
                        "price",
                        0,
                    )
                    or 0
                )

                price_item = QTableWidgetItem(
                    self.format_money(
                        price
                    )
                )

                price_item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.products_table.setItem(
                    row,
                    2,
                    price_item,
                )

                # ------------------------------------------------
                # EXPIRATION
                # ------------------------------------------------

                expiry_item = QTableWidgetItem(
                    self.format_date(
                        expiry
                    )
                )

                expiry_item.setTextAlignment(
                    Qt.AlignCenter
                )

                if expiry:

                    if expiry < date.today():

                        expiry_item.setForeground(
                            QBrush(
                                QColor(
                                    "#dc2626"
                                )
                            )
                        )

                    else:

                        days = (
                            expiry
                            - date.today()
                        ).days

                        if days <= 30:

                            expiry_item.setForeground(
                                QBrush(
                                    QColor(
                                        "#d97706"
                                    )
                                )
                            )

                self.products_table.setItem(
                    row,
                    3,
                    expiry_item,
                )

                # ------------------------------------------------
                # STATUT
                # ------------------------------------------------

                status_item = self.create_status_item(
                    status
                )

                self.products_table.setItem(
                    row,
                    4,
                    status_item,
                )

                # ------------------------------------------------
                # ACTIONS
                # ------------------------------------------------

                self.create_action_buttons(
                    row,
                    product,
                )

            # ====================================================
            # STATISTIQUES
            # ====================================================

            self.total_products_label.setText(
                self.format_number(
                    total_products
                )
            )

            self.available_stock_label.setText(
                self.format_number(
                    total_stock
                )
            )

            self.low_stock_label.setText(
                self.format_number(
                    low_stock
                )
            )

            self.expired_label.setText(
                self.format_number(
                    expired_products
                )
            )

            # ====================================================
            # COMPTEUR
            # ====================================================

            if displayed_products == 1:

                self.result_count_label.setText(
                    "1 produit affiché"
                )

            else:

                self.result_count_label.setText(
                    f"{self.format_number(displayed_products)} produits affichés"
                )

        except Exception as error:

            print(
                "Erreur chargement produits :",
                error,
            )

        finally:

            session.close()

    # ============================================================
    # BOUTONS D'ACTION
    # ============================================================

    def create_action_buttons(
        self,
        row,
        product,
    ):

        container = QWidget()

        container.setObjectName(
            "actionContainer"
        )

        layout = QHBoxLayout(
            container
        )

        layout.setContentsMargins(
            6,
            5,
            6,
            5,
        )

        layout.setSpacing(
            7
        )

        # --------------------------------------------------------
        # VOIR
        # --------------------------------------------------------

        view_button = QPushButton(
            "Voir"
        )

        view_button.setObjectName(
            "viewButton"
        )

        view_button.setToolTip(
            "Consulter les détails du produit"
        )

        # --------------------------------------------------------
        # MODIFIER
        # --------------------------------------------------------

        edit_button = QPushButton(
            "Modifier"
        )

        edit_button.setObjectName(
            "editButton"
        )

        edit_button.setToolTip(
            "Modifier ce produit"
        )

        # --------------------------------------------------------
        # SUPPRIMER
        # --------------------------------------------------------

        delete_button = QPushButton(
            "Supprimer"
        )

        delete_button.setObjectName(
            "deleteButton"
        )

        delete_button.setToolTip(
            "Supprimer définitivement ce produit"
        )

        for button in (
            view_button,
            edit_button,
            delete_button,
        ):

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                36
            )

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

        view_button.clicked.connect(
            lambda checked=False,
            p=product:
            self.view_product(p)
        )

        edit_button.clicked.connect(
            lambda checked=False,
            p=product:
            self.edit_product(p)
        )

        delete_button.clicked.connect(
            lambda checked=False,
            p=product:
            self.delete_product(p)
        )

        layout.addWidget(
            view_button
        )

        layout.addWidget(
            edit_button
        )

        layout.addWidget(
            delete_button
        )

        self.products_table.setCellWidget(
            row,
            5,
            container,
        )

    # ============================================================
    # STATUT
    # ============================================================

    def create_status_item(
        self,
        status,
    ):

        item = QTableWidgetItem(
            status
        )

        item.setTextAlignment(
            Qt.AlignCenter
        )

        if status == "Disponible":

            item.setForeground(
                QBrush(
                    QColor(
                        "#166534"
                    )
                )
            )

            item.setBackground(
                QBrush(
                    QColor(
                        "#dcfce7"
                    )
                )
            )

        elif status == "Stock faible":

            item.setForeground(
                QBrush(
                    QColor(
                        "#92400e"
                    )
                )
            )

            item.setBackground(
                QBrush(
                    QColor(
                        "#fef3c7"
                    )
                )
            )

        elif status == "Rupture":

            item.setForeground(
                QBrush(
                    QColor(
                        "#991b1b"
                    )
                )
            )

            item.setBackground(
                QBrush(
                    QColor(
                        "#fee2e2"
                    )
                )
            )

        else:

            item.setForeground(
                QBrush(
                    QColor(
                        "#374151"
                    )
                )
            )

        return item

    # ============================================================
    # AJOUTER PRODUIT
    # ============================================================

    def add_product(self):

        dialog = ProductDialog(
            parent=self,
            product=None,
        )

        if (
            dialog.exec()
            != QDialog.Accepted
        ):

            return

        data = dialog.get_data()

        session = SessionLocal()

        try:

            existing = (
                session.query(Product)
                .filter(
                    Product.name
                    == data["name"]
                )
                .first()
            )

            if existing:

                QMessageBox.warning(
                    self,
                    "Produit déjà existant",
                    (
                        "Un produit portant ce nom "
                        "existe déjà dans la base de données."
                    ),
                )

                return

            product = Product()

            product.name = data["name"]

            product.category = data["category"]

            product.base_unit = data["base_unit"]

            product.packaging = data["packaging"]

            product.is_medicine = (
                data["is_medicine"]
            )

            product.units_per_plaquette = (
                data["units_per_plaquette"]
            )

            product.plaquettes_per_box = (
                data["plaquettes_per_box"]
            )

            product.boxes_per_carton = (
                data["boxes_per_carton"]
            )

            product.quantity = (
                data["quantity"]
            )

            product.stock_units = (
                data["stock_units"]
            )

            product.min_quantity = (
                data["min_quantity"]
            )

            product.price = (
                data["price"]
            )

            product.price_per_comprime = (
                data["price_per_comprime"]
            )

            product.price_per_plaquette = (
                data["price_per_plaquette"]
            )

            product.price_per_box = (
                data["price_per_box"]
            )

            product.price_per_carton = (
                data["price_per_carton"]
            )

            product.batch_number = (
                data["batch_number"]
            )

            product.expiry_date = (
                data["expiry_date"]
            )

            product.purchase_price = (
                data["purchase_price"]
            )

            product.supplier = (
                data["supplier"]
            )

            session.add(
                product
            )

            session.flush()

            # ----------------------------------------------------
            # LOT
            # ----------------------------------------------------

            if (
                data["batch_number"]
                or data["stock_units"] > 0
            ):

                batch = ProductBatch()

                batch.product_id = (
                    product.id
                )

                batch.batch_number = (
                    data["batch_number"]
                    or f"LOT-{product.id}"
                )

                batch.expiry_date = (
                    data["expiry_date"]
                )

                batch.stock_units = (
                    data["stock_units"]
                )

                batch.purchase_quantity = (
                    data["purchase_quantity"]
                )

                batch.purchase_unit = (
                    data["purchase_unit"]
                )

                batch.purchase_price = (
                    data["purchase_price"]
                )

                batch.supplier = (
                    data["supplier"]
                )

                batch.received_at = (
                    datetime.now()
                )

                batch.is_active = True

                session.add(
                    batch
                )

            session.commit()

            QMessageBox.information(
                self,
                "Produit ajouté",
                (
                    f"Le produit « {data['name']} » "
                    "a été ajouté avec succès."
                ),
            )

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur d'ajout",
                (
                    "Impossible d'ajouter le produit.\n\n"
                    f"{error}"
                ),
            )

        finally:

            session.close()

        self.refresh()

    # ============================================================
    # MODIFIER PRODUIT
    # ============================================================

    def edit_product(
        self,
        product,
    ):

        session = SessionLocal()

        try:

            db_product = (
                session.query(Product)
                .filter(
                    Product.id
                    == product.id
                )
                .first()
            )

            if not db_product:

                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Le produit demandé n'existe plus.",
                )

                return

            dialog = ProductDialog(
                parent=self,
                product=db_product,
            )

            if (
                dialog.exec()
                != QDialog.Accepted
            ):

                return

            data = dialog.get_data()

            # ----------------------------------------------------
            # MISE À JOUR
            # ----------------------------------------------------

            db_product.name = (
                data["name"]
            )

            db_product.category = (
                data["category"]
            )

            db_product.base_unit = (
                data["base_unit"]
            )

            db_product.packaging = (
                data["packaging"]
            )

            db_product.is_medicine = (
                data["is_medicine"]
            )

            db_product.units_per_plaquette = (
                data["units_per_plaquette"]
            )

            db_product.plaquettes_per_box = (
                data["plaquettes_per_box"]
            )

            db_product.boxes_per_carton = (
                data["boxes_per_carton"]
            )

            db_product.min_quantity = (
                data["min_quantity"]
            )

            db_product.price = (
                data["price"]
            )

            db_product.price_per_comprime = (
                data["price_per_comprime"]
            )

            db_product.price_per_plaquette = (
                data["price_per_plaquette"]
            )

            db_product.price_per_box = (
                data["price_per_box"]
            )

            db_product.price_per_carton = (
                data["price_per_carton"]
            )

            db_product.purchase_price = (
                data["purchase_price"]
            )

            db_product.supplier = (
                data["supplier"]
            )

            db_product.batch_number = (
                data["batch_number"]
            )

            db_product.expiry_date = (
                data["expiry_date"]
            )

            # ----------------------------------------------------
            # LOT PRINCIPAL
            # ----------------------------------------------------

            batch = self.get_first_batch(
                db_product
            )

            if batch:

                if data["batch_number"]:

                    batch.batch_number = (
                        data["batch_number"]
                    )

                batch.expiry_date = (
                    data["expiry_date"]
                )

                batch.purchase_price = (
                    data["purchase_price"]
                )

                batch.supplier = (
                    data["supplier"]
                )

            session.commit()

            QMessageBox.information(
                self,
                "Modification réussie",
                (
                    f"Le produit « {db_product.name} » "
                    "a été modifié avec succès."
                ),
            )

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur de modification",
                (
                    "Impossible de modifier le produit.\n\n"
                    f"{error}"
                ),
            )

        finally:

            session.close()

        self.refresh()

    # ============================================================
    # SUPPRIMER PRODUIT
    # ============================================================

    def delete_product(
        self,
        product,
    ):

        # --------------------------------------------------------
        # DIALOG DE CONFIRMATION
        # --------------------------------------------------------

        message_box = QMessageBox(
            self
        )

        message_box.setIcon(
            QMessageBox.Warning
        )

        message_box.setWindowTitle(
            "Supprimer le produit"
        )

        message_box.setText(
            f"Supprimer « {product.name} » ?"
        )

        message_box.setInformativeText(
            "Cette opération peut supprimer le produit "
            "et ses informations de stock. "
            "Vérifiez que ce produit n'est pas nécessaire "
            "à l'historique des ventes."
        )

        yes_button = message_box.addButton(
            "Supprimer",
            QMessageBox.DestructiveRole,
        )

        no_button = message_box.addButton(
            "Annuler",
            QMessageBox.RejectRole,
        )

        message_box.setDefaultButton(
            no_button
        )

        message_box.exec()

        if (
            message_box.clickedButton()
            != yes_button
        ):

            return

        # --------------------------------------------------------
        # SUPPRESSION
        # --------------------------------------------------------

        session = SessionLocal()

        try:

            db_product = (
                session.query(Product)
                .filter(
                    Product.id
                    == product.id
                )
                .first()
            )

            if not db_product:

                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Le produit n'existe plus.",
                )

                return

            # ----------------------------------------------------
            # VÉRIFIER L'HISTORIQUE
            # ----------------------------------------------------

            try:

                if db_product.sale_items:

                    QMessageBox.warning(
                        self,
                        "Suppression protégée",
                        (
                            "Ce produit possède déjà des ventes "
                            "dans l'historique.\n\n"
                            "La suppression est bloquée afin "
                            "de préserver les données comptables "
                            "et l'historique des ventes."
                        ),
                    )

                    return

            except Exception:

                pass

            session.delete(
                db_product
            )

            session.commit()

            QMessageBox.information(
                self,
                "Produit supprimé",
                (
                    f"Le produit « {product.name} » "
                    "a été supprimé avec succès."
                ),
            )

        except Exception as error:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur de suppression",
                (
                    "Impossible de supprimer le produit.\n\n"
                    f"{error}"
                ),
            )

        finally:

            session.close()

        self.refresh()

    # ============================================================
    # VOIR PRODUIT
    # ============================================================

    def view_product(
        self,
        product,
    ):

        session = SessionLocal()

        try:

            db_product = (
                session.query(Product)
                .filter(
                    Product.id
                    == product.id
                )
                .first()
            )

            if not db_product:

                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Le produit n'existe plus.",
                )

                return

            stock = self.get_product_stock(
                db_product
            )

            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id
                    == db_product.id
                )
                .order_by(
                    ProductBatch.expiry_date.asc()
                )
                .all()
            )

            dialog = ProductDetailsDialog(
                parent=self,
                product=db_product,
                stock=stock,
                batches=batches,
            )

            dialog.exec()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )

        finally:

            session.close()

    # ============================================================
    # DOUBLE CLIC
    # ============================================================

    def on_table_double_clicked(
        self,
        row,
        column,
    ):

        widget = (
            self.products_table.cellWidget(
                row,
                5,
            )
        )

        if widget:

            # Le bouton Voir est le premier bouton
            buttons = widget.findChildren(
                QPushButton
            )

            if buttons:

                self.view_product_from_row(
                    row
                )

    def view_product_from_row(
        self,
        row,
    ):

        product_item = (
            self.products_table.item(
                row,
                0,
            )
        )

        if not product_item:
            return

        name = product_item.text()

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.name
                    == name
                )
                .first()
            )

            if product:

                self.view_product(
                    product
                )

        finally:

            session.close()

    # ============================================================
    # STOCK
    # ============================================================

    @staticmethod
    def get_product_stock(
        product,
    ):

        try:

            return int(
                calculate_product_global_stock(
                    product
                )
                or 0
            )

        except Exception:

            return int(
                getattr(
                    product,
                    "stock_units",
                    0,
                )
                or 0
            )

    # ============================================================
    # EXPIRATION
    # ============================================================

    def get_product_expiry(
        self,
        product,
    ):

        batch = self.get_first_batch(
            product
        )

        if batch:

            return batch.expiry_date

        return getattr(
            product,
            "expiry_date",
            None,
        )

    # ============================================================
    # PREMIER LOT
    # ============================================================

    def get_first_batch(
        self,
        product,
    ):

        try:

            batches = list(
                getattr(
                    product,
                    "batches",
                    [],
                )
                or []
            )

            if not batches:

                return None

            batches.sort(
                key=lambda batch: (
                    batch.expiry_date
                    or date.max
                )
            )

            return batches[0]

        except Exception:

            return None

    # ============================================================
    # STATUT
    # ============================================================

    @staticmethod
    def get_product_status(
        product,
        stock,
    ):

        if stock <= 0:

            return "Rupture"

        min_stock = int(
            getattr(
                product,
                "min_quantity",
                0,
            )
            or 0
        )

        if stock <= min_stock:

            return "Stock faible"

        return "Disponible"

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh(self):

        self.load_categories()
        self.load_products()

    # ============================================================
    # FORMAT NOMBRE
    # ============================================================

    @staticmethod
    def format_number(
        value,
    ):

        try:

            return (
                f"{int(value):,}"
                .replace(",", " ")
            )

        except Exception:

            return "0"

    # ============================================================
    # FORMAT ARGENT
    # ============================================================

    @staticmethod
    def format_money(
        value,
    ):

        try:

            return (
                f"{float(value or 0):,.0f}"
                .replace(",", " ")
                + " FC"
            )

        except Exception:

            return "0 FC"

    # ============================================================
    # FORMAT DATE
    # ============================================================

    @staticmethod
    def format_date(
        value,
    ):

        if not value:

            return "-"

        try:

            if isinstance(
                value,
                datetime,
            ):

                value = value.date()

            if isinstance(
                value,
                date,
            ):

                return value.strftime(
                    "%d/%m/%Y"
                )

            return str(value)

        except Exception:

            return str(value)

    # ============================================================
    # STYLE
    # ============================================================

    def apply_styles(self):

        self.setStyleSheet(
            """
            /* ==================================================
               PAGE
            ================================================== */

            QWidget#ProductPage {
                background: #f4f7fb;
            }

            QWidget#ProductContent {
                background: #f4f7fb;
            }

            /* ==================================================
               HEADER
            ================================================== */

            QLabel#pageEyebrow {
                color: #d49b00;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#pageTitle {
                color: #08192d;
                font-size: 29px;
                font-weight: 800;
            }

            QLabel#pageSubtitle {
                color: #64748b;
                font-size: 13px;
            }

            /* ==================================================
               PRIMARY BUTTON
            ================================================== */

            QPushButton#primaryButton {
                background: #facc15;
                color: #08192d;
                border: none;
                border-radius: 9px;
                padding: 11px 18px;
                font-size: 13px;
                font-weight: 800;
            }

            QPushButton#primaryButton:hover {
                background: #eab308;
            }

            QPushButton#primaryButton:pressed {
                background: #ca8a04;
            }

            /* ==================================================
               STAT CARDS
            ================================================== */

            QFrame#statCard {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }

            QFrame#statCard:hover {
                border: 1px solid #facc15;
            }

            QLabel#statTitle {
                color: #64748b;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.8px;
            }

            QLabel#statValue {
                color: #08192d;
                font-size: 27px;
                font-weight: 800;
            }

            QLabel#statDescription {
                color: #94a3b8;
                font-size: 11px;
            }

            /* ==================================================
               FILTRES
            ================================================== */

            QFrame#filterFrame {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }

            QLabel#filterLabel {
                color: #334155;
                font-size: 12px;
                font-weight: 700;
            }

            QLineEdit,
            QComboBox {
                background: #f8fafc;
                color: #0f172a;
                border: 1px solid #dbe3ec;
                border-radius: 8px;
                padding: 8px 11px;
                font-size: 12px;
            }

            QLineEdit:hover,
            QComboBox:hover {
                border: 1px solid #cbd5e1;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #facc15;
                background: white;
            }

            QPushButton#refreshButton {
                background: #08192d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 700;
            }

            QPushButton#refreshButton:hover {
                background: #102c4b;
            }

            /* ==================================================
               TITRES SECTIONS
            ================================================== */

            QLabel#sectionTitle {
                color: #08192d;
                font-size: 18px;
                font-weight: 800;
            }

            QLabel#sectionSubtitle {
                color: #94a3b8;
                font-size: 11px;
            }

            QLabel#resultCount {
                background: #e8eef5;
                color: #334155;
                border-radius: 7px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 700;
            }

            /* ==================================================
               TABLE
            ================================================== */

            QTableWidget {
                background: white;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                gridline-color: transparent;
                font-size: 12px;
                outline: none;
            }

            QTableWidget::item {
                border-bottom: 1px solid #f1f5f9;
                padding: 8px;
            }

            QTableWidget::item:alternate {
                background: #fbfcfe;
            }

            QTableWidget::item:selected {
                background: #fff8d6;
                color: #08192d;
            }

            QHeaderView::section {
                background: #08192d;
                color: white;
                border: none;
                padding: 12px 10px;
                font-size: 11px;
                font-weight: 800;
            }

            QTableCornerButton::section {
                background: #08192d;
                border: none;
            }

            /* ==================================================
               ACTIONS
            ================================================== */

            QWidget#actionContainer {
                background: transparent;
            }

            QTableWidget QPushButton {
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
            }

            QPushButton#viewButton {
                background: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
            }

            QPushButton#viewButton:hover {
                background: #dbeafe;
                border: 1px solid #93c5fd;
            }

            QPushButton#editButton {
                background: #fef3c7;
                color: #92400e;
                border: 1px solid #fcd34d;
            }

            QPushButton#editButton:hover {
                background: #fde68a;
                border: 1px solid #f59e0b;
            }

            QPushButton#deleteButton {
                background: #fee2e2;
                color: #b91c1c;
                border: 1px solid #fca5a5;
            }

            QPushButton#deleteButton:hover {
                background: #fecaca;
                border: 1px solid #ef4444;
            }

            /* ==================================================
               INFORMATION
            ================================================== */

            QFrame#infoFrame {
                background: #eef4fa;
                border: 1px solid #dbe7f2;
                border-radius: 9px;
            }

            QLabel#infoIcon {
                color: #2563eb;
                font-size: 16px;
                font-weight: 800;
            }

            QLabel#infoText {
                color: #475569;
                font-size: 11px;
            }

            /* ==================================================
               DIALOG
            ================================================== */

            QDialog {
                background: #f4f7fb;
            }

            QDialog QLabel {
                color: #334155;
            }

            QGroupBox {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 12px;
                padding: 16px;
                color: #08192d;
                font-weight: 800;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 7px;
                color: #08192d;
            }

            QDialog QLineEdit,
            QDialog QComboBox,
            QDialog QSpinBox,
            QDialog QDoubleSpinBox {
                background: white;
                min-height: 32px;
            }

            QDialog QCheckBox {
                color: #334155;
                font-weight: 600;
            }

            QPushButton#dialogPrimary {
                background: #facc15;
                color: #08192d;
                border: none;
                border-radius: 8px;
                padding: 9px 20px;
                font-weight: 800;
            }

            QPushButton#dialogPrimary:hover {
                background: #eab308;
            }

            QPushButton#dialogCancel {
                background: #e2e8f0;
                color: #334155;
                border: none;
                border-radius: 8px;
                padding: 9px 20px;
                font-weight: 700;
            }

            QPushButton#dialogCancel:hover {
                background: #cbd5e1;
            }

            QScrollBar:vertical {
                background: #eef2f7;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 5px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }

            QScrollBar:horizontal {
                background: #eef2f7;
                height: 10px;
                margin: 2px;
            }

            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                border-radius: 5px;
                min-width: 40px;
            }
            """
        )


# =================================================================
# DIALOG PRODUIT
# =================================================================


class ProductDialog(QDialog):
    """
    Dialogue Ajouter / Modifier produit.
    """

    def __init__(
        self,
        parent=None,
        product=None,
    ):

        super().__init__(parent)

        self.product = product

        self.setWindowTitle(
            "Modifier le produit"
            if product
            else "Ajouter un produit"
        )

        self.setMinimumWidth(
            680
        )

        self.setMinimumHeight(
            700
        )

        self.setup_ui()

        if product:

            self.load_product()

    # ============================================================
    # UI
    # ============================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        main_layout.setSpacing(
            14
        )

        title = QLabel(
            "Modifier le produit"
            if self.product
            else "Nouveau produit"
        )

        title.setStyleSheet(
            """
            font-size: 23px;
            font-weight: 800;
            color: #08192d;
            """
        )

        subtitle = QLabel(
            "Renseignez les informations nécessaires au suivi du produit."
        )

        subtitle.setStyleSheet(
            """
            color: #64748b;
            font-size: 12px;
            """
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
        )

        # ========================================================
        # SCROLL DU FORMULAIRE
        # ========================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        form_content = QWidget()

        form_layout = QVBoxLayout(
            form_content
        )

        form_layout.setContentsMargins(
            2,
            2,
            2,
            10,
        )

        form_layout.setSpacing(
            12
        )

        scroll.setWidget(
            form_content
        )

        main_layout.addWidget(
            scroll,
            1,
        )

        # ========================================================
        # INFORMATIONS
        # ========================================================

        info_group = QGroupBox(
            "Informations générales"
        )

        info_form = QFormLayout(
            info_group
        )

        info_form.setSpacing(
            10
        )

        self.name_input = QLineEdit()

        self.name_input.setPlaceholderText(
            "Exemple : Paracétamol 500 mg"
        )

        self.category_input = QLineEdit()

        self.category_input.setPlaceholderText(
            "Exemple : Antalgique"
        )

        self.base_unit_combo = QComboBox()

        self.base_unit_combo.addItems(
            [
                "Comprimé",
                "Capsule",
                "Millilitre",
                "Flacon",
                "Ampoule",
                "Pièce",
            ]
        )

        self.packaging_combo = QComboBox()

        self.packaging_combo.addItems(
            [
                "Comprimé",
                "Plaquette",
                "Boîte",
                "Carton",
                "Flacon",
                "Ampoule",
                "Pièce",
            ]
        )

        self.medicine_check = QCheckBox(
            "Ce produit est un médicament"
        )

        self.medicine_check.setChecked(
            True
        )

        info_form.addRow(
            "Nom *",
            self.name_input,
        )

        info_form.addRow(
            "Catégorie",
            self.category_input,
        )

        info_form.addRow(
            "Unité de base",
            self.base_unit_combo,
        )

        info_form.addRow(
            "Conditionnement",
            self.packaging_combo,
        )

        info_form.addRow(
            "",
            self.medicine_check,
        )

        form_layout.addWidget(
            info_group
        )

        # ========================================================
        # CONDITIONNEMENT
        # ========================================================

        packaging_group = QGroupBox(
            "Conversion des conditionnements"
        )

        packaging_form = QGridLayout(
            packaging_group
        )

        packaging_form.setSpacing(
            10
        )

        packaging_form.addWidget(
            QLabel(
                "1 plaquette ="
            ),
            0,
            0,
        )

        self.units_per_plaquette = QSpinBox()

        self.units_per_plaquette.setRange(
            1,
            100000,
        )

        self.units_per_plaquette.setValue(
            10
        )

        packaging_form.addWidget(
            self.units_per_plaquette,
            0,
            1,
        )

        packaging_form.addWidget(
            QLabel("unités"),
            0,
            2,
        )

        packaging_form.addWidget(
            QLabel(
                "1 boîte ="
            ),
            1,
            0,
        )

        self.plaquettes_per_box = QSpinBox()

        self.plaquettes_per_box.setRange(
            1,
            100000,
        )

        self.plaquettes_per_box.setValue(
            10
        )

        packaging_form.addWidget(
            self.plaquettes_per_box,
            1,
            1,
        )

        packaging_form.addWidget(
            QLabel("plaquettes"),
            1,
            2,
        )

        packaging_form.addWidget(
            QLabel(
                "1 carton ="
            ),
            2,
            0,
        )

        self.boxes_per_carton = QSpinBox()

        self.boxes_per_carton.setRange(
            1,
            100000,
        )

        self.boxes_per_carton.setValue(
            10
        )

        packaging_form.addWidget(
            self.boxes_per_carton,
            2,
            1,
        )

        packaging_form.addWidget(
            QLabel("boîtes"),
            2,
            2,
        )

        form_layout.addWidget(
            packaging_group
        )

        # ========================================================
        # PRIX
        # ========================================================

        price_group = QGroupBox(
            "Prix de vente"
        )

        price_form = QGridLayout(
            price_group
        )

        price_form.setSpacing(
            10
        )

        self.price_comprime = (
            QDoubleSpinBox()
        )

        self.price_comprime.setRange(
            0,
            999999999,
        )

        self.price_comprime.setDecimals(
            2
        )

        self.price_plaquette = (
            QDoubleSpinBox()
        )

        self.price_plaquette.setRange(
            0,
            999999999,
        )

        self.price_plaquette.setDecimals(
            2
        )

        self.price_box = (
            QDoubleSpinBox()
        )

        self.price_box.setRange(
            0,
            999999999,
        )

        self.price_box.setDecimals(
            2
        )

        self.price_carton = (
            QDoubleSpinBox()
        )

        self.price_carton.setRange(
            0,
            999999999,
        )

        self.price_carton.setDecimals(
            2
        )

        price_form.addWidget(
            QLabel("Unité / comprimé"),
            0,
            0,
        )

        price_form.addWidget(
            self.price_comprime,
            0,
            1,
        )

        price_form.addWidget(
            QLabel("FC"),
            0,
            2,
        )

        price_form.addWidget(
            QLabel("Plaquette"),
            1,
            0,
        )

        price_form.addWidget(
            self.price_plaquette,
            1,
            1,
        )

        price_form.addWidget(
            QLabel("FC"),
            1,
            2,
        )

        price_form.addWidget(
            QLabel("Boîte"),
            2,
            0,
        )

        price_form.addWidget(
            self.price_box,
            2,
            1,
        )

        price_form.addWidget(
            QLabel("FC"),
            2,
            2,
        )

        price_form.addWidget(
            QLabel("Carton"),
            3,
            0,
        )

        price_form.addWidget(
            self.price_carton,
            3,
            1,
        )

        price_form.addWidget(
            QLabel("FC"),
            3,
            2,
        )

        form_layout.addWidget(
            price_group
        )

        # ========================================================
        # STOCK
        # ========================================================

        stock_group = QGroupBox(
            "Stock et informations du lot"
        )

        stock_form = QGridLayout(
            stock_group
        )

        stock_form.setSpacing(
            10
        )

        self.stock_input = QSpinBox()

        self.stock_input.setRange(
            0,
            999999999,
        )

        self.min_stock_input = QSpinBox()

        self.min_stock_input.setRange(
            0,
            999999999,
        )

        self.batch_input = QLineEdit()

        self.batch_input.setPlaceholderText(
            "Exemple : LOT-2026-001"
        )

        self.expiry_input = QLineEdit()

        self.expiry_input.setPlaceholderText(
            "AAAA-MM-JJ"
        )

        self.purchase_price_input = (
            QDoubleSpinBox()
        )

        self.purchase_price_input.setRange(
            0,
            999999999,
        )

        self.purchase_price_input.setDecimals(
            2
        )

        self.purchase_quantity_input = (
            QSpinBox()
        )

        self.purchase_quantity_input.setRange(
            0,
            999999999,
        )

        self.purchase_unit_combo = QComboBox()

        self.purchase_unit_combo.addItems(
            [
                "Comprimé",
                "Plaquette",
                "Boîte",
                "Carton",
                "Flacon",
                "Ampoule",
                "Pièce",
            ]
        )

        self.supplier_input = QLineEdit()

        self.supplier_input.setPlaceholderText(
            "Nom du fournisseur"
        )

        stock_form.addWidget(
            QLabel("Stock initial"),
            0,
            0,
        )

        stock_form.addWidget(
            self.stock_input,
            0,
            1,
        )

        stock_form.addWidget(
            QLabel("unités"),
            0,
            2,
        )

        stock_form.addWidget(
            QLabel("Stock minimum"),
            1,
            0,
        )

        stock_form.addWidget(
            self.min_stock_input,
            1,
            1,
        )

        stock_form.addWidget(
            QLabel("unités"),
            1,
            2,
        )

        stock_form.addWidget(
            QLabel("Numéro de lot"),
            2,
            0,
        )

        stock_form.addWidget(
            self.batch_input,
            2,
            1,
            1,
            2,
        )

        stock_form.addWidget(
            QLabel("Date d'expiration"),
            3,
            0,
        )

        stock_form.addWidget(
            self.expiry_input,
            3,
            1,
            1,
            2,
        )

        stock_form.addWidget(
            QLabel("Quantité achetée"),
            4,
            0,
        )

        stock_form.addWidget(
            self.purchase_quantity_input,
            4,
            1,
        )

        stock_form.addWidget(
            QLabel("unité"),
            4,
            2,
        )

        stock_form.addWidget(
            QLabel("Unité d'achat"),
            5,
            0,
        )

        stock_form.addWidget(
            self.purchase_unit_combo,
            5,
            1,
            1,
            2,
        )

        stock_form.addWidget(
            QLabel("Prix d'achat"),
            6,
            0,
        )

        stock_form.addWidget(
            self.purchase_price_input,
            6,
            1,
        )

        stock_form.addWidget(
            QLabel("FC"),
            6,
            2,
        )

        stock_form.addWidget(
            QLabel("Fournisseur"),
            7,
            0,
        )

        stock_form.addWidget(
            self.supplier_input,
            7,
            1,
            1,
            2,
        )

        form_layout.addWidget(
            stock_group
        )

        form_layout.addStretch()

        # ========================================================
        # BOUTONS
        # ========================================================

        buttons = QDialogButtonBox()

        cancel_button = buttons.addButton(
            "Annuler",
            QDialogButtonBox.RejectRole,
        )

        save_button = buttons.addButton(
            "Enregistrer le produit",
            QDialogButtonBox.AcceptRole,
        )

        cancel_button.setObjectName(
            "dialogCancel"
        )

        save_button.setObjectName(
            "dialogPrimary"
        )

        cancel_button.setCursor(
            Qt.PointingHandCursor
        )

        save_button.setCursor(
            Qt.PointingHandCursor
        )

        save_button.clicked.connect(
            self.validate_and_accept
        )

        cancel_button.clicked.connect(
            self.reject
        )

        main_layout.addWidget(
            buttons
        )

    # ============================================================
    # CHARGER PRODUIT
    # ============================================================

    def load_product(self):

        product = self.product

        self.name_input.setText(
            product.name or ""
        )

        self.category_input.setText(
            product.category or ""
        )

        self.select_combo(
            self.base_unit_combo,
            product.base_unit,
        )

        self.select_combo(
            self.packaging_combo,
            product.packaging,
        )

        self.medicine_check.setChecked(
            bool(
                product.is_medicine
            )
        )

        self.units_per_plaquette.setValue(
            int(
                getattr(
                    product,
                    "units_per_plaquette",
                    1,
                )
                or 1
            )
        )

        self.plaquettes_per_box.setValue(
            int(
                getattr(
                    product,
                    "plaquettes_per_box",
                    1,
                )
                or 1
            )
        )

        self.boxes_per_carton.setValue(
            int(
                getattr(
                    product,
                    "boxes_per_carton",
                    1,
                )
                or 1
            )
        )

        self.price_comprime.setValue(
            float(
                getattr(
                    product,
                    "price_per_comprime",
                    0,
                )
                or 0
            )
        )

        self.price_plaquette.setValue(
            float(
                getattr(
                    product,
                    "price_per_plaquette",
                    0,
                )
                or 0
            )
        )

        self.price_box.setValue(
            float(
                getattr(
                    product,
                    "price_per_box",
                    0,
                )
                or 0
            )
        )

        self.price_carton.setValue(
            float(
                getattr(
                    product,
                    "price_per_carton",
                    0,
                )
                or 0
            )
        )

        self.stock_input.setValue(
            int(
                getattr(
                    product,
                    "stock_units",
                    0,
                )
                or 0
            )
        )

        self.min_stock_input.setValue(
            int(
                getattr(
                    product,
                    "min_quantity",
                    0,
                )
                or 0
            )
        )

        self.batch_input.setText(
            getattr(
                product,
                "batch_number",
                "",
            )
            or ""
        )

        self.expiry_input.setText(
            self.format_date(
                getattr(
                    product,
                    "expiry_date",
                    None,
                )
            )
        )

        self.purchase_price_input.setValue(
            float(
                getattr(
                    product,
                    "purchase_price",
                    0,
                )
                or 0
            )
        )

        self.supplier_input.setText(
            getattr(
                product,
                "supplier",
                "",
            )
            or ""
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_and_accept(self):

        name = (
            self.name_input.text()
            .strip()
        )

        if not name:

            QMessageBox.warning(
                self,
                "Information",
                "Le nom du produit est obligatoire.",
            )

            self.name_input.setFocus()

            return

        expiry_text = (
            self.expiry_input.text()
            .strip()
        )

        expiry = None

        if expiry_text:

            try:

                expiry = datetime.strptime(
                    expiry_text,
                    "%Y-%m-%d",
                ).date()

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Date invalide",
                    (
                        "La date d'expiration doit être "
                        "au format AAAA-MM-JJ.\n\n"
                        "Exemple : 2027-12-31"
                    ),
                )

                self.expiry_input.setFocus()

                return

        if (
            self.stock_input.value() > 0
            and expiry is None
        ):

            QMessageBox.warning(
                self,
                "Date d'expiration obligatoire",
                (
                    "Un produit avec du stock doit "
                    "avoir une date d'expiration."
                ),
            )

            self.expiry_input.setFocus()

            return

        self.accept()

    # ============================================================
    # DONNÉES
    # ============================================================

    def get_data(self):

        expiry = None

        expiry_text = (
            self.expiry_input.text()
            .strip()
        )

        if expiry_text:

            try:

                expiry = datetime.strptime(
                    expiry_text,
                    "%Y-%m-%d",
                ).date()

            except ValueError:

                expiry = None

        stock = (
            self.stock_input.value()
        )

        return {
            "name":
                self.name_input.text().strip(),

            "category":
                self.category_input.text().strip(),

            "base_unit":
                self.base_unit_combo.currentText(),

            "packaging":
                self.packaging_combo.currentText(),

            "is_medicine":
                self.medicine_check.isChecked(),

            "units_per_plaquette":
                self.units_per_plaquette.value(),

            "plaquettes_per_box":
                self.plaquettes_per_box.value(),

            "boxes_per_carton":
                self.boxes_per_carton.value(),

            "quantity":
                stock,

            "stock_units":
                stock,

            "min_quantity":
                self.min_stock_input.value(),

            "price":
                self.price_comprime.value(),

            "price_per_comprime":
                self.price_comprime.value(),

            "price_per_plaquette":
                self.price_plaquette.value(),

            "price_per_box":
                self.price_box.value(),

            "price_per_carton":
                self.price_carton.value(),

            "batch_number":
                self.batch_input.text().strip(),

            "expiry_date":
                expiry,

            "purchase_price":
                self.purchase_price_input.value(),

            "purchase_quantity":
                self.purchase_quantity_input.value(),

            "purchase_unit":
                self.purchase_unit_combo.currentText(),

            "supplier":
                self.supplier_input.text().strip(),
        }

    # ============================================================
    # UTILITAIRES
    # ============================================================

    @staticmethod
    def select_combo(
        combo,
        value,
    ):

        if not value:
            return

        index = combo.findText(
            str(value),
            Qt.MatchFixedString,
        )

        if index >= 0:

            combo.setCurrentIndex(
                index
            )

    @staticmethod
    def format_date(
        value,
    ):

        if not value:

            return ""

        try:

            if isinstance(
                value,
                datetime,
            ):

                value = value.date()

            if isinstance(
                value,
                date,
            ):

                return value.strftime(
                    "%Y-%m-%d"
                )

            return str(value)

        except Exception:

            return str(value)


# =================================================================
# DIALOG DÉTAILS PRODUIT
# =================================================================


class ProductDetailsDialog(QDialog):
    """
    Fenêtre professionnelle de consultation d'un produit.
    """

    def __init__(
        self,
        parent=None,
        product=None,
        stock=0,
        batches=None,
    ):

        super().__init__(parent)

        self.product = product
        self.stock = stock
        self.batches = batches or []

        self.setWindowTitle(
            "Détails du produit"
        )

        self.setMinimumSize(
            760,
            620,
        )

        self.setup_ui()

    # ============================================================
    # UI
    # ============================================================

    def setup_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        layout.setSpacing(
            16
        )

        # --------------------------------------------------------
        # HEADER
        # --------------------------------------------------------

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            self.product.name or "-"
        )

        title.setStyleSheet(
            """
            font-size: 24px;
            font-weight: 800;
            color: #08192d;
            """
        )

        subtitle = QLabel(
            "Informations détaillées du produit"
        )

        subtitle.setStyleSheet(
            """
            color: #64748b;
            font-size: 12px;
            """
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header.addLayout(
            title_layout
        )

        header.addStretch()

        status = ProductPage.get_product_status(
            self.product,
            self.stock,
        )

        status_label = QLabel(
            status
        )

        if status == "Disponible":

            status_label.setStyleSheet(
                """
                background: #dcfce7;
                color: #166534;
                padding: 8px 14px;
                border-radius: 8px;
                font-weight: 800;
                """
            )

        elif status == "Stock faible":

            status_label.setStyleSheet(
                """
                background: #fef3c7;
                color: #92400e;
                padding: 8px 14px;
                border-radius: 8px;
                font-weight: 800;
                """
            )

        else:

            status_label.setStyleSheet(
                """
                background: #fee2e2;
                color: #991b1b;
                padding: 8px 14px;
                border-radius: 8px;
                font-weight: 800;
                """
            )

        header.addWidget(
            status_label
        )

        layout.addLayout(
            header
        )

        # --------------------------------------------------------
        # INFORMATIONS
        # --------------------------------------------------------

        info_group = QGroupBox(
            "Informations générales"
        )

        info_layout = QGridLayout(
            info_group
        )

        info_layout.setSpacing(
            12
        )

        self.add_info(
            info_layout,
            0,
            0,
            "Catégorie",
            self.product.category or "-",
        )

        self.add_info(
            info_layout,
            0,
            1,
            "Unité de base",
            self.product.base_unit or "-",
        )

        self.add_info(
            info_layout,
            1,
            0,
            "Conditionnement",
            self.product.packaging or "-",
        )

        self.add_info(
            info_layout,
            1,
            1,
            "Fournisseur",
            self.product.supplier or "-",
        )

        self.add_info(
            info_layout,
            2,
            0,
            "Stock actuel",
            ProductPage.format_number(
                self.stock
            ),
        )

        self.add_info(
            info_layout,
            2,
            1,
            "Stock minimum",
            ProductPage.format_number(
                getattr(
                    self.product,
                    "min_quantity",
                    0,
                )
                or 0
            ),
        )

        layout.addWidget(
            info_group
        )

        # --------------------------------------------------------
        # PRIX
        # --------------------------------------------------------

        price_group = QGroupBox(
            "Prix de vente"
        )

        price_layout = QGridLayout(
            price_group
        )

        self.add_info(
            price_layout,
            0,
            0,
            "Unité",
            ProductPage.format_money(
                getattr(
                    self.product,
                    "price_per_comprime",
                    0,
                )
            ),
        )

        self.add_info(
            price_layout,
            0,
            1,
            "Plaquette",
            ProductPage.format_money(
                getattr(
                    self.product,
                    "price_per_plaquette",
                    0,
                )
            ),
        )

        self.add_info(
            price_layout,
            1,
            0,
            "Boîte",
            ProductPage.format_money(
                getattr(
                    self.product,
                    "price_per_box",
                    0,
                )
            ),
        )

        self.add_info(
            price_layout,
            1,
            1,
            "Carton",
            ProductPage.format_money(
                getattr(
                    self.product,
                    "price_per_carton",
                    0,
                )
            ),
        )

        layout.addWidget(
            price_group
        )

        # --------------------------------------------------------
        # LOTS
        # --------------------------------------------------------

        batches_group = QGroupBox(
            f"Lots ({len(self.batches)})"
        )

        batches_layout = QVBoxLayout(
            batches_group
        )

        table = QTableWidget()

        table.setColumnCount(
            4
        )

        table.setHorizontalHeaderLabels(
            [
                "Lot",
                "Stock",
                "Expiration",
                "Fournisseur",
            ]
        )

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        table.verticalHeader().setVisible(
            False
        )

        table.setMinimumHeight(
            170
        )

        header = table.horizontalHeader()

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
            QHeaderView.Stretch,
        )

        for batch in self.batches:

            row = table.rowCount()

            table.insertRow(
                row
            )

            table.setItem(
                row,
                0,
                QTableWidgetItem(
                    batch.batch_number
                    or "-"
                ),
            )

            stock_item = QTableWidgetItem(
                ProductPage.format_number(
                    getattr(
                        batch,
                        "stock_units",
                        0,
                    )
                    or 0
                )
            )

            stock_item.setTextAlignment(
                Qt.AlignCenter
            )

            table.setItem(
                row,
                1,
                stock_item,
            )

            expiry = getattr(
                batch,
                "expiry_date",
                None,
            )

            expiry_item = QTableWidgetItem(
                ProductPage.format_date(
                    expiry
                )
            )

            expiry_item.setTextAlignment(
                Qt.AlignCenter
            )

            if (
                expiry
                and expiry < date.today()
            ):

                expiry_item.setForeground(
                    QBrush(
                        QColor(
                            "#dc2626"
                        )
                    )
                )

            table.setItem(
                row,
                2,
                expiry_item,
            )

            table.setItem(
                row,
                3,
                QTableWidgetItem(
                    getattr(
                        batch,
                        "supplier",
                        None,
                    )
                    or "-"
                ),
            )

        batches_layout.addWidget(
            table
        )

        layout.addWidget(
            batches_group
        )

        # --------------------------------------------------------
        # BOUTON
        # --------------------------------------------------------

        close_button = QPushButton(
            "Fermer"
        )

        close_button.setObjectName(
            "dialogCancel"
        )

        close_button.setCursor(
            Qt.PointingHandCursor
        )

        close_button.clicked.connect(
            self.accept
        )

        layout.addWidget(
            close_button
        )

    # ============================================================
    # INFO
    # ============================================================

    @staticmethod
    def add_info(
        layout,
        row,
        column,
        label,
        value,
    ):

        container = QFrame()

        container.setStyleSheet(
            """
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            """
        )

        box = QVBoxLayout(
            container
        )

        box.setContentsMargins(
            12,
            9,
            12,
            9,
        )

        label_widget = QLabel(
            label.upper()
        )

        label_widget.setStyleSheet(
            """
            color: #94a3b8;
            font-size: 9px;
            font-weight: 800;
            """
        )

        value_widget = QLabel(
            str(value)
        )

        value_widget.setStyleSheet(
            """
            color: #08192d;
            font-size: 13px;
            font-weight: 700;
            """
        )

        value_widget.setWordWrap(
            True
        )

        box.addWidget(
            label_widget
        )

        box.addWidget(
            value_widget
        )

        layout.addWidget(
            container,
            row,
            column,
        )