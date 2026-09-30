from datetime import date

from sqlalchemy import (
    String,
    Integer,
    Float,
    Date,
    ForeignKey,
    Boolean,
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

    # Exemple :
    # Comprimé
    # Sirop
    # Injection
    # Matériel médical
    base_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Comprimé"
    )

    # Conditionnement principal affiché dans l'interface.
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

    # Indique si le produit est un médicament.
    #
    # Si True :
    # chaque lot doit obligatoirement avoir
    # une date d'expiration.
    is_medicine: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # ========================================================
    # UNIT CONVERSION
    # ========================================================

    # Nombre de comprimés dans une plaquette.
    #
    # Exemple :
    # 1 plaquette = 10 comprimés
    units_per_plaquette: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # Nombre de plaquettes dans une boîte.
    #
    # Exemple :
    # 1 boîte = 10 plaquettes
    plaquettes_per_box: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # Nombre de boîtes dans un carton.
    #
    # Exemple :
    # 1 carton = 10 boîtes
    boxes_per_carton: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    # ========================================================
    # LEGACY QUANTITY
    # ========================================================

    # Ancien système.
    # Conservé temporairement afin de ne pas casser
    # les anciennes pages pendant la migration.
    # Le nouveau système doit utiliser stock_units ou les ProductBatch.
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # GLOBAL STOCK
    # ========================================================

    # Stock total dans l'unité de base.
    #
    # Exemple :
    # 1 carton
    # = 10 boîtes
    # = 100 plaquettes
    # = 1000 comprimés
    #
    # stock_units = 1000
    #
    # IMPORTANT :
    # Ce champ représente le total de tous les lots.
    # Les stocks individuels sont dans ProductBatch.
    stock_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # Seuil minimum (exprimé dans l'unité de base).
    min_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5
    )

    # ========================================================
    # SELLING PRICES
    # ========================================================

    # Ancien prix principal (conservé pour compatibilité).
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix de vente d'un comprimé.
    price_per_comprime: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix de vente d'une plaquette.
    price_per_plaquette: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix de vente d'une boîte.
    price_per_box: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Prix de vente d'un carton.
    price_per_carton: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # ========================================================
    # LEGACY PRODUCT INFORMATION
    # ========================================================

    # Ces champs sont conservés pour faciliter la migration de l'ancien système.
    # Ils ne doivent plus être utilisés pour gérer les lots.

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

    # Un produit peut avoir plusieurs lots.
    batches = relationship(
        "ProductBatch",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductBatch.expiry_date"
    )

    # Un produit peut apparaître dans plusieurs lignes de vente.
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

    # Numéro du lot.
    # Exemple : PAR-2026-001
    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # EXPIRATION
    # ========================================================

    # Date d'expiration du lot.
    # Pour un médicament : cette valeur doit être renseignée.
    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True
    )

    # ========================================================
    # STOCK
    # ========================================================

    # Stock de CE LOT dans l'unité de base.
    # Exemple : Lot A : 5000 comprimés
    stock_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # ========================================================
    # PURCHASE INFORMATION
    # ========================================================

    # Quantité reçue lors de l'achat, dans l'unité d'achat.
    # Exemple : 5 cartons
    purchase_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # Unité utilisée lors de l'achat.
    # Exemples : Comprimé, Plaquette, Boîte, Carton
    purchase_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Boîte"
    )

    # Prix d'achat d'une unité d'achat.
    # Exemple : 1 carton = 25 000 FC
    purchase_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0
    )

    # Fournisseur ayant livré ce lot.
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

    # Permet de désactiver un lot sans le supprimer de l'historique.
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

    # Lot réellement utilisé pour cette vente.
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

    # Quantité vendue dans l'unité choisie.
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # ========================================================
    # SALE UNIT
    # ========================================================

    # Unité choisie par le vendeur (Comprimé, Plaquette, Boîte, Carton).
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

    # Quantité retirée du stock en unité de base.
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