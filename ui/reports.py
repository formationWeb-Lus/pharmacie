from PySide6.QtWidgets import *
from services.report_service import export_stock_pdf

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout=QVBoxLayout(self)
        title=QLabel("Rapports")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        btn=QPushButton("📄 Exporter le rapport de stock en PDF")
        btn.clicked.connect(self.pdf)
        layout.addWidget(btn)
        layout.addStretch()

    def pdf(self):
        try:
            path=export_stock_pdf()
            QMessageBox.information(self,"Rapport créé",f"Rapport enregistré ici :\n{path}")
        except Exception as e:
            QMessageBox.critical(self,"Erreur",str(e))

    def refresh(self):
        pass
