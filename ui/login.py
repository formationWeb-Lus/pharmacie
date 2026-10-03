from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QApplication,
    QGraphicsDropShadowEffect,
)

from database.user_database import authenticate_user


class LoginWindow(QWidget):
    """
    Fenêtre professionnelle de connexion de l'application Pharmacie.

    ADMIN  -> admin.dashboard.DashboardPage
    WORKER -> ui.main_window.MainWindow
    """

    def __init__(self):
        super().__init__()

        # ============================================================
        # VARIABLES
        # ============================================================

        self.current_user = None
        self.next_window = None
        self.register_window = None

        # ============================================================
        # FENÊTRE
        # ============================================================

        self.setWindowTitle(
            "Pharmacie • Connexion"
        )

        self.setMinimumSize(
            1000,
            650
        )

        # ============================================================
        # INTERFACE
        # ============================================================

        self.setup_ui()

        # ============================================================
        # OUVRIR EN PLEIN ÉCRAN
        # ============================================================

        self.showMaximized()

    # =================================================================
    # INTERFACE
    # =================================================================

    def setup_ui(self):

        # ============================================================
        # STYLE GLOBAL
        # ============================================================

        self.setStyleSheet(
            """
            /* ======================================================
               FENÊTRE
               ====================================================== */

            LoginWindow {
                background-color: #EAF3F8;
                color: #172B4D;
                font-family: "Segoe UI";
            }

            QWidget {
                font-family: "Segoe UI";
            }

            /* ======================================================
               ZONE GAUCHE
               ====================================================== */

            QFrame#brandPanel {
                background-color: #0B5D66;
                border: none;
            }

            QLabel#brandSmall {
                color: #A7E8E4;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 1px;
            }

            QLabel#brandTitle {
                color: white;
                font-size: 42px;
                font-weight: 800;
            }

            QLabel#brandSubtitle {
                color: #D7F4F2;
                font-size: 17px;
                line-height: 1.5;
            }

            QLabel#featureTitle {
                color: white;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#featureText {
                color: #CBEAE8;
                font-size: 13px;
            }

            QFrame#featureIcon {
                background-color: #147985;
                border: 1px solid #26919A;
                border-radius: 14px;
            }

            QLabel#featureIconLabel {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: bold;
            }

            QFrame#brandLogo {
                background-color: #FFFFFF;
                border-radius: 22px;
            }

            QLabel#brandLogoText {
                color: #0B5D66;
                font-size: 25px;
                font-weight: 900;
            }

            QLabel#brandFooter {
                color: #A7D9D7;
                font-size: 11px;
            }

            /* ======================================================
               ZONE DROITE
               ====================================================== */

            QFrame#loginPanel {
                background-color: #F7FAFC;
                border: none;
            }

            QFrame#loginCard {
                background-color: white;
                border: 1px solid #DCE8EE;
                border-radius: 22px;
            }

            QLabel#loginTitle {
                color: #102A43;
                font-size: 30px;
                font-weight: 800;
            }

            QLabel#loginSubtitle {
                color: #627D98;
                font-size: 14px;
            }

            QLabel#fieldLabel {
                color: #243B53;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#fieldHint {
                color: #829AB1;
                font-size: 11px;
            }

            /* ======================================================
               CHAMPS
               ====================================================== */

            QLineEdit {
                background-color: #F8FBFC;
                color: #102A43;

                border: 1px solid #C7D6DF;
                border-radius: 11px;

                padding: 0px 14px;

                min-height: 50px;

                font-size: 14px;
                font-weight: 500;

                selection-background-color: #0B7A75;
                selection-color: white;
            }

            QLineEdit:hover {
                background-color: #FFFFFF;
                border: 1px solid #8FAFBD;
            }

            QLineEdit:focus {
                background-color: #FFFFFF;
                border: 2px solid #0B7A75;
            }

            /* ======================================================
               CONTENEUR MOT DE PASSE
               ====================================================== */

            QFrame#passwordContainer {
                background-color: transparent;
                border: none;
            }

            /* ======================================================
               BOUTON AFFICHER MOT DE PASSE
               ====================================================== */

            QPushButton#showPasswordButton {
                background-color: #E8F3F3;
                color: #0B5D66;

                border: 1px solid #C9E1E1;
                border-radius: 9px;

                font-size: 17px;
                font-weight: bold;
            }

            QPushButton#showPasswordButton:hover {
                background-color: #D7ECEC;
                border: 1px solid #A8D0D0;
            }

            QPushButton#showPasswordButton:pressed {
                background-color: #C4E0E0;
            }

            /* ======================================================
               BOUTON CONNEXION
               ====================================================== */

            QPushButton#loginButton {
                background-color: #0B7A75;
                color: white;

                border: none;
                border-radius: 11px;

                min-height: 52px;

                padding: 0px 20px;

                font-size: 15px;
                font-weight: 800;
            }

            QPushButton#loginButton:hover {
                background-color: #096863;
            }

            QPushButton#loginButton:pressed {
                background-color: #07534F;
            }

            QPushButton#loginButton:disabled {
                background-color: #9CC9C6;
                color: #EAF6F5;
            }

            /* ======================================================
               INSCRIPTION
               ====================================================== */

            QLabel#registerQuestion {
                color: #829AB1;
                font-size: 12px;
            }

            QPushButton#registerButton {
                background-color: transparent;
                color: #0B7A75;

                border: none;

                font-size: 13px;
                font-weight: 800;

                padding: 5px;
            }

            QPushButton#registerButton:hover {
                color: #07534F;
            }

            /* ======================================================
               SÉCURITÉ
               ====================================================== */

            QFrame#securityBox {
                background-color: #F0F8F7;
                border: 1px solid #D6EBE9;
                border-radius: 10px;
            }

            QLabel#securityText {
                color: #39706C;
                font-size: 11px;
            }

            QLabel#footer {
                color: #9AAFC0;
                font-size: 10px;
            }

            /* ======================================================
               SEPARATEUR
               ====================================================== */

            QFrame#separator {
                background-color: #E2E8F0;
                border: none;
                min-height: 1px;
                max-height: 1px;
            }
            """
        )

        # ============================================================
        # LAYOUT PRINCIPAL
        # ============================================================

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        # ============================================================
        # PANNEAU GAUCHE
        # ============================================================

        brand_panel = QFrame()

        brand_panel.setObjectName(
            "brandPanel"
        )

        brand_panel.setMinimumWidth(
            420
        )

        brand_panel.setMaximumWidth(
            650
        )

        brand_layout = QVBoxLayout(
            brand_panel
        )

        brand_layout.setContentsMargins(
            60,
            55,
            60,
            40
        )

        brand_layout.setSpacing(0)

        # ============================================================
        # LOGO
        # ============================================================

        logo = QFrame()

        logo.setObjectName(
            "brandLogo"
        )

        logo.setFixedSize(
            72,
            72
        )

        logo_layout = QVBoxLayout(logo)

        logo_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        logo_text = QLabel(
            "Rx"
        )

        logo_text.setObjectName(
            "brandLogoText"
        )

        logo_text.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo_layout.addWidget(
            logo_text
        )

        brand_layout.addWidget(
            logo,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        brand_layout.addSpacing(35)

        # ============================================================
        # PETIT TITRE
        # ============================================================

        brand_small = QLabel(
            "GESTION PHARMACEUTIQUE"
        )

        brand_small.setObjectName(
            "brandSmall"
        )

        brand_layout.addWidget(
            brand_small
        )

        brand_layout.addSpacing(12)

        # ============================================================
        # GRAND TITRE
        # ============================================================

        brand_title = QLabel(
            "Votre pharmacie,\n"
            "simplement maîtrisée."
        )

        brand_title.setObjectName(
            "brandTitle"
        )

        brand_title.setWordWrap(True)

        brand_layout.addWidget(
            brand_title
        )

        brand_layout.addSpacing(18)

        # ============================================================
        # DESCRIPTION
        # ============================================================

        brand_subtitle = QLabel(
            "Gérez vos médicaments, vos stocks, "
            "vos ventes et vos dates d'expiration "
            "depuis une seule application."
        )

        brand_subtitle.setObjectName(
            "brandSubtitle"
        )

        brand_subtitle.setWordWrap(True)

        brand_layout.addWidget(
            brand_subtitle
        )

        brand_layout.addSpacing(38)

        # ============================================================
        # FONCTIONNALITÉ 1
        # ============================================================

        self._add_feature(
            brand_layout,
            "📦",
            "Gestion des stocks",
            "Suivez les quantités, conditionnements "
            "et niveaux de stock.",
        )

        brand_layout.addSpacing(18)

        # ============================================================
        # FONCTIONNALITÉ 2
        # ============================================================

        self._add_feature(
            brand_layout,
            "🧾",
            "Gestion des ventes",
            "Enregistrez les ventes et actualisez "
            "automatiquement les stocks.",
        )

        brand_layout.addSpacing(18)

        # ============================================================
        # FONCTIONNALITÉ 3
        # ============================================================

        self._add_feature(
            brand_layout,
            "🔒",
            "Données sécurisées",
            "Vos informations restent stockées "
            "localement sur votre ordinateur.",
        )

        brand_layout.addStretch()

        # ============================================================
        # FOOTER GAUCHE
        # ============================================================

        brand_footer = QLabel(
            "Pharmacie Management System • "
            "Gestion professionnelle"
        )

        brand_footer.setObjectName(
            "brandFooter"
        )

        brand_layout.addWidget(
            brand_footer
        )

        main_layout.addWidget(
            brand_panel,
            4
        )

        # ============================================================
        # PANNEAU DROIT
        # ============================================================

        login_panel = QFrame()

        login_panel.setObjectName(
            "loginPanel"
        )

        login_layout = QVBoxLayout(
            login_panel
        )

        login_layout.setContentsMargins(
            45,
            40,
            45,
            40
        )

        login_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ============================================================
        # CARTE CONNEXION
        # ============================================================

        card = QFrame()

        card.setObjectName(
            "loginCard"
        )

        card.setMaximumWidth(
            540
        )

        card.setMinimumWidth(
            440
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        # ============================================================
        # OMBRE
        # ============================================================

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(
            35
        )

        shadow.setOffset(
            0,
            10
        )

        shadow.setColor(
            Qt.GlobalColor.black
        )

        card.setGraphicsEffect(
            shadow
        )

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(
            50,
            45,
            50,
            42
        )

        card_layout.setSpacing(
            10
        )

        # ============================================================
        # TITRE
        # ============================================================

        login_title = QLabel(
            "Bienvenue"
        )

        login_title.setObjectName(
            "loginTitle"
        )

        card_layout.addWidget(
            login_title
        )

        # ============================================================
        # SOUS-TITRE
        # ============================================================

        login_subtitle = QLabel(
            "Connectez-vous à votre espace professionnel."
        )

        login_subtitle.setObjectName(
            "loginSubtitle"
        )

        login_subtitle.setWordWrap(True)

        card_layout.addWidget(
            login_subtitle
        )

        card_layout.addSpacing(
            25
        )

        # ============================================================
        # NUMÉRO DE TÉLÉPHONE
        # ============================================================

        phone_label = QLabel(
            "Numéro de téléphone"
        )

        phone_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            phone_label
        )

        self.phone_input = QLineEdit()

        self.phone_input.setPlaceholderText(
            "Exemple : 099 999 99 99"
        )

        self.phone_input.setMaxLength(
            30
        )

        self.phone_input.setClearButtonEnabled(
            True
        )

        card_layout.addWidget(
            self.phone_input
        )

        phone_hint = QLabel(
            "Utilisez le numéro associé à votre compte."
        )

        phone_hint.setObjectName(
            "fieldHint"
        )

        card_layout.addWidget(
            phone_hint
        )

        card_layout.addSpacing(
            15
        )

        # ============================================================
        # MOT DE PASSE
        # ============================================================

        password_label = QLabel(
            "Mot de passe"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            password_label
        )

        # ============================================================
        # CONTENEUR MOT DE PASSE
        # ============================================================

        password_container = QFrame()

        password_container.setObjectName(
            "passwordContainer"
        )

        password_layout = QHBoxLayout(
            password_container
        )

        password_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        password_layout.setSpacing(
            8
        )

        # ============================================================
        # CHAMP MOT DE PASSE
        # ============================================================

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Entrez votre mot de passe"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_input.setMaxLength(
            100
        )

        self.password_input.setClearButtonEnabled(
            True
        )

        password_layout.addWidget(
            self.password_input
        )

        # ============================================================
        # BOUTON AFFICHER
        # ============================================================

        self.show_password_button = QPushButton(
            "👁"
        )

        self.show_password_button.setObjectName(
            "showPasswordButton"
        )

        self.show_password_button.setFixedSize(
            50,
            50
        )

        self.show_password_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.show_password_button.setToolTip(
            "Afficher le mot de passe"
        )

        self.show_password_button.clicked.connect(
            self.toggle_password
        )

        password_layout.addWidget(
            self.show_password_button
        )

        card_layout.addWidget(
            password_container
        )

        card_layout.addSpacing(
            25
        )

        # ============================================================
        # BOUTON CONNEXION
        # ============================================================

        self.login_button = QPushButton(
            "SE CONNECTER   →"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.login_button.setMinimumHeight(
            52
        )

        self.login_button.clicked.connect(
            self.handle_login
        )

        card_layout.addWidget(
            self.login_button
        )

        # ============================================================
        # ENTER = CONNEXION
        # ============================================================

        self.phone_input.returnPressed.connect(
            self.handle_login
        )

        self.password_input.returnPressed.connect(
            self.handle_login
        )

        card_layout.addSpacing(
            18
        )

        # ============================================================
        # SEPARATEUR
        # ============================================================

        separator = QFrame()

        separator.setObjectName(
            "separator"
        )

        card_layout.addWidget(
            separator
        )

        card_layout.addSpacing(
            14
        )

        # ============================================================
        # INSCRIPTION
        # ============================================================

        register_layout = QHBoxLayout()

        register_layout.setSpacing(
            2
        )

        register_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        register_question = QLabel(
            "Vous n'avez pas encore de compte ?"
        )

        register_question.setObjectName(
            "registerQuestion"
        )

        self.register_button = QPushButton(
            "Créer un compte"
        )

        self.register_button.setObjectName(
            "registerButton"
        )

        self.register_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.register_button.clicked.connect(
            self.open_register
        )

        register_layout.addWidget(
            register_question
        )

        register_layout.addWidget(
            self.register_button
        )

        card_layout.addLayout(
            register_layout
        )

        card_layout.addSpacing(
            18
        )

        # ============================================================
        # SÉCURITÉ
        # ============================================================

        security_box = QFrame()

        security_box.setObjectName(
            "securityBox"
        )

        security_layout = QHBoxLayout(
            security_box
        )

        security_layout.setContentsMargins(
            12,
            9,
            12,
            9
        )

        security_text = QLabel(
            "🔒  Vos données sont stockées "
            "localement et restent protégées."
        )

        security_text.setObjectName(
            "securityText"
        )

        security_text.setWordWrap(
            True
        )

        security_layout.addWidget(
            security_text
        )

        card_layout.addWidget(
            security_box
        )

        card_layout.addSpacing(
            15
        )

        # ============================================================
        # FOOTER
        # ============================================================

        footer = QLabel(
            "Application locale • Fonctionne hors ligne"
        )

        footer.setObjectName(
            "footer"
        )

        footer.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        card_layout.addWidget(
            footer
        )

        # ============================================================
        # AJOUT CARTE
        # ============================================================

        login_layout.addWidget(
            card
        )

        main_layout.addWidget(
            login_panel,
            6
        )

        # ============================================================
        # FOCUS
        # ============================================================

        self.phone_input.setFocus()

    # =================================================================
    # AJOUT FONCTIONNALITÉ PANNEAU GAUCHE
    # =================================================================

    def _add_feature(
        self,
        parent_layout,
        icon,
        title,
        description,
    ):

        feature_layout = QHBoxLayout()

        feature_layout.setSpacing(
            15
        )

        # ------------------------------------------------------------
        # Icône
        # ------------------------------------------------------------

        icon_frame = QFrame()

        icon_frame.setObjectName(
            "featureIcon"
        )

        icon_frame.setFixedSize(
            50,
            50
        )

        icon_layout = QVBoxLayout(
            icon_frame
        )

        icon_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setObjectName(
            "featureIconLabel"
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_layout.addWidget(
            icon_label
        )

        feature_layout.addWidget(
            icon_frame
        )

        # ------------------------------------------------------------
        # Texte
        # ------------------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "featureTitle"
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "featureText"
        )

        description_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            description_label
        )

        feature_layout.addLayout(
            text_layout,
            1
        )

        parent_layout.addLayout(
            feature_layout
        )

    # =================================================================
    # AFFICHER / MASQUER MOT DE PASSE
    # =================================================================

    def toggle_password(self):

        if (
            self.password_input.echoMode()
            == QLineEdit.EchoMode.Password
        ):

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal
            )

            self.show_password_button.setText(
                "🙈"
            )

            self.show_password_button.setToolTip(
                "Masquer le mot de passe"
            )

        else:

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

            self.show_password_button.setText(
                "👁"
            )

            self.show_password_button.setToolTip(
                "Afficher le mot de passe"
            )

    # =================================================================
    # CONNEXION
    # =================================================================

    def handle_login(self):

        phone = self.phone_input.text().strip()

        password = self.password_input.text()

        # ============================================================
        # TÉLÉPHONE
        # ============================================================

        if not phone:

            QMessageBox.warning(
                self,
                "Connexion",
                "Veuillez saisir votre numéro de téléphone."
            )

            self.phone_input.setFocus()

            return

        # ============================================================
        # MOT DE PASSE
        # ============================================================

        if not password:

            QMessageBox.warning(
                self,
                "Connexion",
                "Veuillez saisir votre mot de passe."
            )

            self.password_input.setFocus()

            return

        # ============================================================
        # BOUTON
        # ============================================================

        self.login_button.setEnabled(
            False
        )

        self.login_button.setText(
            "CONNEXION EN COURS..."
        )

        QApplication.processEvents()

        # ============================================================
        # AUTHENTIFICATION
        # ============================================================

        try:

            user = authenticate_user(
                phone,
                password
            )

        except Exception as error:

            self.login_button.setEnabled(
                True
            )

            self.login_button.setText(
                "SE CONNECTER   →"
            )

            QMessageBox.critical(
                self,
                "Erreur de connexion",
                (
                    "Une erreur est survenue "
                    "pendant la connexion.\n\n"
                    f"Détails : {error}"
                )
            )

            return

        # ============================================================
        # RÉACTIVER
        # ============================================================

        self.login_button.setEnabled(
            True
        )

        self.login_button.setText(
            "SE CONNECTER   →"
        )

        # ============================================================
        # REFUS
        # ============================================================

        if user is None:

            QMessageBox.warning(
                self,
                "Connexion refusée",
                (
                    "Numéro de téléphone ou "
                    "mot de passe incorrect."
                )
            )

            self.password_input.clear()

            self.password_input.setFocus()

            return

        # ============================================================
        # UTILISATEUR
        # ============================================================

        self.current_user = user

        self.open_user_interface()

    # =================================================================
    # REDIRECTION
    # =================================================================

    def open_user_interface(self):

        if self.current_user is None:
            return

        role = str(
            getattr(
                self.current_user,
                "role",
                "USER"
            )
        ).upper().strip()

        print()
        print("=" * 60)
        print("UTILISATEUR CONNECTÉ")
        print("=" * 60)

        print(
            "Nom        :",
            getattr(
                self.current_user,
                "full_name",
                "-"
            )
        )

        print(
            "Téléphone  :",
            getattr(
                self.current_user,
                "phone",
                "-"
            )
        )

        print(
            "Rôle       :",
            role
        )

        print("=" * 60)

        try:

            # ========================================================
            # ADMIN
            # ========================================================

            if role == "ADMIN":

                print(
                    "→ Ouverture du dashboard ADMIN"
                )

                from admin.dashboard import DashboardPage

                self.next_window = DashboardPage(
                    self.current_user
                )

            # ========================================================
            # WORKER
            # ========================================================

            elif role == "WORKER":

                print(
                    "→ Ouverture de l'espace WORKER"
                )

                from ui.main_window import MainWindow

                self.next_window = MainWindow(
                    self.current_user
                )

            # ========================================================
            # RÔLE INCONNU
            # ========================================================

            else:

                print(
                    "❌ Rôle inconnu :",
                    role
                )

                QMessageBox.warning(
                    self,
                    "Rôle inconnu",
                    (
                        "Votre compte possède un rôle "
                        f"non reconnu : {role}\n\n"
                        "Veuillez contacter l'administrateur."
                    )
                )

                return

            # ========================================================
            # OUVERTURE
            # ========================================================

            self.next_window.showMaximized()

            self.close()

        except Exception as error:

            print()
            print("=" * 60)
            print("❌ ERREUR OUVERTURE INTERFACE")
            print("=" * 60)

            print(
                "Rôle   :",
                role
            )

            print(
                "Erreur :",
                error
            )

            print("=" * 60)
            print()

            QMessageBox.critical(
                self,
                "Erreur d'ouverture",
                (
                    "Impossible d'ouvrir "
                    "l'espace utilisateur.\n\n"
                    f"Rôle détecté : {role}\n\n"
                    f"Détails : {error}"
                )
            )

    # =================================================================
    # INSCRIPTION
    # =================================================================

    def open_register(self):

        try:

            from ui.register import RegisterWindow

            self.register_window = RegisterWindow()

            self.register_window.showMaximized()

            self.hide()

            self.register_window.destroyed.connect(
                self.show
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Impossible d'ouvrir "
                    "la page d'inscription.\n\n"
                    f"Détails : {error}"
                )
            )

            self.showMaximized()


# ====================================================================
# LANCEMENT DIRECT
# ====================================================================

if __name__ == "__main__":

    import sys

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Pharmacie"
    )

    window = LoginWindow()

    window.showMaximized()

    sys.exit(
        app.exec()
    )