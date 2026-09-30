from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database.database import SessionLocal
from database.models import Product, Sale

REPORT_DIR = Path.home() / "Documents" / "Pharmacie" / "Rapports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_stock_pdf():
    session = SessionLocal()
    try:
        filename = REPORT_DIR / f"stock_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        c = canvas.Canvas(str(filename), pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 800, "Rapport de stock - Pharmacie")
        y = 765
        c.setFont("Helvetica", 10)
        for p in session.query(Product).order_by(Product.name).all():
            text = f"{p.name} | {p.category} | Stock: {p.quantity} | Prix: {p.price:.2f}"
            c.drawString(50, y, text[:110])
            y -= 18
            if y < 50:
                c.showPage()
                y = 800
        c.save()
        return filename
    finally:
        session.close()
