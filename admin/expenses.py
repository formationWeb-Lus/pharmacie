
from __future__ import annotations

from datetime import date, datetime

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
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QDoubleSpinBox,
    QSizePolicy,
    QScrollArea,
    QAbstractItemView,
)

from sqlalchemy import func

from database.database import SessionLocal
from database.models import Expense


# ============================================================
# CONSTANTES
# ============================================================

EXPENSE_CATEGORIES = [
    "Nourriture",
    "Transport",
    "Fournitures",
    "Loyer",
    "Électricité",
    "Eau",
    "Téléphone / Internet",
    "Entretien",
    "Salaires",
    "Autre",
]

PAYMENT_METHODS = [
    "Espèces",
    "Mobile Money",
    "Carte bancaire",
    "Virement",
]


# ============================================================
# UTILITAIRES
# ============================================================

def get_current_user_name(current_user) -> str:
    """
    Récupère proprement le nom de l'utilisateur connecté.

    Accepte :
    - dictionnaire
    - objet SQLAlchemy
    - simple chaîne
    """

    if current_user is None:
        return ""

    if isinstance(current_user, str):
        return current_user

    if isinstance(current_user, dict):
        for key in (
            "name",
            "full_name",
            "username",
            "email",
            "first_name",
        ):
            value = current_user.get(key)
            if value:
                return str(value)

        return ""

    for attribute in (
        "name",
        "full_name",
        "username",
        "email",
        "first_name",
    ):
        value = getattr(current_user, attribute, None)

        if value:
            return str(value)

    return ""


def format_money(value) -> str:
    """
    Formate un montant en CDF.
    """

    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0

    return f"{amount:,.0f} CDF".replace(",", " ")


# ============================================================
# DIALOGUE AJOUT / MODIFICATION
# ============================================================

class ExpenseDialog(QDialog):
    """
    Formulaire d'ajout/modification d'une dépense.
    """

    def __init__(
        self,
        parent=None,
        expense: Expense | None = None,
        current_user=None,
    ):
        super().__init__(parent)

        self.expense = expense
        self.current_user = current_user

        self.setWindowTitle(
            "Modifier la dépense"
            if expense
            else "Nouvelle dépense"
        )

        self.setMinimumWidth(520)

        self.build_ui()

        if expense:
            self.load_expense(expense)

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(18)

        title = QLabel(
            "Modifier une dépense"
            if self.expense
            else "Enregistrer une dépense"
        )

        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(
            """
            QLabel {
                color: #08192d;
            }
            """
        )

        layout.addWidget(title)

        subtitle = QLabel(
            "Saisissez les informations de la dépense."
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #64748b;
                font-size: 13px;
            }
            """
        )

        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            "Exemple : Achat de nourriture"
        )

        form.addRow(
            "Dépense *",
            self.description_input,
        )

        # ----------------------------------------------------
        # CATEGORIE
        # ----------------------------------------------------

        self.category_combo = QComboBox()
        self.category_combo.addItems(EXPENSE_CATEGORIES)

        form.addRow(
            "Catégorie *",
            self.category_combo,
        )

        # ----------------------------------------------------
        # MONTANT
        # ----------------------------------------------------

        self.amount_input = QDoubleSpinBox()

        self.amount_input.setRange(
            0,
            999_999_999_999,
        )

        self.amount_input.setDecimals(0)
        self.amount_input.setSingleStep(500)

        self.amount_input.setSuffix(" CDF")

        form.addRow(
            "Montant *",
            self.amount_input,
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        self.date_input = QDateEdit()

        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")

        form.addRow(
            "Date *",
            self.date_input,
        )

        # ----------------------------------------------------
        # PAIEMENT
        # ----------------------------------------------------

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(PAYMENT_METHODS)

        form.addRow(
            "Mode de paiement",
            self.payment_combo,
        )

        # ----------------------------------------------------
        # NOTE
        # ----------------------------------------------------

        self.note_input = QTextEdit()

        self.note_input.setPlaceholderText(
            "Informations complémentaires..."
        )

        self.note_input.setMaximumHeight(100)

        form.addRow(
            "Note",
            self.note_input,
        )

        layout.addLayout(form)

        # ----------------------------------------------------
        # BOUTONS
        # ----------------------------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        buttons.button(
            QDialogButtonBox.Save
        ).setText("Enregistrer")

        buttons.button(
            QDialogButtonBox.Cancel
        ).setText("Annuler")

        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog {
                background: white;
            }

            QLineEdit,
            QComboBox,
            QDateEdit,
            QDoubleSpinBox,
            QTextEdit {
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 8px;
                background: white;
                min-height: 20px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QDoubleSpinBox:focus,
            QTextEdit:focus {
                border: 2px solid #facc15;
            }

            QPushButton {
                padding: 9px 18px;
                border-radius: 7px;
            }
            """
        )

    # --------------------------------------------------------
    # CHARGER
    # --------------------------------------------------------

    def load_expense(self, expense: Expense):

        self.description_input.setText(
            expense.description or ""
        )

        category_index = self.category_combo.findText(
            expense.category or "Autre"
        )

        if category_index >= 0:
            self.category_combo.setCurrentIndex(
                category_index
            )

        self.amount_input.setValue(
            float(expense.amount or 0)
        )

        if expense.expense_date:

            if isinstance(expense.expense_date, datetime):
                expense_date = expense.expense_date.date()
            else:
                expense_date = expense.expense_date

            self.date_input.setDate(
                QDate(
                    expense_date.year,
                    expense_date.month,
                    expense_date.day,
                )
            )

        payment_index = self.payment_combo.findText(
            expense.payment_method or "Espèces"
        )

        if payment_index >= 0:
            self.payment_combo.setCurrentIndex(
                payment_index
            )

        self.note_input.setPlainText(
            expense.note or ""
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate_and_accept(self):

        description = (
            self.description_input
            .text()
            .strip()
        )

        amount = float(
            self.amount_input.value()
        )

        if not description:
            QMessageBox.warning(
                self,
                "Information manquante",
                "Veuillez saisir la description de la dépense.",
            )
            self.description_input.setFocus()
            return

        if amount <= 0:
            QMessageBox.warning(
                self,
                "Montant invalide",
                "Le montant doit être supérieur à 0 CDF.",
            )
            self.amount_input.setFocus()
            return

        self.accept()

    # --------------------------------------------------------
    # DONNEES
    # --------------------------------------------------------

    def get_data(self):

        qdate = self.date_input.date()

        expense_date = date(
            qdate.year(),
            qdate.month(),
            qdate.day(),
        )

        return {
            "description": (
                self.description_input
                .text()
                .strip()
            ),
            "category": (
                self.category_combo
                .currentText()
            ),
            "amount": float(
                self.amount_input.value()
            ),
            "expense_date": expense_date,
            "payment_method": (
                self.payment_combo
                .currentText()
            ),
            "note": (
                self.note_input
                .toPlainText()
                .strip()
            ),
        }


# ============================================================
# PAGE DEPENSES
# ============================================================

class ExpensesPage(QWidget):

    def __init__(
        self,
        parent=None,
        current_user=None,
    ):
        super().__init__(parent)

        self.current_user = current_user

        self.build_ui()
        self.load_statistics()
        self.load_expenses()

    # ========================================================
    # INTERFACE
    # ========================================================

    def build_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(18)

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(
            0,
            0,
            0,
            20,
        )

        content_layout.setSpacing(18)

        # ====================================================
        # HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel("Gestion des dépenses")

        title.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Bold,
            )
        )

        title.setStyleSheet(
            "color: #08192d;"
        )

        title_layout.addWidget(title)

        subtitle = QLabel(
            "Enregistrez et suivez les dépenses de la pharmacie."
        )

        subtitle.setStyleSheet(
            """
            color: #64748b;
            font-size: 13px;
            """
        )

        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        add_button = QPushButton(
            "+ Nouvelle dépense"
        )

        add_button.setMinimumHeight(42)

        add_button.setCursor(Qt.PointingHandCursor)

        add_button.setStyleSheet(
            """
            QPushButton {
                background: #facc15;
                color: #08192d;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }

            QPushButton:hover {
                background: #eab308;
            }
            """
        )

        add_button.clicked.connect(
            self.add_expense
        )

        header_layout.addWidget(add_button)

        content_layout.addLayout(header_layout)

        # ====================================================
        # KPI
        # ====================================================

        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        self.today_card = self.create_stat_card(
            "Dépenses aujourd'hui",
            "0 CDF",
            "📅",
        )

        self.month_card = self.create_stat_card(
            "Dépenses du mois",
            "0 CDF",
            "📊",
        )

        self.count_card = self.create_stat_card(
            "Nombre de dépenses",
            "0",
            "🧾",
        )

        cards_layout.addWidget(
            self.today_card,
            0,
            0,
        )

        cards_layout.addWidget(
            self.month_card,
            0,
            1,
        )

        cards_layout.addWidget(
            self.count_card,
            0,
            2,
        )

        content_layout.addLayout(cards_layout)

        # ====================================================
        # FILTRES
        # ====================================================

        filter_frame = QFrame()

        filter_frame.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            """
        )

        filter_layout = QGridLayout(
            filter_frame
        )

        filter_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        filter_layout.setHorizontalSpacing(12)
        filter_layout.setVerticalSpacing(10)

        # Recherche

        filter_layout.addWidget(
            QLabel("Recherche"),
            0,
            0,
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Rechercher une dépense..."
        )

        self.search_input.textChanged.connect(
            self.load_expenses
        )

        filter_layout.addWidget(
            self.search_input,
            1,
            0,
        )

        # Catégorie

        filter_layout.addWidget(
            QLabel("Catégorie"),
            0,
            1,
        )

        self.category_filter = QComboBox()

        self.category_filter.addItem(
            "Toutes les catégories"
        )

        self.category_filter.addItems(
            EXPENSE_CATEGORIES
        )

        self.category_filter.currentIndexChanged.connect(
            self.load_expenses
        )

        filter_layout.addWidget(
            self.category_filter,
            1,
            1,
        )

        # Date début

        filter_layout.addWidget(
            QLabel("Du"),
            0,
            2,
        )

        self.start_date = QDateEdit()

        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        # Début du mois courant

        today = date.today()

        self.start_date.setDate(
            QDate(
                today.year,
                today.month,
                1,
            )
        )

        self.start_date.dateChanged.connect(
            self.load_expenses
        )

        filter_layout.addWidget(
            self.start_date,
            1,
            2,
        )

        # Date fin

        filter_layout.addWidget(
            QLabel("Au"),
            0,
            3,
        )

        self.end_date = QDateEdit()

        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.end_date.setDate(
            QDate.currentDate()
        )

        self.end_date.dateChanged.connect(
            self.load_expenses
        )

        filter_layout.addWidget(
            self.end_date,
            1,
            3,
        )

        # Bouton reset

        reset_button = QPushButton(
            "Réinitialiser"
        )

        reset_button.setCursor(
            Qt.PointingHandCursor
        )

        reset_button.clicked.connect(
            self.reset_filters
        )

        filter_layout.addWidget(
            reset_button,
            1,
            4,
        )

        content_layout.addWidget(
            filter_frame
        )

        # ====================================================
        # TABLE
        # ====================================================

        table_frame = QFrame()

        table_frame.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            """
        )

        table_layout = QVBoxLayout(
            table_frame
        )

        table_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        table_title = QLabel(
            "Liste des dépenses"
        )

        table_title.setFont(
            QFont(
                "Segoe UI",
                16,
                QFont.Bold,
            )
        )

        table_title.setStyleSheet(
            "color: #08192d;"
        )

        table_layout.addWidget(
            table_title
        )

        self.table = QTableWidget()

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels(
            [
                "Date",
                "Dépense",
                "Catégorie",
                "Montant",
                "Paiement",
                "Saisi par",
                "Note",
                "Modifier",
                "Supprimer",
            ]
        )

        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.Stretch,
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeToContents,
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeToContents,
        )

        self.table.setMinimumHeight(450)

        table_layout.addWidget(
            self.table
        )

        content_layout.addWidget(
            table_frame
        )

        content_layout.addStretch()

        scroll.setWidget(content)

        main_layout.addWidget(scroll)

        # ====================================================
        # STYLE GENERAL
        # ====================================================

        self.setStyleSheet(
            """
            QWidget {
                font-family: "Segoe UI";
            }

            QLineEdit,
            QComboBox,
            QDateEdit {
                min-height: 34px;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 5px 9px;
                background: white;
                color: #0f172a;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {
                border: 2px solid #facc15;
            }

            QTableWidget {
                border: none;
                gridline-color: #e2e8f0;
                background: white;
                alternate-background-color: #f8fafc;
                selection-background-color: #fef3c7;
                selection-color: #08192d;
            }

            QHeaderView::section {
                background: #08192d;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }

            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 7px 12px;
            }
            """
        )

    # ========================================================
    # CARTE STATISTIQUE
    # ========================================================

    def create_stat_card(
        self,
        title: str,
        value: str,
        icon: str,
    ):

        frame = QFrame()

        frame.setMinimumHeight(105)

        frame.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            """
        )

        layout = QHBoxLayout(frame)

        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )

        icon_label = QLabel(icon)

        icon_label.setFont(
            QFont(
                "Segoe UI Emoji",
                24,
            )
        )

        layout.addWidget(
            icon_label
        )

        text_layout = QVBoxLayout()

        title_label = QLabel(title)

        title_label.setStyleSheet(
            """
            color: #64748b;
            font-size: 12px;
            """
        )

        value_label = QLabel(value)

        value_label.setFont(
            QFont(
                "Segoe UI",
                17,
                QFont.Bold,
            )
        )

        value_label.setStyleSheet(
            "color: #08192d;"
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            value_label
        )

        layout.addLayout(
            text_layout
        )

        layout.addStretch()

        frame.value_label = value_label

        return frame

    # ========================================================
    # STATISTIQUES
    # ========================================================

    def load_statistics(self):

        db = SessionLocal()

        try:

            today = date.today()

            today_total = (
                db.query(
                    func.coalesce(
                        func.sum(
                            Expense.amount
                        ),
                        0,
                    )
                )
                .filter(
                    Expense.expense_date == today
                )
                .scalar()
                or 0
            )

            month_total = (
                db.query(
                    func.coalesce(
                        func.sum(
                            Expense.amount
                        ),
                        0,
                    )
                )
                .filter(
                    Expense.expense_date >= date(
                        today.year,
                        today.month,
                        1,
                    )
                )
                .filter(
                    Expense.expense_date <= today
                )
                .scalar()
                or 0
            )

            count = (
                db.query(
                    func.count(
                        Expense.id
                    )
                )
                .scalar()
                or 0
            )

            self.today_card.value_label.setText(
                format_money(today_total)
            )

            self.month_card.value_label.setText(
                format_money(month_total)
            )

            self.count_card.value_label.setText(
                str(count)
            )

        except Exception as error:

            print(
                f"Erreur statistiques dépenses : {error}"
            )

            self.today_card.value_label.setText(
                "0 CDF"
            )

            self.month_card.value_label.setText(
                "0 CDF"
            )

            self.count_card.value_label.setText(
                "0"
            )

        finally:

            db.close()

    # ========================================================
    # CHARGER LES DEPENSES
    # ========================================================

    def load_expenses(self):

        db = SessionLocal()

        try:

            query = db.query(
                Expense
            )

            # ------------------------------------------------
            # RECHERCHE
            # ------------------------------------------------

            search = (
                self.search_input
                .text()
                .strip()
            )

            if search:

                pattern = f"%{search}%"

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

            # ------------------------------------------------
            # CATEGORIE
            # ------------------------------------------------

            category = (
                self.category_filter
                .currentText()
            )

            if category != "Toutes les catégories":

                query = query.filter(
                    Expense.category == category
                )

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            start_qdate = (
                self.start_date.date()
            )

            end_qdate = (
                self.end_date.date()
            )

            start_date = date(
                start_qdate.year(),
                start_qdate.month(),
                start_qdate.day(),
            )

            end_date = date(
                end_qdate.year(),
                end_qdate.month(),
                end_qdate.day(),
            )

            if start_date > end_date:

                self.table.setRowCount(0)
                return

            query = query.filter(
                Expense.expense_date >= start_date
            )

            query = query.filter(
                Expense.expense_date <= end_date
            )

            # ------------------------------------------------
            # RESULTATS
            # ------------------------------------------------

            expenses = (
                query
                .order_by(
                    Expense.expense_date.desc(),
                    Expense.id.desc(),
                )
                .all()
            )

            self.table.setRowCount(
                len(expenses)
            )

            # ------------------------------------------------
            # REMPLISSAGE
            # ------------------------------------------------

            for row, expense in enumerate(
                expenses
            ):

                # Date

                expense_date = expense.expense_date

                if isinstance(
                    expense_date,
                    datetime,
                ):
                    expense_date = (
                        expense_date.date()
                    )

                date_item = QTableWidgetItem(
                    expense_date.strftime(
                        "%d/%m/%Y"
                    )
                    if expense_date
                    else ""
                )

                # Description

                description_item = (
                    QTableWidgetItem(
                        expense.description or ""
                    )
                )

                # Catégorie

                category_item = (
                    QTableWidgetItem(
                        expense.category or "Autre"
                    )
                )

                # Montant

                amount_item = QTableWidgetItem(
                    format_money(
                        expense.amount
                    )
                )

                amount_item.setTextAlignment(
                    Qt.AlignRight
                    | Qt.AlignVCenter
                )

                # Paiement

                payment_item = (
                    QTableWidgetItem(
                        expense.payment_method
                        or "Espèces"
                    )
                )

                # Utilisateur

                user_item = QTableWidgetItem(
                    expense.created_by or "-"
                )

                # Note

                note_item = QTableWidgetItem(
                    expense.note or ""
                )

                self.table.setItem(
                    row,
                    0,
                    date_item,
                )

                self.table.setItem(
                    row,
                    1,
                    description_item,
                )

                self.table.setItem(
                    row,
                    2,
                    category_item,
                )

                self.table.setItem(
                    row,
                    3,
                    amount_item,
                )

                self.table.setItem(
                    row,
                    4,
                    payment_item,
                )

                self.table.setItem(
                    row,
                    5,
                    user_item,
                )

                self.table.setItem(
                    row,
                    6,
                    note_item,
                )

                # ------------------------------------------------
                # MODIFIER
                # ------------------------------------------------

                edit_button = QPushButton(
                    "Modifier"
                )

                edit_button.setCursor(
                    Qt.PointingHandCursor
                )

                edit_button.setStyleSheet(
                    """
                    QPushButton {
                        background: #e0f2fe;
                        color: #0369a1;
                    }

                    QPushButton:hover {
                        background: #bae6fd;
                    }
                    """
                )

                edit_button.clicked.connect(
                    lambda checked=False,
                    expense_id=expense.id:
                    self.edit_expense(
                        expense_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    7,
                    edit_button,
                )

                # ------------------------------------------------
                # SUPPRIMER
                # ------------------------------------------------

                delete_button = QPushButton(
                    "Supprimer"
                )

                delete_button.setCursor(
                    Qt.PointingHandCursor
                )

                delete_button.setStyleSheet(
                    """
                    QPushButton {
                        background: #fee2e2;
                        color: #b91c1c;
                    }

                    QPushButton:hover {
                        background: #fecaca;
                    }
                    """
                )

                delete_button.clicked.connect(
                    lambda checked=False,
                    expense_id=expense.id:
                    self.delete_expense(
                        expense_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    8,
                    delete_button,
                )

                self.table.setRowHeight(
                    row,
                    48,
                )

        except Exception as error:

            print(
                f"Erreur chargement dépenses : {error}"
            )

        finally:

            db.close()

    # ========================================================
    # AJOUTER
    # ========================================================

    def add_expense(self):

        dialog = ExpenseDialog(
            self,
            current_user=self.current_user,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        data = dialog.get_data()

        db = SessionLocal()

        try:

            user_name = get_current_user_name(
                self.current_user
            )

            expense = Expense(
                description=data[
                    "description"
                ],
                category=data[
                    "category"
                ],
                amount=data[
                    "amount"
                ],
                expense_date=data[
                    "expense_date"
                ],
                payment_method=data[
                    "payment_method"
                ],
                note=data[
                    "note"
                ],
                created_by=user_name,
            )

            db.add(expense)
            db.commit()

            QMessageBox.information(
                self,
                "Dépense enregistrée",
                "La dépense a été enregistrée avec succès.",
            )

            self.load_statistics()
            self.load_expenses()

        except Exception as error:

            db.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible d'enregistrer la dépense.\n\n"
                    f"{error}"
                ),
            )

        finally:

            db.close()

    # ========================================================
    # MODIFIER
    # ========================================================

    def edit_expense(
        self,
        expense_id: int,
    ):

        db = SessionLocal()

        try:

            expense = (
                db.query(Expense)
                .filter(
                    Expense.id == expense_id
                )
                .first()
            )

            if not expense:

                QMessageBox.warning(
                    self,
                    "Dépense introuvable",
                    "Cette dépense n'existe plus.",
                )

                return

            dialog = ExpenseDialog(
                self,
                expense=expense,
                current_user=self.current_user,
            )

            if dialog.exec() != QDialog.Accepted:
                return

            data = dialog.get_data()

            expense.description = data[
                "description"
            ]

            expense.category = data[
                "category"
            ]

            expense.amount = data[
                "amount"
            ]

            expense.expense_date = data[
                "expense_date"
            ]

            expense.payment_method = data[
                "payment_method"
            ]

            expense.note = data[
                "note"
            ]

            db.commit()

            QMessageBox.information(
                self,
                "Dépense modifiée",
                "La dépense a été modifiée avec succès.",
            )

            self.load_statistics()
            self.load_expenses()

        except Exception as error:

            db.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de modifier la dépense.\n\n"
                    f"{error}"
                ),
            )

        finally:

            db.close()

    # ========================================================
    # SUPPRIMER
    # ========================================================

    def delete_expense(
        self,
        expense_id: int,
    ):

        db = SessionLocal()

        try:

            expense = (
                db.query(Expense)
                .filter(
                    Expense.id == expense_id
                )
                .first()
            )

            if not expense:

                QMessageBox.warning(
                    self,
                    "Dépense introuvable",
                    "Cette dépense n'existe plus.",
                )

                return

            confirmation = QMessageBox.question(
                self,
                "Confirmer la suppression",
                (
                    "Voulez-vous vraiment supprimer cette dépense ?\n\n"
                    f"Dépense : {expense.description}\n"
                    f"Montant : {format_money(expense.amount)}"
                ),
                QMessageBox.Yes
                | QMessageBox.No,
                QMessageBox.No,
            )

            if confirmation != QMessageBox.Yes:
                return

            db.delete(expense)
            db.commit()

            QMessageBox.information(
                self,
                "Dépense supprimée",
                "La dépense a été supprimée.",
            )

            self.load_statistics()
            self.load_expenses()

        except Exception as error:

            db.rollback()

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible de supprimer la dépense.\n\n"
                    f"{error}"
                ),
            )

        finally:

            db.close()

    # ========================================================
    # RESET FILTRES
    # ========================================================

    def reset_filters(self):

        today = date.today()

        self.search_input.clear()

        self.category_filter.setCurrentIndex(
            0
        )

        self.start_date.setDate(
            QDate(
                today.year,
                today.month,
                1,
            )
        )

        self.end_date.setDate(
            QDate.currentDate()
        )

        self.load_expenses()
