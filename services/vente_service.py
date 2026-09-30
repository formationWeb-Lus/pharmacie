from database.database import SessionLocal
from database.models import Product, Sale, SaleItem

def create_sale(items, payment_method="Cash"):
    # items = [{"product_id": int, "quantity": int}]
    session = SessionLocal()
    try:
        total = 0
        sale = Sale(payment_method=payment_method, total=0)
        session.add(sale)
        session.flush()

        for item in items:
            product = session.get(Product, item["product_id"])
            qty = int(item["quantity"])
            if not product:
                raise ValueError("Produit introuvable.")
            if qty <= 0:
                raise ValueError("Quantité invalide.")
            if product.quantity < qty:
                raise ValueError(f"Stock insuffisant pour {product.name}.")
            product.quantity -= qty
            total += product.price * qty
            sale.items.append(SaleItem(
                product_id=product.id,
                quantity=qty,
                unit_price=product.price
            ))

        sale.total = total
        session.commit()
        return sale.id, total
    except:
        session.rollback()
        raise
    finally:
        session.close()
