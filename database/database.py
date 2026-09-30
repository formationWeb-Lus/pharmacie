# database/database.py

from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# 1. DATABASE LOCATION
# ============================================================

APP_DIR = (
    Path.home()
    / "AppData"
    / "Local"
    / "Pharmacie"
)

APP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_PATH = APP_DIR / "pharmacie.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ============================================================
# 2. SQLALCHEMY CONFIGURATION
# ============================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


# ============================================================
# 3. DATABASE SESSION
# ============================================================

def get_db():
    """
    Create and return a new database session.
    """
    return SessionLocal()


# ============================================================
# 4. SQLITE HELPERS
# ============================================================

def table_exists(table_name):
    """
    Check whether a table exists.
    """
    inspector = inspect(engine)

    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """
    Check whether a column exists in a SQLite table.
    """
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return False

    columns = inspector.get_columns(table_name)

    return any(
        column["name"] == column_name
        for column in columns
    )


def add_column_if_not_exists(
    table_name,
    column_name,
    column_definition,
):
    """
    Add a column to an existing SQLite table
    if the column does not already exist.
    """

    if not table_exists(table_name):
        return False

    if column_exists(
        table_name,
        column_name,
    ):
        return False

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                ALTER TABLE {table_name}
                ADD COLUMN {column_name}
                {column_definition}
                """
            )
        )

    print(
        f"✓ Colonne ajoutée : "
        f"{table_name}.{column_name}"
    )

    return True


# ============================================================
# 5. SAFE INTEGER
# ============================================================

def safe_int(value, default=0):
    """
    Safely convert a value to integer.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# 6. SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# 6B. SAFE DATE
# ============================================================

def parse_date_safe(value, default=None):
    """
    Convert legacy SQLite date/datetime values into a Python date.

    Accepts:
        2026-09-29
        2026-09-29 17:35:00.386496
        2026-09-29T17:35:00.386496
        datetime/date objects

    This is important because old SQLite databases may contain
    a DATETIME string inside a column now declared as DATE.
    """
    if value is None:
        return default

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    raw = str(value).strip()

    if not raw:
        return default

    # The first 10 characters are the ISO date part for both:
    # YYYY-MM-DD
    # YYYY-MM-DD HH:MM:SS
    # YYYY-MM-DDTHH:MM:SS
    if len(raw) >= 10:
        candidate = raw[:10]
        try:
            return date.fromisoformat(candidate)
        except ValueError:
            pass

    # Last attempt for less common ISO representations.
    try:
        from datetime import datetime
        return datetime.fromisoformat(
            raw.replace("Z", "+00:00")
        ).date()
    except (TypeError, ValueError):
        return default


def normalize_legacy_date_columns():
    """
    Normalize old SQLite date columns before SQLAlchemy ORM reads them.

    Older versions of the application could save values such as:
        2026-09-29 17:35:00.386496

    into a column declared as DATE.

    SQLAlchemy's SQLite DATE processor expects:
        YYYY-MM-DD

    so ORM queries can fail before our Python migration code even runs.

    This function changes only the textual representation of the date;
    it does NOT delete, replace, or otherwise alter the actual date.
    """
    tables_and_columns = {
        "products": ["expiry_date"],
        "sale_items": ["expiry_date"],
        "product_batches": ["expiry_date"],
    }

    with engine.begin() as connection:
        for table_name, columns in tables_and_columns.items():
            if not table_exists(table_name):
                continue

            for column_name in columns:
                if not column_exists(table_name, column_name):
                    continue

                connection.execute(
                    text(
                        f"""
                        UPDATE {table_name}
                        SET {column_name} = substr({column_name}, 1, 10)
                        WHERE {column_name} IS NOT NULL
                          AND length(CAST({column_name} AS TEXT)) > 10
                        """
                    )
                )


# ============================================================
# 7. NORMALIZE UNIT NAME
# ============================================================

def normalize_unit(unit):
    """
    Normalize packaging/unit names.

    Supported units:
        Comprimé
        Plaquette
        Boîte
        Carton
        Flacon
        Ampoule
        Pièce
    """

    if not unit:
        return "Boîte"

    unit = str(unit).strip()

    aliases = {
        "comprime": "Comprimé",
        "comprimé": "Comprimé",
        "comprimés": "Comprimé",

        "plaquette": "Plaquette",
        "plaquettes": "Plaquette",

        "boite": "Boîte",
        "boîte": "Boîte",
        "boites": "Boîte",
        "boîtes": "Boîte",

        "carton": "Carton",
        "cartons": "Carton",

        "flacon": "Flacon",
        "flacons": "Flacon",

        "ampoule": "Ampoule",
        "ampoules": "Ampoule",

        "piece": "Pièce",
        "pièce": "Pièce",
        "pieces": "Pièce",
        "pièces": "Pièce",
    }

    return aliases.get(
        unit.lower(),
        unit,
    )


# ============================================================
# 8. PRODUCT CONVERSION VALUES
# ============================================================

def get_units_per_plaquette(product):
    """
    Return number of base units in one plaquette.

    Example:
        1 plaquette = 10 comprimés
    """

    value = safe_int(
        getattr(
            product,
            "units_per_plaquette",
            10,
        ),
        10,
    )

    return max(1, value)


def get_plaquettes_per_box(product):
    """
    Return number of plaquettes in one box.

    Example:
        1 boîte = 10 plaquettes
    """

    value = safe_int(
        getattr(
            product,
            "plaquettes_per_box",
            10,
        ),
        10,
    )

    return max(1, value)


def get_boxes_per_carton(product):
    """
    Return number of boxes in one carton.

    Example:
        1 carton = 10 boîtes
    """

    value = safe_int(
        getattr(
            product,
            "boxes_per_carton",
            10,
        ),
        10,
    )

    return max(1, value)


def get_units_per_box(product):
    """
    Return number of base units in one box.

    Example:
        1 boîte
        = 10 plaquettes
        × 10 comprimés
        = 100 comprimés
    """

    return (
        get_units_per_plaquette(product)
        * get_plaquettes_per_box(product)
    )


def get_units_per_carton(product):
    """
    Return number of base units in one carton.

    Example:
        1 carton
        = 10 boîtes
        × 10 plaquettes
        × 10 comprimés
        = 1000 comprimés
    """

    return (
        get_units_per_box(product)
        * get_boxes_per_carton(product)
    )


# ============================================================
# 9. CONVERT PACKAGING TO BASE UNITS
# ============================================================

def get_units_for_packaging(
    product,
    packaging,
):
    """
    Convert one packaging unit into base units.

    Example:
        Comprimé  = 1
        Plaquette = 10
        Boîte     = 100
        Carton    = 1000
    """

    packaging = normalize_unit(packaging)

    if packaging == "Comprimé":
        return 1

    if packaging == "Plaquette":
        return get_units_per_plaquette(product)

    if packaging == "Boîte":
        return get_units_per_box(product)

    if packaging == "Carton":
        return get_units_per_carton(product)

    # For products without hierarchical packaging,
    # one unit equals one base unit.
    return 1


# ============================================================
# 10. CONVERT QUANTITY TO BASE UNITS
# ============================================================

def convert_to_base_units(
    product,
    quantity,
    unit,
):
    """
    Convert a quantity into base units.

    Example:
        3 boîtes
        = 3 × 100
        = 300 comprimés
    """

    quantity = safe_int(
        quantity,
        0,
    )

    if quantity <= 0:
        return 0

    units = get_units_for_packaging(
        product,
        unit,
    )

    return quantity * units


# ============================================================
# 11. STOCK DISPLAY
# ============================================================

def get_stock_display(product):
    """
    Convert global stock into a readable format.

    Example:
        1257 comprimés

    becomes:
        1 carton(s) + 2 boîte(s)
        + 5 plaquette(s) + 7 comprimé(s)
    """

    stock_units = max(
        0,
        safe_int(
            getattr(
                product,
                "stock_units",
                0,
            )
        ),
    )

    units_per_plaquette = (
        get_units_per_plaquette(product)
    )

    units_per_box = (
        get_units_per_box(product)
    )

    units_per_carton = (
        get_units_per_carton(product)
    )

    cartons = (
        stock_units
        // units_per_carton
    )

    remaining = (
        stock_units
        % units_per_carton
    )

    boxes = (
        remaining
        // units_per_box
    )

    remaining = (
        remaining
        % units_per_box
    )

    plaquettes = (
        remaining
        // units_per_plaquette
    )

    comprimes = (
        remaining
        % units_per_plaquette
    )

    parts = []

    if cartons > 0:
        parts.append(
            f"{cartons} carton(s)"
        )

    if boxes > 0:
        parts.append(
            f"{boxes} boîte(s)"
        )

    if plaquettes > 0:
        parts.append(
            f"{plaquettes} plaquette(s)"
        )

    if comprimes > 0:
        parts.append(
            f"{comprimes} comprimé(s)"
        )

    if not parts:
        return "0"

    return " + ".join(parts)


# ============================================================
# 12. UPDATE LEGACY QUANTITY
# ============================================================

def get_main_packaging_quantity(product):
    """
    Calculate the number of complete
    main packaging units.

    This is maintained for compatibility
    with the old application.
    """

    stock_units = max(
        0,
        safe_int(
            getattr(
                product,
                "stock_units",
                0,
            )
        ),
    )

    packaging = normalize_unit(
        getattr(
            product,
            "packaging",
            "Boîte",
        )
    )

    units = get_units_for_packaging(
        product,
        packaging,
    )

    if units <= 0:
        return stock_units

    return stock_units // units


def update_display_quantity(product):
    """
    Synchronize the old quantity field
    with stock_units.
    """

    quantity = get_main_packaging_quantity(
        product
    )

    product.quantity = quantity

    return quantity


# ============================================================
# 13. PRICE MANAGEMENT
# ============================================================

def get_price_for_packaging(
    product,
    packaging,
):
    """
    Return the selling price for a unit.

    Prices are explicitly stored for:
        Comprimé
        Plaquette
        Boîte
        Carton
    """

    packaging = normalize_unit(packaging)

    if packaging == "Comprimé":
        return safe_float(
            getattr(
                product,
                "price_per_comprime",
                0,
            )
        )

    if packaging == "Plaquette":
        return safe_float(
            getattr(
                product,
                "price_per_plaquette",
                0,
            )
        )

    if packaging == "Boîte":
        return safe_float(
            getattr(
                product,
                "price_per_box",
                0,
            )
        )

    if packaging == "Carton":
        return safe_float(
            getattr(
                product,
                "price_per_carton",
                0,
            )
        )

    return safe_float(
        getattr(
            product,
            "price",
            0,
        )
    )


def calculate_product_prices(product):
    """
    Calculate packaging prices from
    the product's main price.

    Example:
        Box price = 3000 FC
        1 box = 10 plaquettes
        1 plaquette = 10 comprimés

        Plaquette = 300 FC
        Comprimé = 30 FC
        Carton = 30000 FC
    """

    base_price = max(
        0.0,
        safe_float(
            getattr(
                product,
                "price",
                0,
            )
        ),
    )

    units_per_plaquette = (
        get_units_per_plaquette(product)
    )

    plaquettes_per_box = (
        get_plaquettes_per_box(product)
    )

    boxes_per_carton = (
        get_boxes_per_carton(product)
    )

    packaging = normalize_unit(
        getattr(
            product,
            "packaging",
            "Boîte",
        )
    )

    if packaging == "Comprimé":

        price_per_comprime = base_price

        price_per_plaquette = (
            base_price
            * units_per_plaquette
        )

        price_per_box = (
            price_per_plaquette
            * plaquettes_per_box
        )

        price_per_carton = (
            price_per_box
            * boxes_per_carton
        )

    elif packaging == "Plaquette":

        price_per_comprime = (
            base_price
            / units_per_plaquette
        )

        price_per_plaquette = base_price

        price_per_box = (
            base_price
            * plaquettes_per_box
        )

        price_per_carton = (
            price_per_box
            * boxes_per_carton
        )

    elif packaging == "Carton":

        price_per_carton = base_price

        price_per_box = (
            base_price
            / boxes_per_carton
        )

        price_per_plaquette = (
            price_per_box
            / plaquettes_per_box
        )

        price_per_comprime = (
            price_per_plaquette
            / units_per_plaquette
        )

    else:

        price_per_box = base_price

        price_per_plaquette = (
            base_price
            / plaquettes_per_box
        )

        price_per_comprime = (
            price_per_plaquette
            / units_per_plaquette
        )

        price_per_carton = (
            base_price
            * boxes_per_carton
        )

    product.price_per_comprime = round(
        price_per_comprime,
        2,
    )

    product.price_per_plaquette = round(
        price_per_plaquette,
        2,
    )

    product.price_per_box = round(
        price_per_box,
        2,
    )

    product.price_per_carton = round(
        price_per_carton,
        2,
    )


# ============================================================
# 14. EXPIRATION
# ============================================================

def is_product_expired(product):
    """
    Legacy product expiration check.

    New system:
        expiration belongs to ProductBatch.
    """

    expiry_date = getattr(
        product,
        "expiry_date",
        None,
    )

    if not expiry_date:
        return False

    return expiry_date < date.today()


def is_batch_expired(batch):
    """
    Check whether a batch is expired.
    """

    if not batch.expiry_date:
        return False

    return batch.expiry_date < date.today()


def days_until_expiration(batch):
    """
    Return the number of days remaining
    before expiration.

    Negative value means already expired.
    """

    if not batch.expiry_date:
        return None

    return (
        batch.expiry_date
        - date.today()
    ).days


def is_batch_expiring_soon(
    batch,
    days=90,
):
    """
    Return True if the batch expires
    within the specified number of days.
    """

    if not batch.expiry_date:
        return False

    today = date.today()

    limit = (
        today
        + timedelta(days=days)
    )

    return (
        today
        <= batch.expiry_date
        <= limit
    )


# ============================================================
# 15. BATCH VALIDATION
# ============================================================

def validate_batch_expiry(
    product,
    expiry_date,
):
    """
    Validate a batch expiration date.

    For medicines:
        expiry date is mandatory.

    For non-medicines:
        expiry date may be empty.
    """

    is_medicine = bool(
        getattr(
            product,
            "is_medicine",
            True,
        )
    )

    if is_medicine and not expiry_date:
        raise ValueError(
            "La date d'expiration est "
            "obligatoire pour tout médicament."
        )

    if expiry_date:
        if expiry_date < date.today():
            raise ValueError(
                "La date d'expiration ne "
                "peut pas être dans le passé."
            )

    return True


# ============================================================
# 16. GET ACTIVE BATCHES
# ============================================================

def get_available_batches(
    product,
    db=None,
):
    """
    Return active batches with stock > 0,
    ordered using FEFO.

    FEFO =
        First Expired, First Out

    The batch expiring first is returned first.
    """

    from database.models import ProductBatch

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        batches = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.product_id
                == product.id
            )
            .filter(
                ProductBatch.is_active
                == True
            )
            .filter(
                ProductBatch.stock_units
                > 0
            )
            .order_by(
                ProductBatch.expiry_date.asc(),
                ProductBatch.received_at.asc(),
                ProductBatch.id.asc(),
            )
            .all()
        )

        return batches

    finally:
        if close_session:
            db.close()


# ============================================================
# 17. GET FIRST EXPIRING BATCH
# ============================================================

def get_first_expiring_batch(
    product,
    db=None,
):
    """
    Return the batch that should be consumed first.
    """

    batches = get_available_batches(
        product,
        db,
    )

    if not batches:
        return None

    return batches[0]


# ============================================================
# 18. CALCULATE GLOBAL STOCK
# ============================================================

def calculate_product_global_stock(
    product,
    db=None,
):
    """
    Calculate global product stock
    from all active batches.
    """

    from database.models import ProductBatch

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        total = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.product_id
                == product.id
            )
            .filter(
                ProductBatch.is_active
                == True
            )
            .with_entities(
                ProductBatch.stock_units
            )
            .all()
        )

        stock = sum(
            safe_int(
                row[0],
                0,
            )
            for row in total
        )

        product.stock_units = max(
            0,
            stock,
        )

        update_display_quantity(
            product
        )

        return product.stock_units

    finally:
        if close_session:
            db.close()


# ============================================================
# 19. SYNCHRONIZE PRODUCT STOCK
# ============================================================

def synchronize_product_stock(
    product,
    db=None,
):
    """
    Synchronize Product.stock_units with
    all active ProductBatch stocks.
    """

    return calculate_product_global_stock(
        product,
        db,
    )


# ============================================================
# 20. ADD STOCK TO A BATCH
# ============================================================

def add_batch_stock(
    product,
    quantity,
    purchase_unit,
    batch_number,
    expiry_date,
    purchase_price=0.0,
    supplier="",
    db=None,
):
    """
    Add stock to a batch.

    Example:
        5 cartons
        1 carton = 1000 comprimés

        Added:
            5000 comprimés

    If the same product + batch number exists,
    the existing batch is updated.
    """

    from database.models import ProductBatch

    quantity = safe_int(
        quantity,
        0,
    )

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à zéro."
        )

    purchase_unit = normalize_unit(
        purchase_unit
    )

    validate_batch_expiry(
        product,
        expiry_date,
    )

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        existing_batch = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.product_id
                == product.id
            )
            .filter(
                ProductBatch.batch_number
                == batch_number
            )
            .first()
        )

        added_units = convert_to_base_units(
            product,
            quantity,
            purchase_unit,
        )

        if existing_batch:

            existing_batch.stock_units += (
                added_units
            )

            existing_batch.purchase_quantity += (
                quantity
            )

            existing_batch.purchase_unit = (
                purchase_unit
            )

            existing_batch.purchase_price = (
                purchase_price
            )

            existing_batch.supplier = (
                supplier or ""
            )

            existing_batch.expiry_date = (
                expiry_date
            )

            existing_batch.is_active = True

            batch = existing_batch

        else:

            batch = ProductBatch(
                product_id=product.id,
                batch_number=batch_number,
                expiry_date=expiry_date,
                stock_units=added_units,
                purchase_quantity=quantity,
                purchase_unit=purchase_unit,
                purchase_price=purchase_price,
                supplier=supplier or "",
                is_active=True,
            )

            db.add(batch)

        db.flush()

        synchronize_product_stock(
            product,
            db,
        )

        if close_session:
            db.commit()

        return batch

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 21. ADD PRODUCT STOCK
# ============================================================

def add_product_stock(
    product,
    quantity,
    packaging,
    batch_number=None,
    expiry_date=None,
    purchase_price=0.0,
    supplier="",
    db=None,
):
    """
    Add stock to a product.

    New system:
        stock belongs to a batch.

    A medicine should normally provide:
        batch_number
        expiry_date
    """

    if not batch_number:
        raise ValueError(
            "Le numéro de lot est obligatoire."
        )

    return add_batch_stock(
        product=product,
        quantity=quantity,
        purchase_unit=packaging,
        batch_number=batch_number,
        expiry_date=expiry_date,
        purchase_price=purchase_price,
        supplier=supplier,
        db=db,
    )


# ============================================================
# 22. CHECK PRODUCT STOCK
# ============================================================

def can_sell_product(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Check whether enough non-expired stock
    exists for a sale.
    """

    quantity = safe_int(
        quantity,
        0,
    )

    if quantity <= 0:
        return False

    required_units = convert_to_base_units(
        product,
        quantity,
        packaging,
    )

    batches = get_available_batches(
        product,
        db,
    )

    available_units = 0

    for batch in batches:

        # Never sell expired stock.
        if is_batch_expired(batch):
            continue

        available_units += safe_int(
            batch.stock_units,
            0,
        )

        if available_units >= required_units:
            return True

    return False


# ============================================================
# 23. CALCULATE STOCK AFTER SALE
# ============================================================

def calculate_stock_after_sale(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Calculate global stock after sale
    without modifying the database.
    """

    required_units = convert_to_base_units(
        product,
        quantity,
        packaging,
    )

    current_stock = safe_int(
        getattr(
            product,
            "stock_units",
            0,
        ),
        0,
    )

    return max(
        0,
        current_stock - required_units,
    )


# ============================================================
# 24. REDUCE STOCK FROM BATCHES
# ============================================================

def reduce_stock_from_batches(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Remove stock using FEFO.

    FEFO:
        First Expired, First Out

    More precisely:
        the batch with the earliest
        valid expiration is consumed first.

    Expired batches are NEVER sold.

    Returns:
        {
            "total_units": ...,
            "batches": [...]
        }
    """

    quantity = safe_int(
        quantity,
        0,
    )

    if quantity <= 0:
        raise ValueError(
            "La quantité doit être supérieure à zéro."
        )

    required_units = convert_to_base_units(
        product,
        quantity,
        packaging,
    )

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        batches = get_available_batches(
            product,
            db,
        )

        remaining = required_units

        consumed_batches = []

        for batch in batches:

            if remaining <= 0:
                break

            # Never sell expired medication.
            if is_batch_expired(batch):
                continue

            batch_stock = safe_int(
                batch.stock_units,
                0,
            )

            if batch_stock <= 0:
                continue

            units_to_remove = min(
                batch_stock,
                remaining,
            )

            batch.stock_units -= (
                units_to_remove
            )

            remaining -= (
                units_to_remove
            )

            consumed_batches.append(
                {
                    "batch": batch,
                    "batch_id": batch.id,
                    "batch_number": batch.batch_number,
                    "expiry_date": batch.expiry_date,
                    "stock_units": units_to_remove,
                }
            )

            if batch.stock_units <= 0:

                batch.stock_units = 0

                # Keep the batch for history,
                # but deactivate it.
                batch.is_active = False

        if remaining > 0:
            raise ValueError(
                "Stock insuffisant pour "
                "effectuer cette vente."
            )

        synchronize_product_stock(
            product,
            db,
        )

        if close_session:
            db.commit()

        return {
            "total_units": required_units,
            "batches": consumed_batches,
        }

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 25. LEGACY REDUCE STOCK
# ============================================================

def reduce_product_stock(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Compatibility wrapper.

    New code should preferably use:
        reduce_stock_from_batches()
    """

    result = reduce_stock_from_batches(
        product=product,
        quantity=quantity,
        packaging=packaging,
        db=db,
    )

    return result["total_units"]


# ============================================================
# 26. LOW STOCK
# ============================================================

def is_low_stock(product):
    """
    Determine whether global stock
    is below the configured minimum.
    """

    stock_units = safe_int(
        getattr(
            product,
            "stock_units",
            0,
        )
    )

    minimum = safe_int(
        getattr(
            product,
            "min_quantity",
            0,
        )
    )

    return stock_units <= minimum


# ============================================================
# 27. GET EXPIRING BATCHES
# ============================================================

def get_expiring_batches(
    days=90,
    db=None,
):
    """
    Return batches expiring within the next
    specified number of days.

    Expired batches are not included here.
    """

    from database.models import ProductBatch

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        today = date.today()

        limit = (
            today
            + timedelta(days=days)
        )

        batches = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.is_active
                == True
            )
            .filter(
                ProductBatch.stock_units
                > 0
            )
            .filter(
                ProductBatch.expiry_date
                != None
            )
            .filter(
                ProductBatch.expiry_date
                >= today
            )
            .filter(
                ProductBatch.expiry_date
                <= limit
            )
            .order_by(
                ProductBatch.expiry_date.asc()
            )
            .all()
        )

        return batches

    finally:

        if close_session:
            db.close()


# ============================================================
# 28. GET EXPIRED BATCHES
# ============================================================

def get_expired_batches(db=None):
    """
    Return all active batches whose
    expiration date has passed.
    """

    from database.models import ProductBatch

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        today = date.today()

        batches = (
            db.query(ProductBatch)
            .filter(
                ProductBatch.is_active
                == True
            )
            .filter(
                ProductBatch.stock_units
                > 0
            )
            .filter(
                ProductBatch.expiry_date
                != None
            )
            .filter(
                ProductBatch.expiry_date
                < today
            )
            .order_by(
                ProductBatch.expiry_date.asc()
            )
            .all()
        )

        return batches

    finally:

        if close_session:
            db.close()


# ============================================================
# 29. DEACTIVATE EXPIRED BATCHES
# ============================================================

def deactivate_expired_batches(db=None):
    """
    Mark expired batches as inactive.

    Their stock is NOT deleted.

    This is important because expired stock
    should remain traceable in the database.
    """

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        batches = get_expired_batches(db)

        for batch in batches:
            batch.is_active = False

        if close_session:
            db.commit()

        return len(batches)

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 30. UPDATE OLD DATABASE SCHEMA
# ============================================================

def update_database_schema():
    """
    Update an existing pharmacy database.

    This function adds missing columns
    without deleting existing data.
    """

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    # ========================================================
    # PRODUCTS
    # ========================================================

    if "products" in tables:

        add_column_if_not_exists(
            "products",
            "packaging",
            "VARCHAR(50) DEFAULT 'Boîte'",
        )

        add_column_if_not_exists(
            "products",
            "category",
            "VARCHAR(100) DEFAULT 'Général'",
        )

        add_column_if_not_exists(
            "products",
            "base_unit",
            "VARCHAR(50) DEFAULT 'Comprimé'",
        )

        add_column_if_not_exists(
            "products",
            "is_medicine",
            "BOOLEAN DEFAULT 1",
        )

        add_column_if_not_exists(
            "products",
            "units_per_plaquette",
            "INTEGER DEFAULT 10",
        )

        add_column_if_not_exists(
            "products",
            "plaquettes_per_box",
            "INTEGER DEFAULT 10",
        )

        add_column_if_not_exists(
            "products",
            "boxes_per_carton",
            "INTEGER DEFAULT 10",
        )

        # Legacy columns

        add_column_if_not_exists(
            "products",
            "quantity",
            "INTEGER DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "min_quantity",
            "INTEGER DEFAULT 5",
        )

        add_column_if_not_exists(
            "products",
            "stock_units",
            "INTEGER DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "purchase_price",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "price",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "price_per_comprime",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "price_per_plaquette",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "price_per_box",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "price_per_carton",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "products",
            "batch_number",
            "VARCHAR(100) DEFAULT ''",
        )

        add_column_if_not_exists(
            "products",
            "expiry_date",
            "DATE",
        )

        add_column_if_not_exists(
            "products",
            "supplier",
            "VARCHAR(150) DEFAULT ''",
        )

        add_column_if_not_exists(
            "products",
            "created_at",
            "DATETIME",
        )

    # ========================================================
    # SALES ITEMS
    # ========================================================

    if "sale_items" in tables:

        add_column_if_not_exists(
            "sale_items",
            "sale_unit",
            "VARCHAR(50) DEFAULT 'Boîte'",
        )

        add_column_if_not_exists(
            "sale_items",
            "stock_units",
            "INTEGER DEFAULT 0",
        )

        add_column_if_not_exists(
            "sale_items",
            "total_price",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "sale_items",
            "batch_id",
            "INTEGER",
        )

        add_column_if_not_exists(
            "sale_items",
            "expiry_date",
            "DATE",
        )

        add_column_if_not_exists(
            "sale_items",
            "batch_number",
            "VARCHAR(100) DEFAULT ''",
        )

    # ProductBatch is created through SQLAlchemy
    # in init_db().
    #
    # We intentionally do not manually create it here.


# ============================================================
# 31. MIGRATE OLD STOCK
# ============================================================

def migrate_old_stock_to_batches():
    """
    Migrate old Product stock into ProductBatch without loading
    legacy DATE values through SQLAlchemy before they are normalized.

    This is deliberately implemented with raw SQL for the migration
    because old databases may contain DATETIME strings in expiry_date.
    """
    from database.models import ProductBatch

    # IMPORTANT:
    # Normalize legacy DATE columns before any ORM query on Product.
    normalize_legacy_date_columns()

    db = SessionLocal()

    try:
        # Read the legacy products using raw SQL. This prevents
        # SQLAlchemy's DATE processor from crashing on old values.
        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    packaging,
                    quantity,
                    stock_units,
                    batch_number,
                    expiry_date,
                    purchase_price,
                    supplier
                FROM products
                """
            )
        ).mappings().all()

        for row in rows:
            product_id = row["id"]

            existing_batch = (
                db.query(ProductBatch)
                .filter(
                    ProductBatch.product_id == product_id
                )
                .first()
            )

            # Already migrated.
            if existing_batch:
                continue

            packaging = normalize_unit(
                row["packaging"] or "Boîte"
            )

            stock_units = safe_int(
                row["stock_units"],
                0,
            )

            quantity = safe_int(
                row["quantity"],
                0,
            )

            # If old stock_units is empty, reconstruct it from
            # the old quantity and packaging.
            if stock_units <= 0 and quantity > 0:
                # We need a lightweight product object containing
                # the conversion configuration. Read it directly
                # from the database rather than ORM-loading Product.
                product_data = db.execute(
                    text(
                        """
                        SELECT
                            units_per_plaquette,
                            plaquettes_per_box,
                            boxes_per_carton,
                            packaging
                        FROM products
                        WHERE id = :product_id
                        """
                    ),
                    {"product_id": product_id},
                ).mappings().first()

                class LegacyProduct:
                    pass

                legacy_product = LegacyProduct()
                legacy_product.units_per_plaquette = (
                    product_data["units_per_plaquette"]
                    if product_data
                    else 10
                )
                legacy_product.plaquettes_per_box = (
                    product_data["plaquettes_per_box"]
                    if product_data
                    else 10
                )
                legacy_product.boxes_per_carton = (
                    product_data["boxes_per_carton"]
                    if product_data
                    else 10
                )

                stock_units = convert_to_base_units(
                    legacy_product,
                    quantity,
                    packaging,
                )

            # Nothing to migrate.
            if stock_units <= 0:
                continue

            batch_number = (
                row["batch_number"]
                or f"LEGACY-{product_id}"
            )

            expiry_date = parse_date_safe(
                row["expiry_date"]
            )

            # A legacy medicine may have no expiry date because
            # the old system did not require it. Keep the stock
            # traceable instead of losing it during migration.
            batch = ProductBatch(
                product_id=product_id,
                batch_number=batch_number,
                expiry_date=expiry_date,
                stock_units=stock_units,
                purchase_quantity=quantity,
                purchase_unit=packaging,
                purchase_price=safe_float(
                    row["purchase_price"],
                    0,
                ),
                supplier=row["supplier"] or "",
                is_active=True,
            )

            db.add(batch)

        db.commit()

        print(
            "✓ Migration des anciens stocks terminée."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# 32. INITIALIZE STOCK
# ============================================================

def initialize_stock_units():
    """
    Initialize and synchronize product stock.

    This function is maintained for compatibility
    with the previous version.
    """

    from database.models import Product

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .all()
        )

        for product in products:

            stock_units = safe_int(
                getattr(
                    product,
                    "stock_units",
                    0,
                ),
                0,
            )

            quantity = safe_int(
                getattr(
                    product,
                    "quantity",
                    0,
                ),
                0,
            )

            if (
                stock_units <= 0
                and quantity > 0
            ):
                product.stock_units = (
                    convert_to_base_units(
                        product,
                        quantity,
                        getattr(
                            product,
                            "packaging",
                            "Boîte",
                        ),
                    )
                )

            update_display_quantity(
                product
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# 33. UPDATE ALL PRODUCT PRICES
# ============================================================

def update_product_prices():
    """
    Recalculate packaging prices
    for all existing products.
    """

    from database.models import Product

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .all()
        )

        for product in products:
            calculate_product_prices(
                product
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# 34. DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Initialize the pharmacy database.

    Steps:
        1. Import models
        2. Create tables
        3. Update old schema
        4. Migrate old stock
        5. Initialize stock
        6. Update prices
        7. Create demo products if necessary
    """

    from database.models import (
        Product,
        ProductBatch,
        Sale,
        SaleItem,
    )

    print("")
    print("=" * 70)
    print("INITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 70)

    print(
        f"Database : {DATABASE_PATH}"
    )

    print("")

    try:

        # ----------------------------------------------------
        # CREATE TABLES
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        print(
            "✓ Tables vérifiées/créées."
        )

        # ----------------------------------------------------
        # UPDATE OLD DATABASE
        # ----------------------------------------------------

        update_database_schema()

        # ----------------------------------------------------
        # NORMALIZE LEGACY DATE VALUES
        # ----------------------------------------------------
        # Must happen before any ORM query on Product.
        # Old databases may contain:
        #   2026-09-29 17:35:00.386496
        # while the model expects:
        #   2026-09-29
        normalize_legacy_date_columns()

        # ----------------------------------------------------
        # CREATE NEW BATCH TABLE
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        print(
            "✓ Table ProductBatch vérifiée/créée."
        )

        # ----------------------------------------------------
        # MIGRATE OLD STOCK
        # ----------------------------------------------------

        migrate_old_stock_to_batches()

        # ----------------------------------------------------
        # INITIALIZE STOCK
        # ----------------------------------------------------

        initialize_stock_units()

        # ----------------------------------------------------
        # UPDATE PRICES
        # ----------------------------------------------------

        update_product_prices()

        # ----------------------------------------------------
        # DEACTIVATE EXPIRED BATCHES
        # ----------------------------------------------------

        deactivate_expired_batches()

        # ----------------------------------------------------
        # SEED DEMO DATA
        # ----------------------------------------------------

        seed_products()

        print("")

        print(
            "✓ Base de données prête."
        )

        print("=" * 70)
        print("")

    except Exception as error:

        print("")

        print(
            "❌ ERREUR DATABASE :"
        )

        print(error)

        print("")

        raise


# ============================================================
# 35. DEMO PRODUCTS
# ============================================================

def seed_products():
    """
    Create demo products only if the database
    contains no products.

    Demo medicines include an expiration date
    because expiration is mandatory for medicines.
    """

    from database.models import (
        Product,
        ProductBatch,
    )

    db = SessionLocal()

    try:

        existing_product = (
            db.query(Product)
            .first()
        )

        if existing_product:
            return

        # ====================================================
        # PARACETAMOL
        # ====================================================

        paracetamol = Product(
            name="Paracétamol 500 mg",
            category="Antalgique",
            base_unit="Comprimé",
            packaging="Boîte",
            is_medicine=True,
            units_per_plaquette=10,
            plaquettes_per_box=10,
            boxes_per_carton=10,
            quantity=0,
            min_quantity=100,
            stock_units=0,
            price=3000.0,
            price_per_comprime=30.0,
            price_per_plaquette=300.0,
            price_per_box=3000.0,
            price_per_carton=30000.0,
            supplier="Pharma Supplier",
        )

        db.add(paracetamol)
        db.flush()

        batch_paracetamol = ProductBatch(
            product_id=paracetamol.id,
            batch_number="PAR-2026-001",
            expiry_date=date(
                2027,
                12,
                31,
            ),
            stock_units=5000,
            purchase_quantity=5,
            purchase_unit="Carton",
            purchase_price=25000.0,
            supplier="Pharma Supplier",
            is_active=True,
        )

        db.add(batch_paracetamol)

        # ====================================================
        # AMOXICILLIN
        # ====================================================

        amoxicilline = Product(
            name="Amoxicilline 500 mg",
            category="Antibiotique",
            base_unit="Comprimé",
            packaging="Boîte",
            is_medicine=True,
            units_per_plaquette=10,
            plaquettes_per_box=10,
            boxes_per_carton=10,
            quantity=0,
            min_quantity=100,
            stock_units=0,
            price=5000.0,
            price_per_comprime=50.0,
            price_per_plaquette=500.0,
            price_per_box=5000.0,
            price_per_carton=50000.0,
            supplier="Pharma Supplier",
        )

        db.add(amoxicilline)
        db.flush()

        batch_amoxicilline = ProductBatch(
            product_id=amoxicilline.id,
            batch_number="AMO-2026-001",
            expiry_date=date(
                2028,
                6,
                30,
            ),
            stock_units=3000,
            purchase_quantity=3,
            purchase_unit="Carton",
            purchase_price=42000.0,
            supplier="Pharma Supplier",
            is_active=True,
        )

        db.add(batch_amoxicilline)

        # ====================================================
        # VITAMIN C
        # ====================================================

        vitamine_c = Product(
            name="Vitamine C",
            category="Vitamines",
            base_unit="Comprimé",
            packaging="Boîte",
            is_medicine=True,
            units_per_plaquette=10,
            plaquettes_per_box=10,
            boxes_per_carton=10,
            quantity=0,
            min_quantity=100,
            stock_units=0,
            price=2000.0,
            price_per_comprime=20.0,
            price_per_plaquette=200.0,
            price_per_box=2000.0,
            price_per_carton=20000.0,
            supplier="Pharma Supplier",
        )

        db.add(vitamine_c)
        db.flush()

        batch_vitamine = ProductBatch(
            product_id=vitamine_c.id,
            batch_number="VIT-2026-001",
            expiry_date=date(
                2028,
                12,
                31,
            ),
            stock_units=4000,
            purchase_quantity=4,
            purchase_unit="Carton",
            purchase_price=16000.0,
            supplier="Pharma Supplier",
            is_active=True,
        )

        db.add(batch_vitamine)

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        print(
            "✓ Produits et lots de démonstration ajoutés."
        )

    except Exception as error:

        db.rollback()

        print(
            "⚠ Erreur lors de l'ajout "
            f"des produits de démonstration : {error}"
        )

    finally:

        db.close()


# ============================================================
# 36. DATABASE INFORMATION
# ============================================================

def get_database_path():
    """
    Return database path.
    """

    return str(DATABASE_PATH)


def database_exists():
    """
    Check whether database exists.
    """

    return DATABASE_PATH.exists()


# ============================================================
# 37. DATABASE CONNECTION TEST
# ============================================================

def test_database_connection():
    """
    Test SQLite connection.
    """

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception as error:

        print(
            "❌ Erreur SQLite :",
            error,
        )

        return False


# ============================================================
# 38. GET DATABASE STATISTICS
# ============================================================

def get_database_statistics():
    """
    Return basic database statistics.
    """

    from database.models import (
        Product,
        ProductBatch,
        Sale,
        SaleItem,
    )

    db = SessionLocal()

    try:

        return {
            "products": (
                db.query(Product).count()
            ),
            "batches": (
                db.query(ProductBatch).count()
            ),
            "sales": (
                db.query(Sale).count()
            ),
            "sale_items": (
                db.query(SaleItem).count()
            ),
        }

    finally:

        db.close()


# ============================================================
# END OF FILE
# ============================================================