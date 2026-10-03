
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QLineEdit,
    QDialog,
    QDoubleSpinBox,
    QDateEdit,
    QTextEdit,
    QScrollArea,
    QMessageBox,
    QSizePolicy,
    QAbstractItemView,
)

from database.database import SessionLocal
from database.models import Expense


# ============================================================
# COULEURS
# ============================================================

NAVY = "#0F2747"
BLUE = "#2563EB"
GREEN = "#12B76A"
RED = "#D92D20"
ORANGE = "#F79009"
PURPLE = "#7A5AF8"
TEAL = "#0E9384"

BG = "#F6F8FC"
WHITE = "#FFFFFF"
TEXT = "#101828"
TEXT_MUTED = "#667085"
BORDER = "#E4E7EC"
INPUT_BG = "#F9FAFB"


# ============================================================
# UTILITAIRES
# ============================================================

def get_current_user_name(current_user: Any) -> str:
    """
    Essaie de récupérer le nom de l'utilisateur connecté.
    Compatible avec plusieurs structures d'objet utilisateur.
    """

    if current_user is None:
        return ""

    possible_fields = [
        "full_name",
        "name",
        "username",
        "user_name",
        "email",
    ]

    for field in possible_fields:
        try:
            value = getattr(current_user, field, None)
            if value:
                return str(value).strip()
        except Exception:
            pass

    if isinstance(current_user, dict):
        for field in possible_fields:
            value = current_user.get(field)
            if value:
                return str(value).strip()

    return ""


# ============================================================
# CARTE KPI
# ============================================================

class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        icon: str,
        accent: str,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("statCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icon_box = QLabel(icon)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(48, 48)

        icon_box.setStyleSheet(
            f"""
            QLabel {{
                background: {accent}18;
                color: {accent};
                border-radius: 14px;
                font-size: 22px;
                font-weight: 700;
            }}
            """
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                font-size: 22px;
                font-weight: 800;
            }}
            """
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(self.value_label)

        layout.addWidget(icon_box)
        layout.addLayout(text_layout, 1)

        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )

    def set_value(self, value: str):
        self.value_label.setText(value)


# ============================================================
# DIALOGUE AJOUT DÉPENSE
# ============================================================

class ExpenseDialog(QDialog):
    """
    Dialogue d'ajout d'une dépense.

    Important :
    - Le formulaire est entièrement scrollable.
    - Les boutons restent toujours visibles.
    - Une dépense enregistrée ne peut pas être modifiée
      depuis cette interface.
    """

    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)

        self.current_user = current_user

        self.setWindowTitle("Nouvelle dépense")
        self.resize(580, 700)
        self.setMinimumSize(520, 580)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG};
            }}

            QLabel#dialogTitle {{
                color: {NAVY};
                font-size: 22px;
                font-weight: 800;
            }}

            QLabel#dialogSubtitle {{
                color: {TEXT_MUTED};
                font-size: 13px;
            }}

            QLabel.fieldLabel {{
                color: {TEXT};
                font-size: 13px;
                font-weight: 700;
                margin-top: 4px;
            }}

            QLineEdit,
            QComboBox,
            QDoubleSpinBox,
            QDateEdit,
            QTextEdit {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 9px 11px;
                color: {TEXT};
                font-size: 13px;
            }}

            QLineEdit:focus,
            QComboBox:focus,
            QDoubleSpinBox:focus,
            QDateEdit:focus,
            QTextEdit:focus {{
                border: 2px solid {BLUE};
            }}

            QPushButton#cancelButton {{
                background: {WHITE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
            }}

            QPushButton#cancelButton:hover {{
                background: #F2F4F7;
            }}

            QPushButton#saveButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 700;
            }}

            QPushButton#saveButton:hover {{
                background: #1D4ED8;
            }}

            QScrollArea {{
                border: none;
                background: transparent;
            }}

            QScrollBar:vertical {{
                background: #EEF2F6;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }}

            QScrollBar::handle:vertical {{
                background: #98A2B3;
                min-height: 40px;
                border-radius: 5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: #667085;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        self.build_ui()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 20, 22, 18)
        main_layout.setSpacing(12)

        # ----------------------------------------------------
        # EN-TÊTE
        # ----------------------------------------------------

        title = QLabel("Nouvelle dépense")
        title.setObjectName("dialogTitle")

        subtitle = QLabel(
            "Enregistrez une nouvelle dépense de la pharmacie."
        )
        subtitle.setObjectName("dialogSubtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ----------------------------------------------------
        # ZONE SCROLLABLE
        # ----------------------------------------------------

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        content = QWidget()
        content.setStyleSheet(
            f"""
            QWidget {{
                background: transparent;
            }}
            """
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 8, 8, 8)
        content_layout.setSpacing(12)

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        label = QLabel("Description *")
        label.setProperty("class", "fieldLabel")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            "Exemple : Achat de fournitures"
        )
        self.description_input.setMinimumHeight(42)

        content_layout.addWidget(label)
        content_layout.addWidget(self.description_input)

        # ----------------------------------------------------
        # CATÉGORIE
        # ----------------------------------------------------

        label = QLabel("Catégorie *")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(42)

        self.category_input.addItems(
            [
                "Achat de médicaments",
                "Fournitures",
                "Transport",
                "Électricité",
                "Eau",
                "Internet",
                "Loyer",
                "Salaires",
                "Maintenance",
                "Taxes",
                "Marketing",
                "Autre",
            ]
        )

        content_layout.addWidget(label)
        content_layout.addWidget(self.category_input)

        # ----------------------------------------------------
        # MONTANT
        # ----------------------------------------------------

        label = QLabel("Montant (CDF) *")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(999999999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(1000)
        self.amount_input.setSuffix(" CDF")
        self.amount_input.setMinimumHeight(42)

        content_layout.addWidget(label)
        content_layout.addWidget(self.amount_input)

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        label = QLabel("Date de la dépense *")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setMinimumHeight(42)

        content_layout.addWidget(label)
        content_layout.addWidget(self.date_input)

        # ----------------------------------------------------
        # MODE DE PAIEMENT
        # ----------------------------------------------------

        label = QLabel("Mode de paiement *")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.payment_input = QComboBox()
        self.payment_input.setMinimumHeight(42)

        self.payment_input.addItems(
            [
                "Espèces",
                "Mobile Money",
                "Carte bancaire",
                "Virement",
            ]
        )

        content_layout.addWidget(label)
        content_layout.addWidget(self.payment_input)

        # ----------------------------------------------------
        # SAISI PAR
        # ----------------------------------------------------

        label = QLabel("Saisi par *")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.created_by_input = QLineEdit()
        self.created_by_input.setPlaceholderText(
            "Nom de la personne qui saisit la dépense"
        )
        self.created_by_input.setMinimumHeight(42)

        current_name = get_current_user_name(
            self.current_user
        )

        if current_name:
            self.created_by_input.setText(current_name)

        content_layout.addWidget(label)
        content_layout.addWidget(self.created_by_input)

        # ----------------------------------------------------
        # NOTE
        # ----------------------------------------------------

        label = QLabel("Note")
        label.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText(
            "Ajoutez une remarque ou une information complémentaire..."
        )
        self.note_input.setMinimumHeight(130)
        self.note_input.setMaximumHeight(180)

        content_layout.addWidget(label)
        content_layout.addWidget(self.note_input)

        # ----------------------------------------------------
        # INFORMATION DE SÉCURITÉ
        # ----------------------------------------------------

        security = QFrame()
        security.setStyleSheet(
            f"""
            QFrame {{
                background: #EFF8FF;
                border: 1px solid #B2DDFF;
                border-radius: 12px;
            }}
            QLabel {{
                color: #175CD3;
                font-size: 12px;
                line-height: 18px;
            }}
            """
        )

        security_layout = QHBoxLayout(security)
        security_layout.setContentsMargins(
            14, 12, 14, 12
        )

        security_icon = QLabel("🔒")
        security_icon.setStyleSheet(
            "font-size: 20px; border: none;"
        )

        security_text = QLabel(
            "<b>Information :</b><br>"
            "Une fois enregistrée, cette dépense ne peut "
            "pas être modifiée ou supprimée depuis cette interface."
        )
        security_text.setWordWrap(True)
        security_text.setStyleSheet(
            "border: none;"
        )

        security_layout.addWidget(
            security_icon,
            0,
            Qt.AlignTop,
        )
        security_layout.addWidget(
            security_text,
            1,
        )

        content_layout.addWidget(security)

        # espace inférieur
        content_layout.addSpacing(10)

        scroll.setWidget(content)

        main_layout.addWidget(scroll, 1)

        # ----------------------------------------------------
        # BOUTONS TOUJOURS VISIBLES
        # ----------------------------------------------------

        button_line = QFrame()
        button_line.setStyleSheet(
            f"""
            QFrame {{
                background: {WHITE};
                border-top: 1px solid {BORDER};
            }}
            """
        )

        button_layout = QHBoxLayout(button_line)
        button_layout.setContentsMargins(
            0, 12, 0, 0
        )
        button_layout.setSpacing(10)

        button_layout.addStretch()

        cancel_button = QPushButton("Annuler")
        cancel_button.setObjectName("cancelButton")
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setMinimumHeight(42)
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("✓  Enregistrer")
        save_button.setObjectName("saveButton")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setMinimumHeight(42)
        save_button.clicked.connect(self.save)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        main_layout.addWidget(button_line)

        # ----------------------------------------------------
        # FOCUS
        # ----------------------------------------------------

        self.description_input.setFocus()

    # --------------------------------------------------------
    # RÉCUPÉRER LES DONNÉES
    # --------------------------------------------------------

    def get_data(self) -> dict:
        return {
            "description": self.description_input.text().strip(),
            "category": self.category_input.currentText().strip(),
            "amount": float(self.amount_input.value()),
            "expense_date": self.date_input.date().toPython(),
            "payment_method": (
                self.payment_input.currentText().strip()
            ),
            "note": self.note_input.toPlainText().strip(),
            "created_by": (
                self.created_by_input.text().strip()
            ),
        }

    # --------------------------------------------------------
    # ENREGISTRER
    # --------------------------------------------------------

    def save(self):

        data = self.get_data()

        if not data["description"]:
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez saisir la description de la dépense.",
            )
            self.description_input.setFocus()
            return

        if data["amount"] <= 0:
            QMessageBox.warning(
                self,
                "Montant invalide",
                "Le montant doit être supérieur à zéro.",
            )
            self.amount_input.setFocus()
            return

        if not data["created_by"]:
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Veuillez indiquer le nom de la personne "
                "qui saisit la dépense.",
            )
            self.created_by_input.setFocus()
            return

        self.accept()


# ============================================================
# PAGE DÉPENSES
# ============================================================

class ExpensesPage(QWidget):

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)

        self.current_user = current_user

        self.setup_ui()
        self.refresh()

    # --------------------------------------------------------
    # INTERFACE
    # --------------------------------------------------------

    def setup_ui(self):

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: "Segoe UI";
            }}

            QLabel#pageTitle {{
                color: {NAVY};
                font-size: 28px;
                font-weight: 800;
            }}

            QLabel#pageSubtitle {{
                color: {TEXT_MUTED};
                font-size: 13px;
            }}

            QFrame#toolbar {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}

            QLineEdit,
            QComboBox {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 9px 12px;
                color: {TEXT};
                font-size: 13px;
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border: 2px solid {BLUE};
            }}

            QPushButton#addButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 700;
            }}

            QPushButton#addButton:hover {{
                background: #1D4ED8;
            }}

            QPushButton#refreshButton {{
                background: {WHITE};
                color: {NAVY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: 700;
            }}

            QPushButton#refreshButton:hover {{
                background: #F2F4F7;
            }}

            QTableWidget {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
                gridline-color: #F2F4F7;
                font-size: 12px;
                selection-background-color: #EFF6FF;
                selection-color: {TEXT};
            }}

            QHeaderView::section {{
                background: #F9FAFB;
                color: #475467;
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 12px 8px;
                font-size: 12px;
                font-weight: 800;
            }}

            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #F2F4F7;
            }}
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            24, 22, 24, 24
        )
        main_layout.setSpacing(18)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()
        header.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title = QLabel("Dépenses")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Suivez et enregistrez les dépenses de la pharmacie."
        )
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        add_button = QPushButton(
            "＋  Nouvelle dépense"
        )
        add_button.setObjectName("addButton")
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(self.add_expense)

        refresh_button = QPushButton(
            "↻  Actualiser"
        )
        refresh_button.setObjectName("refreshButton")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)

        header.addWidget(refresh_button)
        header.addWidget(add_button)

        main_layout.addLayout(header)

        # ----------------------------------------------------
        # FILTRES
        # ----------------------------------------------------

        toolbar = QFrame()
        toolbar.setObjectName("toolbar")

        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(
            14, 12, 14, 12
        )
        toolbar_layout.setSpacing(10)

        search_label = QLabel("🔎")
        search_label.setStyleSheet(
            "font-size: 18px;"
        )

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher une dépense, catégorie ou personne..."
        )
        self.search_input.setMinimumHeight(40)
        self.search_input.textChanged.connect(
            self.refresh_table
        )

        period_label = QLabel("Période :")
        period_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-weight: 700;"
        )

        self.period_combo = QComboBox()
        self.period_combo.setMinimumHeight(40)
        self.period_combo.addItems(
            [
                "Toutes les dates",
                "Aujourd'hui",
                "7 derniers jours",
                "30 derniers jours",
                "Cette année",
            ]
        )
        self.period_combo.currentIndexChanged.connect(
            self.refresh
        )

        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(
            self.search_input,
            1,
        )
        toolbar_layout.addWidget(period_label)
        toolbar_layout.addWidget(
            self.period_combo
        )

        main_layout.addWidget(toolbar)

        # ----------------------------------------------------
        # KPI
        # ----------------------------------------------------

        stats_layout = QGridLayout()
        stats_layout.setSpacing(12)

        self.total_card = StatCard(
            "Total des dépenses",
            "0 CDF",
            "💰",
            RED,
        )

        self.count_card = StatCard(
            "Nombre de dépenses",
            "0",
            "🧾",
            BLUE,
        )

        self.average_card = StatCard(
            "Dépense moyenne",
            "0 CDF",
            "📊",
            PURPLE,
        )

        stats_layout.addWidget(
            self.total_card,
            0,
            0,
        )

        stats_layout.addWidget(
            self.count_card,
            0,
            1,
        )

        stats_layout.addWidget(
            self.average_card,
            0,
            2,
        )

        for i in range(3):
            stats_layout.setColumnStretch(
                i,
                1,
            )

        main_layout.addLayout(stats_layout)

        # ----------------------------------------------------
        # INFO SÉCURITÉ
        # ----------------------------------------------------

        info = QFrame()
        info.setStyleSheet(
            f"""
            QFrame {{
                background: #F0FDF4;
                border: 1px solid #ABEFC6;
                border-radius: 12px;
            }}
            QLabel {{
                color: #067647;
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )

        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(
            14, 10, 14, 10
        )

        info_icon = QLabel("🔒")
        info_icon.setStyleSheet(
            "font-size: 17px; border: none;"
        )

        info_text = QLabel(
            "Les dépenses enregistrées sont conservées "
            "dans l'historique. Elles ne peuvent pas être "
            "modifiées ou supprimées depuis cette page."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            "border: none;"
        )

        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text, 1)

        main_layout.addWidget(info)

        # ----------------------------------------------------
        # TABLEAU
        # ----------------------------------------------------

        table_frame = QFrame()
        table_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(
            1, 1, 1, 1
        )

        self.table = QTableWidget()
        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "Date",
                "Description",
                "Catégorie",
                "Montant",
                "Paiement",
                "Saisi par",
                "Note",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setAlternatingRowColors(True)

        self.table.setShowGrid(False)

        self.table.verticalHeader().setVisible(False)

        header_view = self.table.horizontalHeader()

        header_view.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header_view.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        header_view.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        header_view.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        header_view.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )

        header_view.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents,
        )

        header_view.setSectionResizeMode(
            6,
            QHeaderView.Stretch,
        )

        table_layout.addWidget(self.table)

        main_layout.addWidget(
            table_frame,
            1,
        )

    # --------------------------------------------------------
    # PÉRIODE
    # --------------------------------------------------------

    def get_period_dates(self):
        today = date.today()

        index = self.period_combo.currentIndex()

        if index == 0:
            return None, None

        if index == 1:
            return today, today

        if index == 2:
            start = today - timedelta(days=6)
            return start, today

        if index == 3:
            start = today - timedelta(days=29)
            return start, today

        if index == 4:
            start = date(today.year, 1, 1)
            return start, today

        return None, None

    # --------------------------------------------------------
    # CHARGEMENT
    # --------------------------------------------------------

    def get_expenses(self):

        session = SessionLocal()

        try:
            query = (
                session.query(Expense)
                .order_by(
                    Expense.expense_date.desc(),
                    Expense.id.desc(),
                )
            )

            start_date, end_date = (
                self.get_period_dates()
            )

            if start_date:
                query = query.filter(
                    Expense.expense_date >= start_date
                )

            if end_date:
                query = query.filter(
                    Expense.expense_date <= end_date
                )

            return query.all()

        finally:
            session.close()

    # --------------------------------------------------------
    # REFRESH GLOBAL
    # --------------------------------------------------------

    def refresh(self):

        try:
            expenses = self.get_expenses()

            self.update_statistics(expenses)
            self.refresh_table(expenses)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger les dépenses.\n\n{e}",
            )

    # --------------------------------------------------------
    # STATISTIQUES
    # --------------------------------------------------------

    def update_statistics(self, expenses):

        total = sum(
            float(exp.amount or 0)
            for exp in expenses
        )

        count = len(expenses)

        average = (
            total / count
            if count > 0
            else 0
        )

        self.total_card.set_value(
            f"{total:,.0f} CDF".replace(
                ",",
                " ",
            )
        )

        self.count_card.set_value(
            str(count)
        )

        self.average_card.set_value(
            f"{average:,.0f} CDF".replace(
                ",",
                " ",
            )
        )

    # --------------------------------------------------------
    # TABLEAU
    # --------------------------------------------------------

    def refresh_table(self, expenses=None):

        if expenses is None:
            try:
                expenses = self.get_expenses()
            except Exception:
                expenses = []

        search = (
            self.search_input.text()
            .strip()
            .lower()
        )

        filtered = []

        for expense in expenses:

            values = [
                str(
                    getattr(
                        expense,
                        "description",
                        "",
                    )
                    or ""
                ),
                str(
                    getattr(
                        expense,
                        "category",
                        "",
                    )
                    or ""
                ),
                str(
                    getattr(
                        expense,
                        "note",
                        "",
                    )
                    or ""
                ),
                str(
                    getattr(
                        expense,
                        "created_by",
                        "",
                    )
                    or ""
                ),
                str(
                    getattr(
                        expense,
                        "payment_method",
                        "",
                    )
                    or ""
                ),
            ]

            if search:
                text = " ".join(values).lower()

                if search not in text:
                    continue

            filtered.append(expense)

        self.table.setRowCount(0)

        for expense in filtered:

            row = self.table.rowCount()
            self.table.insertRow(row)

            expense_date = getattr(
                expense,
                "expense_date",
                None,
            )

            if expense_date:
                date_text = expense_date.strftime(
                    "%d/%m/%Y"
                )
            else:
                date_text = "-"

            description = getattr(
                expense,
                "description",
                "",
            ) or ""

            category = getattr(
                expense,
                "category",
                "Autre",
            ) or "Autre"

            amount = float(
                getattr(
                    expense,
                    "amount",
                    0,
                )
                or 0
            )

            payment = getattr(
                expense,
                "payment_method",
                "",
            ) or ""

            created_by = getattr(
                expense,
                "created_by",
                "",
            ) or ""

            note = getattr(
                expense,
                "note",
                "",
            ) or ""

            values = [
                date_text,
                description,
                category,
                f"{amount:,.0f} CDF".replace(
                    ",",
                    " ",
                ),
                payment,
                created_by,
                note,
            ]

            for column, value in enumerate(values):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setFlags(
                    Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                )

                if column == 3:
                    item.setTextAlignment(
                        Qt.AlignRight
                        | Qt.AlignVCenter
                    )

                    item.setForeground(
                        Qt.red
                    )

                elif column == 0:
                    item.setTextAlignment(
                        Qt.AlignCenter
                        | Qt.AlignVCenter
                    )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

        self.table.resizeRowsToContents()

    # --------------------------------------------------------
    # AJOUT D'UNE DÉPENSE
    # --------------------------------------------------------

    def add_expense(self):

        dialog = ExpenseDialog(
            self,
            self.current_user,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        session = SessionLocal()

        try:

            expense = Expense(
                description=data["description"],
                category=data["category"],
                amount=data["amount"],
                expense_date=data["expense_date"],
                payment_method=data["payment_method"],
                note=data["note"],
                created_by=data["created_by"],
            )

            session.add(expense)
            session.commit()

            QMessageBox.information(
                self,
                "Dépense enregistrée",
                "La dépense a été enregistrée avec succès.",
            )

            self.refresh()

        except Exception as e:

            session.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'enregistrer la dépense.\n\n"
                f"{e}",
            )

        finally:
            session.close()
