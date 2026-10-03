from datetime import date, datetime

from sqlalchemy import (
    String,
    Integer,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.database import Base


# ============================================================
# PRODUCT
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Général"
    )

    # Unité de base
    #
    # Exemple :
    # Comprimé
    # Flacon
    # Ampoule
    # Pièce
    base_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Comprimé"
    )

    # Conditionnement principal
    #
    # Exemples :
    # Plaquette
    # Boîte
    # Carton
    packaging: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Boîte"
    )

    # Produit médicament ou non
    is_medicine: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # ========================================================
    # UNIT CONVERSION
    # ========================================================

    # 1 plaquette = X comprimés
    units_per_plaquette: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # 1 boîte = X plaquettes
    plaquettes_per_box: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # 1 carton = X boîtes
    boxes_per_carton: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # ========================================================
    # LEGACY QUANTITY
    # ========================================================

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # GLOBAL STOCK
    # ========================================================

    # Stock global dans l'unité de base.
    #
    # Exemple :
    #
    # 1 carton
    # = 10 boîtes
    # = 100 plaquettes
    # = 1000 comprimés
    #
    # stock_units = 1000
    stock_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # Seuil minimum en unité de base.
    min_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5
    )

    # ========================================================
    # SELLING PRICES
    # ========================================================

    # Prix principal historique.
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix d'un comprimé
    price_per_comprime: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix d'une plaquette
    price_per_plaquette: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix d'une boîte
    price_per_box: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix d'un carton
    price_per_carton: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # LEGACY PRODUCT INFORMATION
    # ========================================================

    batch_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=""
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    purchase_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    supplier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=""
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    batches = relationship(
        "ProductBatch",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductBatch.expiry_date"
    )

    sale_items = relationship(
        "SaleItem",
        back_populates="product"
    )


# ============================================================
# PRODUCT BATCH
# ============================================================

class ProductBatch(Base):
    __tablename__ = "product_batches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # ========================================================
    # PRODUCT RELATION
    # ========================================================

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    product = relationship(
        "Product",
        back_populates="batches"
    )

    # ========================================================
    # BATCH INFORMATION
    # ========================================================

    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # EXPIRATION
    # ========================================================

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True
    )

    # ========================================================
    # STOCK
    # ========================================================

    stock_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # PURCHASE INFORMATION
    # ========================================================

    purchase_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    purchase_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Boîte"
    )

    purchase_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    supplier: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default=""
    )

    # ========================================================
    # DATE OF RECEIPT
    # ========================================================

    received_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )

    # ========================================================
    # ACTIVE STATUS
    # ========================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    sale_items = relationship(
        "SaleItem",
        back_populates="batch"
    )


# ============================================================
# SALE
# ============================================================

class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # ========================================================
    # INVOICE
    # ========================================================

    invoice_number: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
        index=True
    )

    # ========================================================
    # CLIENT
    # ========================================================

    client_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Client comptant"
    )

    # ========================================================
    # TOTAL
    # ========================================================

    total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # PAYMENT
    # ========================================================

    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Espèces"
    )

    # ========================================================
    # DATE
    # ========================================================

    created_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today
    )

    # ========================================================
    # RELATION
    # ========================================================

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan"
    )


# ============================================================
# SALE ITEM
# ============================================================

class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # ========================================================
    # SALE
    # ========================================================

    sale_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sales.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    sale = relationship(
        "Sale",
        back_populates="items"
    )

    # ========================================================
    # PRODUCT
    # ========================================================

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id"
        ),
        nullable=False,
        index=True
    )

    product = relationship(
        "Product",
        back_populates="sale_items"
    )

    # ========================================================
    # BATCH
    # ========================================================

    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "product_batches.id"
        ),
        nullable=True,
        index=True
    )

    batch = relationship(
        "ProductBatch",
        back_populates="sale_items"
    )

    # ========================================================
    # QUANTITY
    # ========================================================

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # ========================================================
    # SALE UNIT
    # ========================================================

    sale_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Boîte"
    )

    # ========================================================
    # UNIT PRICE
    # ========================================================

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # TOTAL PRICE
    # ========================================================

    total_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # STOCK CONVERSION
    # ========================================================

    stock_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # EXPIRATION SNAPSHOT
    # ========================================================

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # ========================================================
    # BATCH NUMBER SNAPSHOT
    # ========================================================

    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=""
    )


# ============================================================
# EXPENSE
# ============================================================

class Expense(Base):
    """
    Dépense manuelle de la pharmacie.

    Exemples :
        - Nourriture
        - Transport
        - Électricité
        - Eau
        - Internet
        - Fournitures
        - Entretien
        - Salaire
        - Loyer
        - Autre
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # ========================================================
    # EXPENSE NAME
    # ========================================================

    # Exemple :
    # "Déjeuner du personnel"
    # "Transport fournisseur"
    # "Achat papier"
    description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )

    # ========================================================
    # CATEGORY
    # ========================================================

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Autre",
        index=True
    )

    # ========================================================
    # AMOUNT
    # ========================================================

    # Montant de la dépense en CDF.
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # EXPENSE DATE
    # ========================================================

    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        index=True
    )

    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Espèces"
    )

    # ========================================================
    # NOTE
    # ========================================================

    note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=""
    )

    # ========================================================
    # USER WHO CREATED THE EXPENSE
    # ========================================================

    # On conserve le nom de l'utilisateur
    # sans créer de dépendance avec la table User.
    #
    # Exemple :
    # Administrateur
    # Jean
    # Marie
    created_by: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default=""
    )

    # ========================================================
    # CREATED AT
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            f"<Expense("
            f"id={self.id}, "
            f"description='{self.description}', "
            f"category='{self.category}', "
            f"amount={self.amount}, "
            f"expense_date={self.expense_date}"
            f")>"
        )