
from datetime import date, datetime

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
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QDoubleSpinBox,
    QScrollArea,
    QFrame,
    QMessageBox,
    QAbstractItemView,
    QHeaderView,
)

from sqlalchemy import inspect

from database.database import (
    SessionLocal,
    get_stock_display,
    get_units_for_packaging,
    get_price_for_packaging,
    update_display_quantity,
)

from database.models import (
    Product,
    Sale,
    SaleItem,
    ProductBatch,
)


class SalesPage(QWidget):
    """
    Page de gestion des ventes.

    Fonctionnalités :

    - Recherche des médicaments
    - Sélection du conditionnement
    - Prix automatique selon le conditionnement
    - Conversion en unités de base
    - Panier
    - Vérification du stock
    - Gestion des lots
    - FEFO : First Expired, First Out
    - Diminution automatique du stock lors de la vente
    - Mise à jour du stock des lots
    - Mise à jour du stock global du produit
    - Vente répartie sur plusieurs lots
    - Génération de facture PDF
    """

    # =========================================================
    # CONSTANTES
    # =========================================================

    PACKAGING = [
        "Comprimé",
        "Plaquette",
        "Boîte",
        "Carton",
    ]

    PAYMENT_METHODS = [
        "Espèces",
        "Mobile Money",
        "Carte bancaire",
        "Virement",
    ]

    # =========================================================
    # INITIALISATION
    # =========================================================

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cart = []

        self.setup_ui()
        self.search_products()

    # =========================================================
    # INTERFACE
    # =========================================================

    def setup_ui(self):
        self.setObjectName("SalesPage")

        self.setStyleSheet(
            """
            QWidget#SalesPage {
                background-color: #f5f7fb;
                color: #08192d;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QWidget#scrollContent {
                background-color: #f5f7fb;
            }

            QFrame.card {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 14px;
            }

            QLabel.title {
                color: #08192d;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel.subtitle {
                color: #64748b;
                font-size: 13px;
            }

            QLabel.sectionTitle {
                color: #08192d;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel.fieldLabel {
                color: #475569;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel.valueLabel {
                color: #08192d;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel.totalLabel {
                color: #08192d;
                font-size: 24px;
                font-weight: 800;
            }

            QLineEdit,
            QComboBox,
            QDoubleSpinBox {
                min-height: 42px;
                border: 1px solid #d8dee8;
                border-radius: 9px;
                background-color: white;
                padding: 0 12px;
                color: #08192d;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDoubleSpinBox:focus {
                border: 2px solid #facc15;
            }

            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }

            QListWidget::item {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 6px;
            }

            QListWidget::item:hover {
                background-color: #fffbea;
                border: 1px solid #facc15;
            }

            QListWidget::item:selected {
                background-color: #fff7cc;
                border: 1px solid #facc15;
                color: #08192d;
            }

            QTableWidget {
                background-color: white;
                border: none;
                gridline-color: #edf0f4;
                outline: none;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #edf0f4;
            }

            QTableWidget::item:selected {
                background-color: #fff8d8;
                color: #08192d;
            }

            QHeaderView::section {
                background-color: #08192d;
                color: white;
                padding: 11px 8px;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }

            QPushButton {
                min-height: 40px;
                border-radius: 9px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton.primary {
                background-color: #facc15;
                color: #08192d;
                border: none;
            }

            QPushButton.primary:hover {
                background-color: #eab308;
            }

            QPushButton.primary:pressed {
                background-color: #ca8a04;
            }

            QPushButton.secondary {
                background-color: #08192d;
                color: white;
                border: none;
            }

            QPushButton.secondary:hover {
                background-color: #102b49;
            }

            QPushButton.danger {
                background-color: #fee2e2;
                color: #b91c1c;
                border: none;
                min-height: 32px;
                min-width: 32px;
                padding: 0;
            }

            QPushButton.danger:hover {
                background-color: #fecaca;
            }

            QPushButton.small {
                background-color: #eef2f7;
                color: #08192d;
                border: none;
                min-height: 30px;
                min-width: 30px;
                padding: 0;
            }

            QPushButton.small:hover {
                background-color: #e2e8f0;
            }

            QFrame.separator {
                background-color: #e5e7eb;
                max-height: 1px;
            }
            """
        )

        # =====================================================
        # SCROLL
        # =====================================================

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        scroll_area.setWidget(scroll_content)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll_area)

        # =====================================================
        # HEADER
        # =====================================================

        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel("Nouvelle vente")
        title.setProperty("class", "title")

        subtitle = QLabel(
            "Sélectionnez les médicaments, choisissez le "
            "conditionnement et validez la vente."
        )
        subtitle.setProperty("class", "subtitle")

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        self.cart_count_label = QLabel("0 article")

        self.cart_count_label.setStyleSheet(
            """
            QLabel {
                background-color: #08192d;
                color: white;
                border-radius: 18px;
                padding: 8px 14px;
                font-weight: 700;
            }
            """
        )

        header_layout.addWidget(self.cart_count_label)

        main_layout.addLayout(header_layout)

        # =====================================================
        # PRODUITS
        # =====================================================

        products_card = QFrame()
        products_card.setProperty("class", "card")

        products_layout = QVBoxLayout(products_card)
        products_layout.setContentsMargins(18, 18, 18, 18)
        products_layout.setSpacing(14)

        products_title = QLabel("Sélection des médicaments")
        products_title.setProperty("class", "sectionTitle")

        products_layout.addWidget(products_title)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher un médicament..."
        )
        self.search_input.setClearButtonEnabled(True)

        self.search_input.textChanged.connect(
            self.search_products
        )

        self.search_input.returnPressed.connect(
            self.add_first_product
        )

        search_layout.addWidget(self.search_input)

        self.packaging_combo = QComboBox()
        self.packaging_combo.addItems(self.PACKAGING)
        self.packaging_combo.setMinimumWidth(160)

        self.packaging_combo.currentTextChanged.connect(
            self.on_packaging_changed
        )

        search_layout.addWidget(self.packaging_combo)

        self.add_product_button = QPushButton("+ Ajouter")
        self.add_product_button.setProperty(
            "class",
            "primary",
        )

        self.add_product_button.clicked.connect(
            self.add_selected_product
        )

        search_layout.addWidget(self.add_product_button)

        products_layout.addLayout(search_layout)

        self.product_list = QListWidget()
        self.product_list.setMinimumHeight(220)
        self.product_list.setMaximumHeight(350)

        self.product_list.itemDoubleClicked.connect(
            lambda _item: self.add_selected_product()
        )

        self.product_list.currentItemChanged.connect(
            self.on_product_selected
        )

        products_layout.addWidget(self.product_list)

        main_layout.addWidget(products_card)

        # =====================================================
        # PANIER
        # =====================================================

        cart_card = QFrame()
        cart_card.setProperty("class", "card")

        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(18, 18, 18, 18)
        cart_layout.setSpacing(14)

        cart_title_layout = QHBoxLayout()

        cart_title = QLabel("Panier")
        cart_title.setProperty("class", "sectionTitle")

        self.cart_status_label = QLabel("Aucun article")

        self.cart_status_label.setStyleSheet(
            """
            QLabel {
                color: #64748b;
                font-size: 12px;
                font-weight: 600;
            }
            """
        )

        cart_title_layout.addWidget(cart_title)
        cart_title_layout.addStretch()
        cart_title_layout.addWidget(self.cart_status_label)

        cart_layout.addLayout(cart_title_layout)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)

        self.cart_table.setHorizontalHeaderLabels(
            [
                "Médicament",
                "Conditionnement",
                "Quantité",
                "Prix unitaire",
                "Total",
                "Action",
            ]
        )

        self.cart_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.cart_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.cart_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.cart_table.verticalHeader().setVisible(False)

        header = self.cart_table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in [1, 2, 3, 4]:
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Fixed,
        )

        self.cart_table.setColumnWidth(5, 90)
        self.cart_table.setMinimumHeight(250)

        cart_layout.addWidget(self.cart_table)

        main_layout.addWidget(cart_card)

        # =====================================================
        # BAS
        # =====================================================

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(18)

        # =====================================================
        # PAIEMENT
        # =====================================================

        payment_card = QFrame()
        payment_card.setProperty("class", "card")

        payment_layout = QVBoxLayout(payment_card)
        payment_layout.setContentsMargins(18, 18, 18, 18)
        payment_layout.setSpacing(14)

        payment_title = QLabel("Paiement")
        payment_title.setProperty("class", "sectionTitle")

        payment_layout.addWidget(payment_title)

        payment_grid = QGridLayout()
        payment_grid.setHorizontalSpacing(12)
        payment_grid.setVerticalSpacing(10)

        payment_label = QLabel("Mode de paiement")
        payment_label.setProperty("class", "fieldLabel")

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(self.PAYMENT_METHODS)

        payment_grid.addWidget(payment_label, 0, 0)
        payment_grid.addWidget(self.payment_combo, 1, 0)

        discount_label = QLabel("Remise")
        discount_label.setProperty("class", "fieldLabel")

        self.discount_input = QDoubleSpinBox()
        self.discount_input.setDecimals(2)
        self.discount_input.setMinimum(0.0)
        self.discount_input.setMaximum(999999999.0)
        self.discount_input.setSingleStep(1.0)
        self.discount_input.setValue(0.0)
        self.discount_input.setSuffix(" FC")

        self.discount_input.valueChanged.connect(
            self.update_totals
        )

        payment_grid.addWidget(discount_label, 0, 1)
        payment_grid.addWidget(self.discount_input, 1, 1)

        payment_layout.addLayout(payment_grid)

        payment_info = QLabel(
            "Le stock est contrôlé une dernière fois lors "
            "de la validation. Les lots expirant le plus tôt "
            "sont consommés en priorité."
        )

        payment_info.setWordWrap(True)

        payment_info.setStyleSheet(
            """
            QLabel {
                color: #64748b;
                font-size: 12px;
            }
            """
        )

        payment_layout.addWidget(payment_info)
        payment_layout.addStretch()

        bottom_layout.addWidget(payment_card, 1)

        # =====================================================
        # RESUME
        # =====================================================

        summary_card = QFrame()
        summary_card.setProperty("class", "card")

        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(18, 18, 18, 18)
        summary_layout.setSpacing(12)

        summary_title = QLabel("Résumé")
        summary_title.setProperty("class", "sectionTitle")

        summary_layout.addWidget(summary_title)

        self.subtotal_label = QLabel("0.00")
        self.subtotal_label.setProperty("class", "valueLabel")

        self.discount_label = QLabel("0.00")
        self.discount_label.setProperty("class", "valueLabel")

        self.total_label = QLabel("0.00")
        self.total_label.setProperty("class", "totalLabel")

        self._add_summary_row(
            summary_layout,
            "Sous-total",
            self.subtotal_label,
        )

        self._add_summary_row(
            summary_layout,
            "Remise",
            self.discount_label,
        )

        separator = QFrame()
        separator.setProperty("class", "separator")

        summary_layout.addWidget(separator)

        self._add_summary_row(
            summary_layout,
            "Total à payer",
            self.total_label,
        )

        summary_layout.addStretch()

        self.validate_button = QPushButton(
            "✓ Valider la vente"
        )

        self.validate_button.setProperty(
            "class",
            "primary",
        )

        self.validate_button.setMinimumHeight(48)

        self.validate_button.clicked.connect(
            self.validate_sale
        )

        summary_layout.addWidget(self.validate_button)

        bottom_layout.addWidget(summary_card, 1)

        main_layout.addLayout(bottom_layout)
        main_layout.addStretch()

    # =========================================================
    # HELPERS
    # =========================================================

    def _add_summary_row(
        self,
        layout,
        label_text,
        value_label,
    ):
        row = QHBoxLayout()

        label = QLabel(label_text)
        label.setProperty("class", "fieldLabel")

        row.addWidget(label)
        row.addStretch()
        row.addWidget(value_label)

        layout.addLayout(row)

    def _format_money(self, value):
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _get_cart_quantity(self):
        total = 0

        for item in self.cart:
            try:
                total += int(item["quantity"])
            except (KeyError, TypeError, ValueError):
                pass

        return total

    # =========================================================
    # CONVERSION
    # =========================================================

    def _get_base_units_for_quantity(
        self,
        product,
        packaging,
        quantity,
    ):
        units_per_packaging = get_units_for_packaging(
            product,
            packaging,
        )

        if units_per_packaging <= 0:
            raise ValueError(
                f"Le conditionnement « {packaging} » "
                "possède une conversion invalide."
            )

        return int(
            quantity * units_per_packaging
        )

    # =========================================================
    # LOTS
    # =========================================================

    def _get_product_batches(
        self,
        session,
        product_id,
        include_expired=False,
    ):
        """
        Retourne les lots disponibles en ordre FEFO.
        """

        try:
            batches = (
                session.query(ProductBatch)
                .filter(
                    ProductBatch.product_id == product_id
                )
                .order_by(
                    ProductBatch.expiry_date.asc(),
                    ProductBatch.id.asc(),
                )
                .all()
            )

        except Exception:
            return []

        result = []
        today = date.today()

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

            expiry = getattr(
                batch,
                "expiry_date",
                None,
            )

            if isinstance(expiry, datetime):
                expiry = expiry.date()

            if (
                not include_expired
                and expiry is not None
                and expiry < today
            ):
                continue

            result.append(batch)

        return result

    def _get_valid_batch_stock(
        self,
        session,
        product_id,
    ):
        batches = self._get_product_batches(
            session,
            product_id,
            include_expired=False,
        )

        return sum(
            int(
                getattr(
                    batch,
                    "stock_units",
                    0,
                )
                or 0
            )
            for batch in batches
        )

    def _format_expiry(self, expiry):
        if expiry is None:
            return "Date inconnue"

        if isinstance(expiry, datetime):
            expiry = expiry.date()

        if isinstance(expiry, date):
            return expiry.strftime("%d/%m/%Y")

        return str(expiry)

    # =========================================================
    # FEFO
    # =========================================================

    def _simulate_fefo(
        self,
        session,
        product,
        required_units,
    ):
        """
        Simule la consommation FEFO sans modifier la base.
        """

        if required_units <= 0:
            return []

        batches = self._get_product_batches(
            session,
            product.id,
            include_expired=False,
        )

        remaining = int(required_units)
        allocations = []

        for batch in batches:

            if remaining <= 0:
                break

            available = int(
                getattr(
                    batch,
                    "stock_units",
                    0,
                )
                or 0
            )

            if available <= 0:
                continue

            consumed = min(
                available,
                remaining,
            )

            allocations.append(
                {
                    "batch": batch,
                    "units": consumed,
                }
            )

            remaining -= consumed

        if remaining > 0:
            return None

        return allocations

    # =========================================================
    # RECHERCHE
    # =========================================================

    def search_products(self, text=None):

        if text is None:
            text = self.search_input.text()

        text = text.strip()

        self.product_list.clear()

        session = SessionLocal()

        try:

            query = session.query(Product)

            if text:
                query = query.filter(
                    Product.name.ilike(
                        f"%{text}%"
                    )
                )

            products = (
                query
                .order_by(Product.name.asc())
                .limit(100)
                .all()
            )

            for product in products:
                self._add_product_to_list(product)

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de charger "
                    "les produits.\n\n"
                    f"{error}"
                ),
            )

        finally:
            session.close()

    def _add_product_to_list(self, product):

        try:
            stock_text = get_stock_display(product)
        except Exception:
            stock_text = "Stock indisponible"

        try:
            price = get_price_for_packaging(
                product,
                self.packaging_combo.currentText(),
            )
        except Exception:
            price = getattr(
                product,
                "price",
                0.0,
            ) or 0.0

        item = QListWidgetItem()

        item.setData(
            Qt.ItemDataRole.UserRole,
            product.id,
        )

        item.setText(
            f"{product.name}\n"
            f"Stock : {stock_text}    •    "
            f"{self.packaging_combo.currentText()} : "
            f"{self._format_money(price)}"
        )

        self.product_list.addItem(item)

    # =========================================================
    # PRODUIT SELECTIONNE
    # =========================================================

    def on_product_selected(
        self,
        current_item,
        previous_item=None,
    ):
        if current_item is None:
            return

        product_id = current_item.data(
            Qt.ItemDataRole.UserRole
        )

        if product_id is None:
            return

        self._refresh_selected_product_text(
            product_id
        )

    def on_packaging_changed(self, packaging):

        current_item = self.product_list.currentItem()

        if current_item is None:
            return

        product_id = current_item.data(
            Qt.ItemDataRole.UserRole
        )

        if product_id is None:
            return

        self._refresh_selected_product_text(
            product_id
        )

    def _refresh_selected_product_text(
        self,
        product_id,
    ):
        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(Product.id == product_id)
                .first()
            )

            if product is None:
                return

            try:
                stock_text = get_stock_display(product)
            except Exception:
                stock_text = "Stock indisponible"

            try:
                price = get_price_for_packaging(
                    product,
                    self.packaging_combo.currentText(),
                )
            except Exception:
                price = getattr(
                    product,
                    "price",
                    0.0,
                ) or 0.0

            item = self.product_list.currentItem()

            if item is not None:
                item.setText(
                    f"{product.name}\n"
                    f"Stock : {stock_text}    •    "
                    f"{self.packaging_combo.currentText()} : "
                    f"{self._format_money(price)}"
                )

        finally:
            session.close()

    # =========================================================
    # AJOUT PRODUIT
    # =========================================================

    def add_first_product(self):

        if self.product_list.count() == 0:
            return

        self.product_list.setCurrentRow(0)
        self.add_selected_product()

    def add_selected_product(self):

        item = self.product_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "Produit requis",
                "Veuillez sélectionner un médicament.",
            )
            return

        product_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if product_id is None:
            return

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(Product.id == product_id)
                .first()
            )

            if product is None:
                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Le médicament sélectionné n'existe plus.",
                )
                return

            packaging = self.packaging_combo.currentText()

            self._add_product_to_cart(
                product,
                packaging,
                session,
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible d'ajouter le produit.\n\n"
                    f"{error}"
                ),
            )

        finally:
            session.close()

    def _add_product_to_cart(
        self,
        product,
        packaging,
        session=None,
    ):

        if session is None:
            session = SessionLocal()
            close_session = True
        else:
            close_session = False

        try:

            units_per_packaging = get_units_for_packaging(
                product,
                packaging,
            )

            if units_per_packaging <= 0:
                raise ValueError(
                    f"Le conditionnement "
                    f"« {packaging} » est invalide."
                )

            valid_stock = self._get_valid_batch_stock(
                session,
                product.id,
            )

            if valid_stock <= 0:
                valid_stock = int(
                    getattr(
                        product,
                        "stock_units",
                        0,
                    )
                    or 0
                )

            available_packages = (
                valid_stock // units_per_packaging
            )

            if available_packages <= 0:
                QMessageBox.warning(
                    self,
                    "Stock insuffisant",
                    (
                        f"Le médicament "
                        f"« {product.name} » "
                        f"ne possède pas assez de stock "
                        f"pour vendre une "
                        f"{packaging.lower()}."
                    ),
                )
                return

            try:
                unit_price = get_price_for_packaging(
                    product,
                    packaging,
                )
            except Exception:
                unit_price = getattr(
                    product,
                    "price",
                    0.0,
                ) or 0.0

            for item in self.cart:

                if (
                    item["product_id"] == product.id
                    and item["sale_unit"] == packaging
                ):

                    new_quantity = (
                        item["quantity"] + 1
                    )

                    if new_quantity > available_packages:
                        QMessageBox.warning(
                            self,
                            "Stock insuffisant",
                            (
                                f"Stock insuffisant "
                                f"pour {product.name}.\n\n"
                                f"Disponible : "
                                f"{available_packages} "
                                f"{packaging.lower()}."
                            ),
                        )
                        return

                    item["quantity"] = new_quantity

                    self.update_cart_ui()
                    return

            self.cart.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "sale_unit": packaging,
                    "quantity": 1,
                    "unit_price": float(unit_price),
                }
            )

            self.update_cart_ui()

        finally:

            if close_session:
                session.close()

    # =========================================================
    # PANIER
    # =========================================================

    def update_cart_ui(self):

        self.cart_table.setRowCount(0)

        for row, cart_item in enumerate(self.cart):

            self.cart_table.insertRow(row)
            self.cart_table.setRowHeight(row, 58)

            product_name = cart_item["product_name"]
            packaging = cart_item["sale_unit"]

            quantity = int(cart_item["quantity"])

            unit_price = float(
                cart_item["unit_price"]
            )

            line_total = quantity * unit_price

            product_cell = QTableWidgetItem(
                product_name
            )

            self.cart_table.setItem(
                row,
                0,
                product_cell,
            )

            packaging_combo = QComboBox()
            packaging_combo.addItems(self.PACKAGING)

            packaging_combo.blockSignals(True)
            packaging_combo.setCurrentText(packaging)
            packaging_combo.blockSignals(False)

            packaging_combo.currentTextChanged.connect(
                lambda value, index=row:
                self.change_packaging(index, value)
            )

            self.cart_table.setCellWidget(
                row,
                1,
                packaging_combo,
            )

            quantity_widget = QWidget()

            quantity_layout = QHBoxLayout(
                quantity_widget
            )

            quantity_layout.setContentsMargins(
                4,
                2,
                4,
                2,
            )

            quantity_layout.setSpacing(4)

            minus_button = QPushButton("−")
            minus_button.setProperty(
                "class",
                "small",
            )

            plus_button = QPushButton("+")
            plus_button.setProperty(
                "class",
                "small",
            )

            quantity_label = QLabel(str(quantity))

            quantity_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            quantity_label.setMinimumWidth(28)

            minus_button.clicked.connect(
                lambda _checked=False, index=row:
                self.change_quantity(index, -1)
            )

            plus_button.clicked.connect(
                lambda _checked=False, index=row:
                self.change_quantity(index, 1)
            )

            quantity_layout.addWidget(minus_button)
            quantity_layout.addWidget(quantity_label)
            quantity_layout.addWidget(plus_button)

            self.cart_table.setCellWidget(
                row,
                2,
                quantity_widget,
            )

            price_cell = QTableWidgetItem(
                self._format_money(unit_price)
            )

            price_cell.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.cart_table.setItem(
                row,
                3,
                price_cell,
            )

            total_cell = QTableWidgetItem(
                self._format_money(line_total)
            )

            total_cell.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            total_cell.setFont(
                QFont(
                    "Arial",
                    10,
                    QFont.Weight.Bold,
                )
            )

            self.cart_table.setItem(
                row,
                4,
                total_cell,
            )

            remove_button = QPushButton("×")

            remove_button.setProperty(
                "class",
                "danger",
            )

            remove_button.setToolTip(
                "Supprimer du panier"
            )

            remove_button.clicked.connect(
                lambda _checked=False, index=row:
                self.remove_cart_item(index)
            )

            self.cart_table.setCellWidget(
                row,
                5,
                remove_button,
            )

        self.update_cart_count()
        self.update_totals()

    def update_cart_count(self):

        total_quantity = self._get_cart_quantity()
        line_count = len(self.cart)

        if line_count == 0:

            self.cart_count_label.setText(
                "0 article"
            )

            self.cart_status_label.setText(
                "Aucun article"
            )

        elif total_quantity == 1:

            self.cart_count_label.setText(
                "1 article"
            )

            self.cart_status_label.setText(
                "1 article dans le panier"
            )

        else:

            self.cart_count_label.setText(
                f"{total_quantity} articles"
            )

            self.cart_status_label.setText(
                f"{line_count} ligne(s) • "
                f"{total_quantity} conditionnement(s)"
            )

    # =========================================================
    # QUANTITE
    # =========================================================

    def change_quantity(
        self,
        index,
        difference,
    ):

        if index < 0 or index >= len(self.cart):
            return

        item = self.cart[index]

        new_quantity = (
            item["quantity"] + difference
        )

        if new_quantity <= 0:
            self.remove_cart_item(index)
            return

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.id == item["product_id"]
                )
                .first()
            )

            if product is None:
                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Ce produit n'existe plus.",
                )
                return

            units_per_packaging = get_units_for_packaging(
                product,
                item["sale_unit"],
            )

            available_stock = self._get_valid_batch_stock(
                session,
                product.id,
            )

            if available_stock <= 0:
                available_stock = int(
                    getattr(
                        product,
                        "stock_units",
                        0,
                    )
                    or 0
                )

            available_packages = (
                available_stock // units_per_packaging
            )

            if new_quantity > available_packages:

                QMessageBox.warning(
                    self,
                    "Stock insuffisant",
                    (
                        f"Stock disponible pour "
                        f"{product.name} : "
                        f"{available_packages} "
                        f"{item['sale_unit'].lower()}."
                    ),
                )

                return

            item["quantity"] = new_quantity

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de modifier "
                    "la quantité.\n\n"
                    f"{error}"
                ),
            )

        finally:
            session.close()

        self.update_cart_ui()

    # =========================================================
    # CONDITIONNEMENT
    # =========================================================

    def change_packaging(
        self,
        index,
        new_packaging,
    ):

        if index < 0 or index >= len(self.cart):
            return

        item = self.cart[index]

        if item["sale_unit"] == new_packaging:
            return

        session = SessionLocal()

        try:

            product = (
                session.query(Product)
                .filter(
                    Product.id == item["product_id"]
                )
                .first()
            )

            if product is None:
                QMessageBox.warning(
                    self,
                    "Produit introuvable",
                    "Ce produit n'existe plus.",
                )
                return

            units_per_packaging = get_units_for_packaging(
                product,
                new_packaging,
            )

            if units_per_packaging <= 0:
                raise ValueError(
                    "Conversion de conditionnement invalide."
                )

            available_stock = self._get_valid_batch_stock(
                session,
                product.id,
            )

            if available_stock <= 0:
                available_stock = int(
                    getattr(
                        product,
                        "stock_units",
                        0,
                    )
                    or 0
                )

            available_packages = (
                available_stock // units_per_packaging
            )

            if item["quantity"] > available_packages:

                QMessageBox.warning(
                    self,
                    "Stock insuffisant",
                    (
                        f"Le conditionnement "
                        f"« {new_packaging} » "
                        f"ne permet pas une quantité "
                        f"de {item['quantity']}.\n\n"
                        f"Disponible : "
                        f"{available_packages} "
                        f"{new_packaging.lower()}."
                    ),
                )

                self.update_cart_ui()
                return

            unit_price = get_price_for_packaging(
                product,
                new_packaging,
            )

            item["sale_unit"] = new_packaging
            item["unit_price"] = float(unit_price)

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de changer "
                    "le conditionnement.\n\n"
                    f"{error}"
                ),
            )

        finally:
            session.close()

        self.update_cart_ui()

    # =========================================================
    # SUPPRESSION
    # =========================================================

    def remove_cart_item(self, index):

        if index < 0 or index >= len(self.cart):
            return

        item = self.cart[index]

        answer = QMessageBox.question(
            self,
            "Supprimer l'article",
            (
                f"Voulez-vous supprimer "
                f"« {item['product_name']} » "
                f"du panier ?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.cart.pop(index)

        self.update_cart_ui()

    # =========================================================
    # CALCULS
    # =========================================================

    def calculate_subtotal(self):

        subtotal = 0.0

        for item in self.cart:

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            subtotal += quantity * unit_price

        return subtotal

    def update_totals(self):

        subtotal = self.calculate_subtotal()

        discount = self.discount_input.value()

        total = max(
            0.0,
            subtotal - discount,
        )

        self.subtotal_label.setText(
            self._format_money(subtotal)
        )

        self.discount_label.setText(
            self._format_money(discount)
        )

        self.total_label.setText(
            self._format_money(total)
        )

    # =========================================================
    # VERIFICATION STOCK
    # =========================================================

    def check_stock_before_sale(self):

        session = SessionLocal()

        try:

            # -------------------------------------------------
            # Vérification de chaque ligne
            # -------------------------------------------------

            for item in self.cart:

                product = (
                    session.query(Product)
                    .filter(
                        Product.id == item["product_id"]
                    )
                    .first()
                )

                if product is None:
                    return (
                        f"Le produit "
                        f"« {item['product_name']} » "
                        f"n'existe plus."
                    )

                required_units = (
                    self._get_base_units_for_quantity(
                        product,
                        item["sale_unit"],
                        item["quantity"],
                    )
                )

                valid_stock = self._get_valid_batch_stock(
                    session,
                    product.id,
                )

                if valid_stock <= 0:
                    valid_stock = int(
                        getattr(
                            product,
                            "stock_units",
                            0,
                        )
                        or 0
                    )

                if valid_stock < required_units:

                    return (
                        f"Stock insuffisant pour "
                        f"« {product.name} ».\n\n"
                        f"Demandé : "
                        f"{required_units} unités de base\n"
                        f"Disponible : "
                        f"{valid_stock} unités de base"
                    )

                batches = self._get_product_batches(
                    session,
                    product.id,
                    include_expired=False,
                )

                if not batches:

                    return (
                        f"Le médicament "
                        f"« {product.name} » "
                        f"n'a aucun lot disponible "
                        f"et non expiré."
                    )

                allocations = self._simulate_fefo(
                    session,
                    product,
                    required_units,
                )

                if allocations is None:

                    return (
                        f"Le stock disponible "
                        f"en lots valides est "
                        f"insuffisant pour "
                        f"« {product.name} »."
                    )

            return None

        except Exception as error:

            return (
                "Impossible de vérifier le stock.\n\n"
                f"{error}"
            )

        finally:
            session.close()

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate_sale(self):

        if not self.cart:

            QMessageBox.warning(
                self,
                "Panier vide",
                "Ajoutez au moins un médicament au panier.",
            )

            return

        subtotal = self.calculate_subtotal()

        discount = self.discount_input.value()

        if discount > subtotal:

            QMessageBox.warning(
                self,
                "Remise invalide",
                (
                    "La remise ne peut pas être "
                    "supérieure au sous-total."
                ),
            )

            return

        total = max(
            0.0,
            subtotal - discount,
        )

        payment_method = self.payment_combo.currentText()

        stock_error = self.check_stock_before_sale()

        if stock_error:

            QMessageBox.warning(
                self,
                "Stock insuffisant",
                stock_error,
            )

            return

        confirmation = QMessageBox.question(
            self,
            "Confirmer la vente",
            (
                "Voulez-vous confirmer cette vente ?\n\n"
                f"Sous-total : "
                f"{self._format_money(subtotal)}\n"
                f"Remise : "
                f"{self._format_money(discount)}\n"
                f"Total : "
                f"{self._format_money(total)}\n\n"
                f"Paiement : "
                f"{payment_method}"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self.save_sale(
            total=total,
            payment_method=payment_method,
        )

    # =========================================================
    # CREATION SALE ITEM
    # =========================================================

    def _create_sale_item(
        self,
        session,
        sale,
        product,
        cart_item,
        allocation,
    ):
        """
        Crée une ligne SaleItem correspondant
        à une consommation d'un lot.
        """

        batch = allocation["batch"]

        consumed_units = int(
            allocation["units"]
        )

        units_per_packaging = get_units_for_packaging(
            product,
            cart_item["sale_unit"],
        )

        if units_per_packaging <= 0:
            raise ValueError(
                "Conversion de conditionnement invalide."
            )

        package_quantity_float = (
            consumed_units / units_per_packaging
        )

        """
        Une vente peut être répartie sur plusieurs lots.

        Exemple :

        Vente = 2 boîtes
        1 boîte = 100 comprimés

        Lot A = 150 comprimés
        Lot B = 150 comprimés

        FEFO :
        Lot A -> 150 comprimés
        Lot B -> 50 comprimés

        Le deuxième lot ne représente donc pas
        une boîte complète.

        Pour éviter une erreur de quantité,
        on enregistre stock_units comme quantité
        réelle consommée et quantity comme
        équivalent de conditionnement.
        """

        kwargs = {
            "sale": sale,
            "product_id": product.id,
            "quantity": package_quantity_float,
            "unit_price": float(
                cart_item["unit_price"]
            ),
            "sale_unit": cart_item["sale_unit"],
            "stock_units": consumed_units,
        }

        # -----------------------------------------------------
        # batch_id si présent dans le modèle
        # -----------------------------------------------------

        try:

            mapper = inspect(SaleItem)

            has_batch_id = any(
                column.key == "batch_id"
                for column in mapper.columns
            )

            if has_batch_id:
                kwargs["batch_id"] = batch.id

        except Exception:
            pass

        return SaleItem(**kwargs)

    # =========================================================
    # ENREGISTREMENT VENTE
    # =========================================================

    def save_sale(
        self,
        total,
        payment_method,
    ):
        """
        Enregistre la vente et diminue le stock.

        IMPORTANT :

        La vente et la diminution du stock
        sont effectuées dans la même transaction.

        Si une erreur arrive :

            rollback()

        donc :

            aucune vente
            aucun stock modifié
        """

        session = SessionLocal()

        try:

            # =================================================
            # NUMERO FACTURE
            # =================================================

            invoice_number = (
                "FAC-"
                + datetime.now().strftime(
                    "%Y%m%d-%H%M%S-%f"
                )
            )

            # =================================================
            # CREATION SALE
            # =================================================

            sale = Sale(
                invoice_number=invoice_number,
                client_name="Client comptant",
                payment_method=payment_method,
                total=float(total),
            )

            session.add(sale)

            session.flush()

            # =================================================
            # TRAITEMENT DES ARTICLES
            # =================================================

            for cart_item in self.cart:

                product = (
                    session.query(Product)
                    .filter(
                        Product.id
                        == cart_item["product_id"]
                    )
                    .first()
                )

                if product is None:
                    raise ValueError(
                        (
                            f"Le produit "
                            f"« {cart_item['product_name']} » "
                            f"est introuvable."
                        )
                    )

                quantity = int(
                    cart_item["quantity"]
                )

                if quantity <= 0:
                    raise ValueError(
                        "La quantité vendue doit être "
                        "supérieure à zéro."
                    )

                # =================================================
                # CONVERSION EN UNITES DE BASE
                # =================================================

                required_units = (
                    self._get_base_units_for_quantity(
                        product,
                        cart_item["sale_unit"],
                        quantity,
                    )
                )

                if required_units <= 0:
                    raise ValueError(
                        (
                            f"La quantité calculée "
                            f"pour « {product.name} » "
                            "est invalide."
                        )
                    )

                # =================================================
                # FEFO
                # =================================================

                allocations = self._simulate_fefo(
                    session,
                    product,
                    required_units,
                )

                if allocations is None:

                    raise ValueError(
                        (
                            f"Stock insuffisant pour "
                            f"« {product.name} »."
                        )
                    )

                # =================================================
                # CALCUL TOTAL CONSOMME
                # =================================================

                total_consumed = 0

                # =================================================
                # CONSOMMATION DES LOTS
                # =================================================

                for allocation in allocations:

                    batch = allocation["batch"]

                    consumed_units = int(
                        allocation["units"]
                    )

                    # ---------------------------------------------
                    # VERIFICATION EXPIRATION
                    # ---------------------------------------------

                    expiry = getattr(
                        batch,
                        "expiry_date",
                        None,
                    )

                    if isinstance(
                        expiry,
                        datetime,
                    ):
                        expiry = expiry.date()

                    if (
                        expiry is not None
                        and expiry < date.today()
                    ):
                        raise ValueError(
                            (
                                f"Le lot "
                                f"{getattr(batch, 'batch_number', 'inconnu')} "
                                f"du médicament "
                                f"« {product.name} » "
                                f"est expiré."
                            )
                        )

                    # ---------------------------------------------
                    # STOCK ACTUEL DU LOT
                    # ---------------------------------------------

                    current_batch_stock = int(
                        getattr(
                            batch,
                            "stock_units",
                            0,
                        )
                        or 0
                    )

                    if current_batch_stock < consumed_units:

                        raise ValueError(
                            (
                                f"Stock insuffisant dans "
                                f"le lot "
                                f"{getattr(batch, 'batch_number', 'inconnu')}."
                            )
                        )

                    # ---------------------------------------------
                    # DIMINUTION DU LOT
                    # ---------------------------------------------

                    batch.stock_units = (
                        current_batch_stock
                        - consumed_units
                    )

                    # ---------------------------------------------
                    # TOTAL CONSOMME
                    # ---------------------------------------------

                    total_consumed += consumed_units

                    # ---------------------------------------------
                    # CREATION SALE ITEM
                    # ---------------------------------------------

                    sale_item = self._create_sale_item(
                        session=session,
                        sale=sale,
                        product=product,
                        cart_item=cart_item,
                        allocation=allocation,
                    )

                    session.add(sale_item)

                # =================================================
                # VERIFICATION FINALE
                # =================================================

                if total_consumed != required_units:

                    raise ValueError(
                        (
                            f"Erreur de synchronisation "
                            f"du stock pour "
                            f"« {product.name} ».\n\n"
                            f"Demandé : {required_units}\n"
                            f"Consommé : {total_consumed}"
                        )
                    )

                # =================================================
                # MISE A JOUR STOCK GLOBAL
                # =================================================

                current_product_stock = int(
                    getattr(
                        product,
                        "stock_units",
                        0,
                    )
                    or 0
                )

                if current_product_stock < total_consumed:

                    raise ValueError(
                        (
                            f"Le stock global du produit "
                            f"« {product.name} » "
                            f"est inférieur à la quantité vendue."
                        )
                    )

                product.stock_units = (
                    current_product_stock
                    - total_consumed
                )

                # =================================================
                # MISE A JOUR AFFICHAGE
                # =================================================

                try:
                    update_display_quantity(product)
                except Exception:
                    pass

            # =================================================
            # COMMIT FINAL
            # =================================================

            session.commit()

            # =================================================
            # FACTURE
            # =================================================

            invoice_generated = self.generate_invoice(
                sale
            )

            if invoice_generated:

                QMessageBox.information(
                    self,
                    "Vente enregistrée",
                    (
                        "La vente a été enregistrée "
                        "avec succès.\n\n"
                        f"Facture : "
                        f"{invoice_number}\n"
                        f"Total : "
                        f"{self._format_money(total)}\n\n"
                        "Le stock a été automatiquement "
                        "diminué selon la méthode FEFO."
                    ),
                )

            else:

                QMessageBox.information(
                    self,
                    "Vente enregistrée",
                    (
                        "La vente a été enregistrée "
                        "avec succès.\n\n"
                        f"Facture : "
                        f"{invoice_number}\n"
                        f"Total : "
                        f"{self._format_money(total)}\n\n"
                        "Le stock a été automatiquement "
                        "diminué.\n\n"
                        "La facture PDF n'a pas pu "
                        "être générée."
                    ),
                )

            # =================================================
            # RESET
            # =================================================

            self.reset_sale()

        except Exception as error:

            # =================================================
            # ANNULATION COMPLETE
            # =================================================

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                (
                    "La vente n'a pas pu être enregistrée.\n\n"
                    f"{error}\n\n"
                    "Aucun stock n'a été définitivement "
                    "modifié."
                ),
            )

        finally:

            session.close()

    # =========================================================
    # FACTURE
    # =========================================================

    def generate_invoice(self, sale):

        try:

            from utils.pdf_generator import (
                generate_invoice_pdf,
            )

            generate_invoice_pdf(sale)

            return True

        except ImportError:
            return False

        except TypeError:
            return False

        except Exception:
            return False

    # =========================================================
    # RESET
    # =========================================================

    def reset_sale(self):

        self.cart.clear()

        self.discount_input.blockSignals(True)

        self.discount_input.setValue(0.0)

        self.discount_input.blockSignals(False)

        self.payment_combo.setCurrentIndex(0)
        self.packaging_combo.setCurrentIndex(0)

        self.cart_table.setRowCount(0)

        self.search_input.clear()

        self.update_cart_count()
        self.update_totals()

        self.search_products()
