# database/database.py

from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import (
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base,
)


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


def column_exists(
    table_name,
    column_name,
):
    """
    Check whether a column exists in a SQLite table.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return False

    columns = inspector.get_columns(
        table_name
    )

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

def safe_int(
    value,
    default=0,
):
    """
    Safely convert a value to integer.
    """

    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# 6. SAFE FLOAT
# ============================================================

def safe_float(
    value,
    default=0.0,
):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# 7. SAFE DATE
# ============================================================

def parse_date_safe(
    value,
    default=None,
):
    """
    Convert legacy SQLite date/datetime values
    into a Python date.

    Accepts:
        2026-09-29
        2026-09-29 17:35:00
        2026-09-29T17:35:00
        datetime/date objects
    """

    if value is None:
        return default

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

    raw = str(value).strip()

    if not raw:
        return default

    if len(raw) >= 10:

        candidate = raw[:10]

        try:
            return date.fromisoformat(
                candidate
            )

        except ValueError:
            pass

    try:

        return datetime.fromisoformat(
            raw.replace(
                "Z",
                "+00:00",
            )
        ).date()

    except (
        TypeError,
        ValueError,
    ):
        return default


# ============================================================
# 8. NORMALIZE LEGACY DATE COLUMNS
# ============================================================

def normalize_legacy_date_columns():
    """
    Normalize old SQLite date columns before
    SQLAlchemy ORM reads them.
    """

    tables_and_columns = {
        "products": [
            "expiry_date",
        ],
        "sale_items": [
            "expiry_date",
        ],
        "product_batches": [
            "expiry_date",
        ],
        "expenses": [
            "expense_date",
        ],
    }

    with engine.begin() as connection:

        for (
            table_name,
            columns,
        ) in tables_and_columns.items():

            if not table_exists(
                table_name
            ):
                continue

            for column_name in columns:

                if not column_exists(
                    table_name,
                    column_name,
                ):
                    continue

                connection.execute(
                    text(
                        f"""
                        UPDATE {table_name}
                        SET {column_name} =
                            substr(
                                {column_name},
                                1,
                                10
                            )
                        WHERE {column_name} IS NOT NULL
                          AND length(
                              CAST(
                                  {column_name}
                                  AS TEXT
                              )
                          ) > 10
                        """
                    )
                )


# ============================================================
# 9. NORMALIZE UNIT NAME
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
# 10. PRODUCT CONVERSION VALUES
# ============================================================

def get_units_per_plaquette(product):
    """
    Return number of base units in one plaquette.
    """

    value = safe_int(
        getattr(
            product,
            "units_per_plaquette",
            10,
        ),
        10,
    )

    return max(
        1,
        value,
    )


def get_plaquettes_per_box(product):
    """
    Return number of plaquettes in one box.
    """

    value = safe_int(
        getattr(
            product,
            "plaquettes_per_box",
            10,
        ),
        10,
    )

    return max(
        1,
        value,
    )


def get_boxes_per_carton(product):
    """
    Return number of boxes in one carton.
    """

    value = safe_int(
        getattr(
            product,
            "boxes_per_carton",
            10,
        ),
        10,
    )

    return max(
        1,
        value,
    )


def get_units_per_box(product):
    """
    Return number of base units in one box.
    """

    return (
        get_units_per_plaquette(product)
        * get_plaquettes_per_box(product)
    )


def get_units_per_carton(product):
    """
    Return number of base units in one carton.
    """

    return (
        get_units_per_box(product)
        * get_boxes_per_carton(product)
    )


# ============================================================
# 11. CONVERT PACKAGING TO BASE UNITS
# ============================================================

def get_units_for_packaging(
    product,
    packaging,
):
    """
    Convert one packaging unit into base units.
    """

    packaging = normalize_unit(
        packaging
    )

    if packaging == "Comprimé":
        return 1

    if packaging == "Plaquette":
        return get_units_per_plaquette(
            product
        )

    if packaging == "Boîte":
        return get_units_per_box(
            product
        )

    if packaging == "Carton":
        return get_units_per_carton(
            product
        )

    return 1


# ============================================================
# 12. CONVERT QUANTITY TO BASE UNITS
# ============================================================

def convert_to_base_units(
    product,
    quantity,
    unit,
):
    """
    Convert a quantity into base units.
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
# 13. STOCK DISPLAY
# ============================================================

def get_stock_display(product):
    """
    Convert global stock into a readable format.
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
        get_units_per_plaquette(
            product
        )
    )

    units_per_box = (
        get_units_per_box(
            product
        )
    )

    units_per_carton = (
        get_units_per_carton(
            product
        )
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
# 14. UPDATE LEGACY QUANTITY
# ============================================================

def get_main_packaging_quantity(
    product
):
    """
    Calculate the number of complete main
    packaging units.
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


def update_display_quantity(
    product
):
    """
    Synchronize the old quantity field
    with stock_units.
    """

    quantity = (
        get_main_packaging_quantity(
            product
        )
    )

    product.quantity = quantity

    return quantity


# ============================================================
# 15. PRICE MANAGEMENT
# ============================================================

def get_price_for_packaging(
    product,
    packaging,
):
    """
    Return the selling price for a unit.
    """

    packaging = normalize_unit(
        packaging
    )

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


def calculate_product_prices(
    product
):
    """
    Calculate packaging prices from
    the product's main price.
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
        get_units_per_plaquette(
            product
        )
    )

    plaquettes_per_box = (
        get_plaquettes_per_box(
            product
        )
    )

    boxes_per_carton = (
        get_boxes_per_carton(
            product
        )
    )

    packaging = normalize_unit(
        getattr(
            product,
            "packaging",
            "Boîte",
        )
    )

    if packaging == "Comprimé":

        price_per_comprime = (
            base_price
        )

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

        price_per_plaquette = (
            base_price
        )

        price_per_box = (
            base_price
            * plaquettes_per_box
        )

        price_per_carton = (
            price_per_box
            * boxes_per_carton
        )

    elif packaging == "Carton":

        price_per_carton = (
            base_price
        )

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

        price_per_box = (
            base_price
        )

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
# 16. EXPIRATION
# ============================================================

def is_product_expired(product):
    """
    Legacy product expiration check.
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

    return (
        batch.expiry_date
        < date.today()
    )


def days_until_expiration(batch):
    """
    Return number of days remaining before expiration.
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
    Return True if the batch expires within
    the specified period.
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
# 17. BATCH VALIDATION
# ============================================================

def validate_batch_expiry(
    product,
    expiry_date,
):
    """
    Validate a batch expiration date.
    """

    is_medicine = bool(
        getattr(
            product,
            "is_medicine",
            True,
        )
    )

    if (
        is_medicine
        and not expiry_date
    ):
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
# 18. GET ACTIVE BATCHES
# ============================================================

def get_available_batches(
    product,
    db=None,
):
    """
    Return active batches with stock > 0,
    ordered using FEFO.
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
# 19. GET FIRST EXPIRING BATCH
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
# 20. CALCULATE GLOBAL STOCK
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
# 21. SYNCHRONIZE PRODUCT STOCK
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
# 22. ADD STOCK TO A BATCH
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
# 23. ADD PRODUCT STOCK
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
# 24. CHECK PRODUCT STOCK
# ============================================================

def can_sell_product(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Check whether enough non-expired stock exists.
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

        if is_batch_expired(
            batch
        ):
            continue

        available_units += safe_int(
            batch.stock_units,
            0,
        )

        if (
            available_units
            >= required_units
        ):
            return True

    return False


# ============================================================
# 25. CALCULATE STOCK AFTER SALE
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
# 26. REDUCE STOCK FROM BATCHES
# ============================================================

def reduce_stock_from_batches(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Remove stock using FEFO.

    Expired batches are never sold.
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

            if is_batch_expired(
                batch
            ):
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
                    "batch_number": (
                        batch.batch_number
                    ),
                    "expiry_date": (
                        batch.expiry_date
                    ),
                    "stock_units": (
                        units_to_remove
                    ),
                }
            )

            if batch.stock_units <= 0:

                batch.stock_units = 0

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
# 27. LEGACY REDUCE STOCK
# ============================================================

def reduce_product_stock(
    product,
    quantity,
    packaging,
    db=None,
):
    """
    Compatibility wrapper.
    """

    result = reduce_stock_from_batches(
        product=product,
        quantity=quantity,
        packaging=packaging,
        db=db,
    )

    return result["total_units"]


# ============================================================
# 28. LOW STOCK
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
# 29. GET EXPIRING BATCHES
# ============================================================

def get_expiring_batches(
    days=90,
    db=None,
):
    """
    Return batches expiring within the next
    specified number of days.
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
# 30. GET EXPIRED BATCHES
# ============================================================

def get_expired_batches(
    db=None
):
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
# 31. DEACTIVATE EXPIRED BATCHES
# ============================================================

def deactivate_expired_batches(
    db=None
):
    """
    Mark expired batches as inactive.

    Their stock is NOT deleted.
    """

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        batches = get_expired_batches(
            db
        )

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
# 32. EXPENSE CATEGORIES
# ============================================================

EXPENSE_CATEGORIES = [
    "Nourriture",
    "Transport",
    "Fournitures",
    "Électricité",
    "Eau",
    "Internet / Téléphone",
    "Entretien",
    "Loyer",
    "Salaire",
    "Taxes / Frais",
    "Autre",
]


EXPENSE_PAYMENT_METHODS = [
    "Espèces",
    "Mobile Money",
    "Carte bancaire",
    "Virement",
]


# ============================================================
# 33. UPDATE OLD DATABASE SCHEMA
# ============================================================

def update_database_schema():
    """
    Update an existing pharmacy database.

    Missing columns are added without deleting data.

    Important:
    The Expense model now uses `description`.

    Older versions used `title`.

    Existing title values are copied into description.
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
            "DATE",
        )

    # ========================================================
    # PRODUCT BATCHES
    # ========================================================

    if "product_batches" in tables:

        add_column_if_not_exists(
            "product_batches",
            "product_id",
            "INTEGER",
        )

        add_column_if_not_exists(
            "product_batches",
            "batch_number",
            "VARCHAR(100)",
        )

        add_column_if_not_exists(
            "product_batches",
            "expiry_date",
            "DATE",
        )

        add_column_if_not_exists(
            "product_batches",
            "stock_units",
            "INTEGER DEFAULT 0",
        )

        add_column_if_not_exists(
            "product_batches",
            "purchase_quantity",
            "INTEGER DEFAULT 0",
        )

        add_column_if_not_exists(
            "product_batches",
            "purchase_unit",
            "VARCHAR(50) DEFAULT 'Boîte'",
        )

        add_column_if_not_exists(
            "product_batches",
            "purchase_price",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "product_batches",
            "supplier",
            "VARCHAR(150) DEFAULT ''",
        )

        add_column_if_not_exists(
            "product_batches",
            "received_at",
            "DATE",
        )

        add_column_if_not_exists(
            "product_batches",
            "is_active",
            "BOOLEAN DEFAULT 1",
        )

    # ========================================================
    # SALES
    # ========================================================

    if "sales" in tables:

        add_column_if_not_exists(
            "sales",
            "invoice_number",
            "VARCHAR(80)",
        )

        add_column_if_not_exists(
            "sales",
            "client_name",
            "VARCHAR(150) DEFAULT 'Client comptant'",
        )

        add_column_if_not_exists(
            "sales",
            "total",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "sales",
            "payment_method",
            "VARCHAR(50) DEFAULT 'Espèces'",
        )

        add_column_if_not_exists(
            "sales",
            "created_at",
            "DATE",
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

    # ========================================================
    # EXPENSES
    # ========================================================

    if "expenses" in tables:

        # ----------------------------------------------------
        # New column
        # ----------------------------------------------------

        add_column_if_not_exists(
            "expenses",
            "description",
            "VARCHAR(200) DEFAULT ''",
        )

        add_column_if_not_exists(
            "expenses",
            "category",
            "VARCHAR(100) DEFAULT 'Autre'",
        )

        add_column_if_not_exists(
            "expenses",
            "amount",
            "FLOAT DEFAULT 0",
        )

        add_column_if_not_exists(
            "expenses",
            "expense_date",
            "DATE",
        )

        add_column_if_not_exists(
            "expenses",
            "payment_method",
            "VARCHAR(50) DEFAULT 'Espèces'",
        )

        add_column_if_not_exists(
            "expenses",
            "note",
            "TEXT DEFAULT ''",
        )

        add_column_if_not_exists(
            "expenses",
            "created_by",
            "VARCHAR(150) DEFAULT ''",
        )

        add_column_if_not_exists(
            "expenses",
            "created_at",
            "DATETIME",
        )

        # ----------------------------------------------------
        # Old column from previous version
        # ----------------------------------------------------

        if column_exists(
            "expenses",
            "title",
        ) and column_exists(
            "expenses",
            "description",
        ):

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        UPDATE expenses
                        SET description = title
                        WHERE (
                            description IS NULL
                            OR TRIM(description) = ''
                        )
                        AND title IS NOT NULL
                        AND TRIM(title) <> ''
                        """
                    )
                )

                print(
                    "✓ Migration expenses.title "
                    "→ expenses.description terminée."
                )


# ============================================================
# 34. MIGRATE OLD STOCK TO BATCHES
# ============================================================

def migrate_old_stock_to_batches():
    """
    Migrate old Product stock into ProductBatch.
    """

    from database.models import ProductBatch

    normalize_legacy_date_columns()

    db = SessionLocal()

    try:

        if not table_exists("products"):
            return

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
                    ProductBatch.product_id
                    == product_id
                )
                .first()
            )

            if existing_batch:
                continue

            packaging = normalize_unit(
                row["packaging"]
                or "Boîte"
            )

            stock_units = safe_int(
                row["stock_units"],
                0,
            )

            quantity = safe_int(
                row["quantity"],
                0,
            )

            if (
                stock_units <= 0
                and quantity > 0
            ):

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
                    {
                        "product_id": product_id
                    },
                ).mappings().first()

                class LegacyProduct:
                    pass

                legacy_product = (
                    LegacyProduct()
                )

                legacy_product.units_per_plaquette = (
                    product_data[
                        "units_per_plaquette"
                    ]
                    if product_data
                    else 10
                )

                legacy_product.plaquettes_per_box = (
                    product_data[
                        "plaquettes_per_box"
                    ]
                    if product_data
                    else 10
                )

                legacy_product.boxes_per_carton = (
                    product_data[
                        "boxes_per_carton"
                    ]
                    if product_data
                    else 10
                )

                stock_units = (
                    convert_to_base_units(
                        legacy_product,
                        quantity,
                        packaging,
                    )
                )

            if stock_units <= 0:
                continue

            batch_number = (
                row["batch_number"]
                or f"LEGACY-{product_id}"
            )

            expiry_date = (
                parse_date_safe(
                    row["expiry_date"]
                )
            )

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
                supplier=(
                    row["supplier"]
                    or ""
                ),
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
# 35. INITIALIZE STOCK
# ============================================================

def initialize_stock_units():
    """
    Initialize and synchronize product stock.
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
# 36. UPDATE ALL PRODUCT PRICES
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
# 37. EXPENSE MODEL ACCESS
# ============================================================

def get_expense_model():
    """
    Return the unique Expense ORM model.

    Expense is defined ONLY in database.models.
    """

    from database.models import Expense

    return Expense


# ============================================================
# 38. CREATE EXPENSE
# ============================================================

def create_expense(
    title=None,
    amount=0.0,
    category="Autre",
    expense_date=None,
    payment_method="Espèces",
    note="",
    created_by="",
    db=None,
    description=None,
):
    """
    Create a manual expense.

    Compatibility:
        title       = old parameter name
        description = new parameter name

    The database model uses:
        Expense.description
    """

    Expense = get_expense_model()

    # --------------------------------------------------------
    # Compatibility title -> description
    # --------------------------------------------------------

    if description is None:
        description = title

    description = str(
        description or ""
    ).strip()

    if not description:

        raise ValueError(
            "Le libellé de la dépense est obligatoire."
        )

    amount = safe_float(
        amount,
        0.0,
    )

    if amount <= 0:

        raise ValueError(
            "Le montant de la dépense doit être "
            "supérieur à zéro."
        )

    category = str(
        category or "Autre"
    ).strip()

    if not category:
        category = "Autre"

    payment_method = str(
        payment_method
        or "Espèces"
    ).strip()

    if not payment_method:
        payment_method = "Espèces"

    expense_date = parse_date_safe(
        expense_date,
        date.today(),
    )

    if expense_date is None:
        expense_date = date.today()

    note = str(
        note or ""
    ).strip()

    created_by = str(
        created_by or ""
    ).strip()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        expense = Expense(
            description=description,
            amount=round(
                amount,
                2,
            ),
            category=category,
            expense_date=expense_date,
            payment_method=payment_method,
            note=note,
            created_by=created_by,
            created_at=datetime.now(),
        )

        db.add(expense)

        db.flush()

        if close_session:
            db.commit()

        return expense

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 39. GET EXPENSE BY ID
# ============================================================

def get_expense(
    expense_id,
    db=None,
):
    """
    Return one expense by ID.
    """

    Expense = get_expense_model()

    expense_id = safe_int(
        expense_id,
        0,
    )

    if expense_id <= 0:
        return None

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        return (
            db.query(Expense)
            .filter(
                Expense.id
                == expense_id
            )
            .first()
        )

    finally:

        if close_session:
            db.close()


# ============================================================
# 40. GET ALL EXPENSES
# ============================================================

def get_expenses(
    expense_date=None,
    category=None,
    search=None,
    limit=None,
    db=None,
):
    """
    Return expenses.

    Optional filters:
        expense_date
        category
        search
        limit
    """

    Expense = get_expense_model()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        query = db.query(
            Expense
        )

        parsed_date = parse_date_safe(
            expense_date
        )

        if parsed_date:

            query = query.filter(
                Expense.expense_date
                == parsed_date
            )

        if category:

            category = str(
                category
            ).strip()

            if (
                category
                and category != "Toutes"
            ):

                query = query.filter(
                    Expense.category
                    == category
                )

        if search:

            search = str(
                search
            ).strip()

            if search:

                pattern = (
                    f"%{search}%"
                )

                query = query.filter(
                    (
                        Expense.description.ilike(
                            pattern
                        )
                    )
                    |
                    (
                        Expense.note.ilike(
                            pattern
                        )
                    )
                    |
                    (
                        Expense.category.ilike(
                            pattern
                        )
                    )
                )

        query = query.order_by(
            Expense.expense_date.desc(),
            Expense.created_at.desc(),
            Expense.id.desc(),
        )

        if limit is not None:

            limit = safe_int(
                limit,
                0,
            )

            if limit > 0:
                query = query.limit(
                    limit
                )

        return query.all()

    finally:

        if close_session:
            db.close()


# ============================================================
# 41. UPDATE EXPENSE
# ============================================================

def update_expense(
    expense_id,
    title=None,
    amount=None,
    category=None,
    expense_date=None,
    payment_method=None,
    note=None,
    db=None,
    description=None,
):
    """
    Update an existing expense.

    Compatibility:
        title       = old parameter
        description = new parameter
    """

    Expense = get_expense_model()

    expense_id = safe_int(
        expense_id,
        0,
    )

    if expense_id <= 0:

        raise ValueError(
            "Identifiant de dépense invalide."
        )

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        expense = (
            db.query(Expense)
            .filter(
                Expense.id
                == expense_id
            )
            .first()
        )

        if expense is None:

            raise ValueError(
                "Cette dépense n'existe pas."
            )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        if description is None:
            description = title

        if description is not None:

            description = str(
                description
            ).strip()

            if not description:

                raise ValueError(
                    "Le libellé de la dépense "
                    "est obligatoire."
                )

            expense.description = (
                description
            )

        # ----------------------------------------------------
        # AMOUNT
        # ----------------------------------------------------

        if amount is not None:

            amount = safe_float(
                amount,
                0.0,
            )

            if amount <= 0:

                raise ValueError(
                    "Le montant doit être "
                    "supérieur à zéro."
                )

            expense.amount = round(
                amount,
                2,
            )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        if category is not None:

            category = str(
                category
            ).strip()

            expense.category = (
                category
                or "Autre"
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        if expense_date is not None:

            parsed_date = (
                parse_date_safe(
                    expense_date
                )
            )

            if parsed_date is None:

                raise ValueError(
                    "Date de dépense invalide."
                )

            expense.expense_date = (
                parsed_date
            )

        # ----------------------------------------------------
        # PAYMENT
        # ----------------------------------------------------

        if payment_method is not None:

            payment_method = str(
                payment_method
            ).strip()

            expense.payment_method = (
                payment_method
                or "Espèces"
            )

        # ----------------------------------------------------
        # NOTE
        # ----------------------------------------------------

        if note is not None:

            expense.note = str(
                note
            ).strip()

        expense.created_at = (
            getattr(
                expense,
                "created_at",
                None,
            )
            or datetime.now()
        )

        db.flush()

        if close_session:
            db.commit()

        return expense

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 42. DELETE EXPENSE
# ============================================================

def delete_expense(
    expense_id,
    db=None,
):
    """
    Delete an expense.

    Returns:
        True if deleted.
    """

    Expense = get_expense_model()

    expense_id = safe_int(
        expense_id,
        0,
    )

    if expense_id <= 0:
        return False

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        expense = (
            db.query(Expense)
            .filter(
                Expense.id
                == expense_id
            )
            .first()
        )

        if expense is None:
            return False

        db.delete(expense)

        db.flush()

        if close_session:
            db.commit()

        return True

    except Exception:

        if close_session:
            db.rollback()

        raise

    finally:

        if close_session:
            db.close()


# ============================================================
# 43. DAILY EXPENSE TOTAL
# ============================================================

def get_daily_expense_total(
    expense_date=None,
    db=None,
):
    """
    Return total expenses for one day.
    """

    Expense = get_expense_model()

    expense_date = parse_date_safe(
        expense_date,
        date.today(),
    )

    if expense_date is None:
        expense_date = date.today()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        result = (
            db.query(
                Expense.amount
            )
            .filter(
                Expense.expense_date
                == expense_date
            )
            .all()
        )

        total = sum(
            safe_float(
                row[0],
                0.0,
            )
            for row in result
        )

        return round(
            total,
            2,
        )

    finally:

        if close_session:
            db.close()


# ============================================================
# 44. MONTHLY EXPENSE TOTAL
# ============================================================

def get_monthly_expense_total(
    year=None,
    month=None,
    db=None,
):
    """
    Return total expenses for a month.
    """

    Expense = get_expense_model()

    today = date.today()

    year = safe_int(
        year,
        today.year,
    )

    month = safe_int(
        month,
        today.month,
    )

    if month < 1 or month > 12:
        month = today.month

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        next_year = (
            year + 1
            if month == 12
            else year
        )

        next_month = (
            1
            if month == 12
            else month + 1
        )

        result = (
            db.query(
                Expense.amount
            )
            .filter(
                Expense.expense_date
                >= date(
                    year,
                    month,
                    1,
                )
            )
            .filter(
                Expense.expense_date
                < date(
                    next_year,
                    next_month,
                    1,
                )
            )
            .all()
        )

        total = sum(
            safe_float(
                row[0],
                0.0,
            )
            for row in result
        )

        return round(
            total,
            2,
        )

    finally:

        if close_session:
            db.close()


# ============================================================
# 45. EXPENSE COUNT
# ============================================================

def get_expense_count(
    expense_date=None,
    category=None,
    db=None,
):
    """
    Count expenses.

    If expense_date is supplied, only that date
    is counted.
    """

    Expense = get_expense_model()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        query = db.query(
            Expense
        )

        parsed_date = parse_date_safe(
            expense_date
        )

        if parsed_date:

            query = query.filter(
                Expense.expense_date
                == parsed_date
            )

        if category:

            category = str(
                category
            ).strip()

            if (
                category
                and category != "Toutes"
            ):

                query = query.filter(
                    Expense.category
                    == category
                )

        return query.count()

    finally:

        if close_session:
            db.close()


# ============================================================
# 46. EXPENSE TOTAL BY CATEGORY
# ============================================================

def get_expense_totals_by_category(
    expense_date=None,
    db=None,
):
    """
    Return expense totals grouped by category.
    """

    Expense = get_expense_model()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        query = db.query(
            Expense
        )

        parsed_date = parse_date_safe(
            expense_date
        )

        if parsed_date:

            query = query.filter(
                Expense.expense_date
                == parsed_date
            )

        expenses = query.all()

        totals = {}

        for expense in expenses:

            category = (
                expense.category
                or "Autre"
            )

            amount = safe_float(
                expense.amount,
                0.0,
            )

            totals[category] = round(
                totals.get(
                    category,
                    0.0,
                )
                + amount,
                2,
            )

        return totals

    finally:

        if close_session:
            db.close()


# ============================================================
# 47. EXPENSE STATISTICS
# ============================================================

def get_expense_statistics(
    expense_date=None,
    db=None,
):
    """
    Return complete expense statistics
    for the selected day.
    """

    selected_date = (
        parse_date_safe(
            expense_date,
            date.today(),
        )
    )

    if selected_date is None:
        selected_date = date.today()

    daily_total = (
        get_daily_expense_total(
            selected_date,
            db,
        )
    )

    count = get_expense_count(
        selected_date,
        db=db,
    )

    by_category = (
        get_expense_totals_by_category(
            selected_date,
            db,
        )
    )

    return {
        "date": selected_date,
        "total": daily_total,
        "count": count,
        "by_category": by_category,
    }


# ============================================================
# 48. EXPENSE TABLE
# ============================================================

def ensure_expense_table():
    """
    Ensure that the expenses table exists.

    Expense is defined only in database.models.
    """

    from database.models import Expense

    Base.metadata.create_all(
        bind=engine,
        tables=[
            Expense.__table__,
        ],
    )

    return True


# ============================================================
# 49. DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Initialize the pharmacy database.

    No demo products are created automatically.
    """

    # --------------------------------------------------------
    # Import models HERE, after Base exists.
    # --------------------------------------------------------

    from database.models import (
        Product,
        ProductBatch,
        Sale,
        SaleItem,
        Expense,
    )

    # Avoid "unused import" confusion.
    _ = (
        Product,
        ProductBatch,
        Sale,
        SaleItem,
        Expense,
    )

    print("")
    print("=" * 70)
    print(
        "INITIALISATION DE LA BASE DE DONNÉES"
    )
    print("=" * 70)

    print(
        f"Database : {DATABASE_PATH}"
    )

    print("")

    try:

        # ----------------------------------------------------
        # CREATE ALL ORM TABLES
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        print(
            "✓ Tables vérifiées/créées."
        )

        # ----------------------------------------------------
        # UPDATE EXISTING DATABASE
        # ----------------------------------------------------

        update_database_schema()

        # ----------------------------------------------------
        # MIGRATE OLD EXPENSE DATA
        # ----------------------------------------------------

        # If the old database contains:
        #
        # title
        #
        # it is copied to:
        #
        # description
        #
        # The old column is intentionally NOT deleted.
        #

        if table_exists("expenses"):

            if (
                column_exists(
                    "expenses",
                    "title",
                )
                and column_exists(
                    "expenses",
                    "description",
                )
            ):

                with engine.begin() as connection:

                    connection.execute(
                        text(
                            """
                            UPDATE expenses
                            SET description = title
                            WHERE (
                                description IS NULL
                                OR TRIM(description) = ''
                            )
                            AND title IS NOT NULL
                            AND TRIM(title) <> ''
                            """
                        )
                    )

        # ----------------------------------------------------
        # NORMALIZE DATES
        # ----------------------------------------------------

        normalize_legacy_date_columns()

        # ----------------------------------------------------
        # CREATE / VERIFY TABLES AGAIN
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        print(
            "✓ Table ProductBatch vérifiée/créée."
        )

        print(
            "✓ Table Dépenses vérifiée/créée."
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

        deactivated = (
            deactivate_expired_batches()
        )

        if deactivated > 0:

            print(
                f"✓ {deactivated} lot(s) expiré(s) "
                f"désactivé(s)."
            )

        # ----------------------------------------------------
        # NO DEMO DATA
        # ----------------------------------------------------

        print("")

        print(
            "✓ Aucun produit de démonstration ajouté."
        )

        print(
            "✓ Gestion des dépenses activée."
        )

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
# 50. DATABASE INFORMATION
# ============================================================

def get_database_path():
    """
    Return database path.
    """

    return str(
        DATABASE_PATH
    )


def database_exists():
    """
    Check whether database exists.
    """

    return DATABASE_PATH.exists()


# ============================================================
# 51. DATABASE CONNECTION TEST
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
# 52. GET DATABASE STATISTICS
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
        Expense,
    )

    db = SessionLocal()

    try:

        return {
            "products": (
                db.query(
                    Product
                ).count()
            ),

            "batches": (
                db.query(
                    ProductBatch
                ).count()
            ),

            "sales": (
                db.query(
                    Sale
                ).count()
            ),

            "sale_items": (
                db.query(
                    SaleItem
                ).count()
            ),

            "expenses": (
                db.query(
                    Expense
                ).count()
            ),

            "expenses_today": (
                get_daily_expense_total(
                    db=db
                )
            ),

            "expenses_month": (
                get_monthly_expense_total(
                    db=db
                )
            ),
        }

    finally:

        db.close()


# ============================================================
# 53. GET FINANCIAL DAILY SUMMARY
# ============================================================

def get_daily_financial_summary(
    selected_date=None,
    db=None,
):
    """
    Return a summary useful for the dashboard.

    Includes:
        - sales of the day
        - expenses of the day
        - number of expenses
        - balance
    """

    from database.models import Sale

    selected_date = parse_date_safe(
        selected_date,
        date.today(),
    )

    if selected_date is None:
        selected_date = date.today()

    close_session = False

    if db is None:
        db = SessionLocal()
        close_session = True

    try:

        # ----------------------------------------------------
        # SALES
        # ----------------------------------------------------

        sales = (
            db.query(Sale)
            .all()
        )

        sales_total = 0.0

        for sale in sales:

            sale_date = getattr(
                sale,
                "created_at",
                None,
            )

            if sale_date:

                sale_date = (
                    parse_date_safe(
                        sale_date
                    )
                )

                if sale_date != selected_date:
                    continue

            else:
                continue

            sale_amount = safe_float(
                getattr(
                    sale,
                    "total",
                    0,
                ),
                0.0,
            )

            sales_total += (
                sale_amount
            )

        # ----------------------------------------------------
        # EXPENSES
        # ----------------------------------------------------

        expenses_total = (
            get_daily_expense_total(
                selected_date,
                db,
            )
        )

        expenses_count = (
            get_expense_count(
                selected_date,
                db=db,
            )
        )

        balance = (
            sales_total
            - expenses_total
        )

        return {
            "date": selected_date,
            "sales": round(
                sales_total,
                2,
            ),
            "expenses": round(
                expenses_total,
                2,
            ),
            "expenses_count": (
                expenses_count
            ),
            "balance": round(
                balance,
                2,
            ),
        }

    finally:

        if close_session:
            db.close()


# ============================================================
# END OF FILE
# ============================================================