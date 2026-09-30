import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_invoice_pdf(sale, filepath):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    story = []
    styles = getSampleStyleSheet()

    # Styles sur-mesure
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        alignment=0
    )
    meta_style = ParagraphStyle(
        'InvoiceMeta',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )

    # Entête
    story.append(Paragraph("<b>PHARMACIE DE GARDE</b>", title_style))
    story.append(Paragraph("SANTÉ & BIEN-ÊTRE", meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=15))

    # Info Facture
    info_data = [
        [
            Paragraph(f"<b>N° Facture :</b> {sale.invoice_number}<br/><b>Date :</b> {sale.created_at.strftime('%d/%m/%Y %H:%M')}", meta_style),
            Paragraph(f"<b>Client :</b> {sale.client_name}<br/><b>Paiement :</b> {sale.payment_method}", meta_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Articles
    table_data = [["Désignation", "Qté", "P.U (CDF)", "Total (CDF)"]]
    for item in sale.items:
        prod_name = item.product.name if item.product else "Produit retiré"
        table_data.append([
            prod_name,
            str(item.quantity),
            f"{item.unit_price:,.2f}",
            f"{item.quantity * item.unit_price:,.2f}"
        ])

    table_data.append(["", "", "TOTAL :", f"{sale.total:,.2f} CDF"])

    t = Table(table_data, colWidths=[250, 60, 100, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2,-1), (-1,-1), colors.HexColor('#0F172A')),
        ('TOPPADDING', (0,-1), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 30))
    story.append(Paragraph("<para align='center'><i>Merci pour votre confiance. Bon rétablissement !</i></para>", meta_style))

    doc.build(story)