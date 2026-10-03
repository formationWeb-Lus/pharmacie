from __future__ import annotations

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
    QGraphicsDropShadowEffect,
)

from database.user_database import create_user


class RegisterWindow(QWidget):
    """
    Fenêtre professionnelle d'inscription.

    Les nouveaux comptes sont créés avec le rôle WORKER.
    Le rôle ADMIN est géré séparément.
    """

    def __init__(self):
        super().__init__()

        self.login_window = None

        self.setWindowTitle("Pharmacie - Création de compte")
        self.setMinimumSize(1000, 700)

        self.setup_ui()

        # Ouvre directement l'application en plein écran.
        self.showFullScreen()

    # ==========================================================
    # INTERFACE
    # ==========================================================

    def setup_ui(self):

        self.setStyleSheet("""
            /* ==================================================
               FOND PRINCIPAL
               ================================================== */

            QWidget#mainWindow {
                background-color: #EAF4F3;
            }

            /* ==================================================
               PANNEAU GAUCHE
               ================================================== */

            QFrame#brandingPanel {
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 1,
                    stop: 0 #063B3A,
                    stop: 0.55 #075E5B,
                    stop: 1 #0B7A75
                );
                border: none;
                border-radius: 28px;
            }

            QLabel#brandLogo {
                background-color: #DFF8F3;
                color: #075E5B;
                border-radius: 34px;
                font-size: 30px;
                font-weight: bold;
                padding: 8px;
            }

            QLabel#brandTitle {
                color: white;
                font-size: 34px;
                font-weight: 800;
            }

            QLabel#brandSubtitle {
                color: #D7EFEC;
                font-size: 16px;
                line-height: 1.4;
            }

            QFrame#featureBox {
                background-color: rgba(255, 255, 255, 25);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 15px;
            }

            QLabel#featureIcon {
                color: #A7F3D0;
                font-size: 20px;
                font-weight: bold;
            }

            QLabel#featureTitle {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#featureText {
                color: #CDE8E5;
                font-size: 12px;
            }

            QLabel#securityText {
                color: #B9DEDA;
                font-size: 12px;
            }

            /* ==================================================
               CARTE INSCRIPTION
               ================================================== */

            QFrame#registerCard {
                background-color: #FFFFFF;
                border: 1px solid #DCE9E7;
                border-radius: 28px;
            }

            QLabel#formHeader {
                color: #123B3A;
                font-size: 30px;
                font-weight: 800;
            }

            QLabel#formSubtitle {
                color: #6B8180;
                font-size: 14px;
            }

            QLabel#sectionTitle {
                color: #0F766E;
                font-size: 12px;
                font-weight: bold;
            }

            QLabel.fieldLabel {
                color: #244442;
                font-size: 13px;
                font-weight: 700;
            }

            /* ==================================================
               CHAMPS
               ================================================== */

            QLineEdit {
                background-color: #F5FAF9;
                color: #173B39;
                border: 1px solid #C9DDDA;
                border-radius: 12px;
                padding: 13px 15px;
                font-size: 15px;
                min-height: 27px;
                selection-background-color: #0F766E;
                selection-color: white;
            }

            QLineEdit:hover {
                border: 1px solid #8BBDB8;
                background-color: #F8FCFB;
            }

            QLineEdit:focus {
                border: 2px solid #0F766E;
                background-color: #FFFFFF;
            }

            QLineEdit::placeholder {
                color: #8BA19F;
            }

            /* ==================================================
               BOUTON INSCRIPTION
               ================================================== */

            QPushButton#registerButton {
                background-color: #0F766E;
                color: white;
                border: none;
                border-radius: 12px;
                min-height: 52px;
                padding: 0 20px;
                font-size: 15px;
                font-weight: 800;
            }

            QPushButton#registerButton:hover {
                background-color: #0D9488;
            }

            QPushButton#registerButton:pressed {
                background-color: #115E59;
            }

            QPushButton#registerButton:disabled {
                background-color: #9ABDB9;
                color: #EAF4F3;
            }

            /* ==================================================
               BOUTON RETOUR CONNEXION
               ================================================== */

            QPushButton#loginButton {
                background-color: transparent;
                color: #0F766E;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#loginButton:hover {
                background-color: #E8F5F3;
                color: #075E5B;
            }

            /* ==================================================
               FOOTER
               ================================================== */

            QLabel#footer {
                color: #91A5A3;
                font-size: 11px;
            }

            QLabel#roleBadge {
                background-color: #E6F6F3;
                color: #0F766E;
                border-radius: 10px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        # ------------------------------------------------------
        # Widget principal
        # ------------------------------------------------------

        self.setObjectName("mainWindow")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(35, 35, 35, 35)
        main_layout.setSpacing(28)

        # ======================================================
        # PANNEAU GAUCHE
        # ======================================================

        branding_panel = QFrame()
        branding_panel.setObjectName("brandingPanel")
        branding_panel.setMinimumWidth(380)
        branding_panel.setMaximumWidth(500)

        branding_layout = QVBoxLayout(branding_panel)
        branding_layout.setContentsMargins(45, 45, 45, 45)
        branding_layout.setSpacing(0)

        # Logo
        logo = QLabel("Rx")
        logo.setObjectName("brandLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(68, 68)

        branding_layout.addWidget(logo, 0, Qt.AlignLeft)

        branding_layout.addSpacing(35)

        # Titre
        brand_title = QLabel(
            "GESTION\nPHARMACIE"
        )
        brand_title.setObjectName("brandTitle")
        brand_title.setWordWrap(True)

        branding_layout.addWidget(brand_title)

        branding_layout.addSpacing(15)

        # Description
        brand_subtitle = QLabel(
            "Créez votre compte utilisateur et "
            "rejoignez votre espace de gestion "
            "pharmaceutique."
        )
        brand_subtitle.setObjectName("brandSubtitle")
        brand_subtitle.setWordWrap(True)

        branding_layout.addWidget(brand_subtitle)

        branding_layout.addSpacing(35)

        # Fonctionnalités
        self.add_feature(
            branding_layout,
            "01",
            "Gestion sécurisée",
            "Chaque utilisateur possède son propre compte."
        )

        branding_layout.addSpacing(14)

        self.add_feature(
            branding_layout,
            "02",
            "Gestion des ventes",
            "Travaillez efficacement avec votre espace."
        )

        branding_layout.addSpacing(14)

        self.add_feature(
            branding_layout,
            "03",
            "Gestion du stock",
            "Suivez les produits, lots et dates d'expiration."
        )

        branding_layout.addStretch()

        security = QLabel(
            "●  Système local sécurisé\n"
            "   Vos données restent sur votre ordinateur."
        )
        security.setObjectName("securityText")
        security.setWordWrap(True)

        branding_layout.addWidget(security)

        main_layout.addWidget(branding_panel)

        # ======================================================
        # CARTE DROITE
        # ======================================================

        card = QFrame()
        card.setObjectName("registerCard")
        card.setMinimumWidth(480)
        card.setMaximumWidth(600)

        # Ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setOffset(0, 12)
        shadow.setColor(Qt.black)

        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 42, 50, 38)
        card_layout.setSpacing(0)

        # ------------------------------------------------------
        # En-tête
        # ------------------------------------------------------

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_container = QVBoxLayout()
        title_container.setSpacing(5)

        title = QLabel("Créer un compte")
        title.setObjectName("formHeader")

        subtitle = QLabel(
            "Renseignez vos informations pour commencer."
        )
        subtitle.setObjectName("formSubtitle")

        title_container.addWidget(title)
        title_container.addWidget(subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch()

        role_badge = QLabel("COMPTE WORKER")
        role_badge.setObjectName("roleBadge")
        role_badge.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(
            role_badge,
            0,
            Qt.AlignTop
        )

        card_layout.addLayout(header_layout)

        card_layout.addSpacing(25)

        # Ligne de séparation visuelle
        section_title = QLabel("INFORMATIONS PERSONNELLES")
        section_title.setObjectName("sectionTitle")

        card_layout.addWidget(section_title)

        card_layout.addSpacing(15)

        # ======================================================
        # NOM COMPLET
        # ======================================================

        name_label = QLabel("Nom complet")
        name_label.setProperty("class", "fieldLabel")

        card_layout.addWidget(name_label)
        card_layout.addSpacing(6)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Exemple : Jean Dupont"
        )
        self.name_input.setMaxLength(150)
        self.name_input.setClearButtonEnabled(True)

        card_layout.addWidget(self.name_input)

        card_layout.addSpacing(15)

        # ======================================================
        # TELEPHONE
        # ======================================================

        phone_label = QLabel("Numéro de téléphone")
        phone_label.setProperty("class", "fieldLabel")

        card_layout.addWidget(phone_label)
        card_layout.addSpacing(6)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(
            "Exemple : 0999999999"
        )
        self.phone_input.setMaxLength(30)
        self.phone_input.setClearButtonEnabled(True)

        card_layout.addWidget(self.phone_input)

        card_layout.addSpacing(20)

        # ======================================================
        # SECTION SECURITE
        # ======================================================

        security_title = QLabel("SÉCURITÉ DU COMPTE")
        security_title.setObjectName("sectionTitle")

        card_layout.addWidget(security_title)

        card_layout.addSpacing(15)

        # ======================================================
        # MOT DE PASSE
        # ======================================================

        password_label = QLabel("Mot de passe")
        password_label.setProperty("class", "fieldLabel")

        card_layout.addWidget(password_label)
        card_layout.addSpacing(6)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Minimum 6 caractères"
        )
        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(15)

        # ======================================================
        # CONFIRMATION
        # ======================================================

        confirm_label = QLabel(
            "Confirmer le mot de passe"
        )
        confirm_label.setProperty(
            "class",
            "fieldLabel"
        )

        card_layout.addWidget(confirm_label)
        card_layout.addSpacing(6)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText(
            "Saisissez à nouveau votre mot de passe"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )

        card_layout.addWidget(
            self.confirm_password_input
        )

        card_layout.addSpacing(25)

        # ======================================================
        # BOUTON INSCRIPTION
        # ======================================================

        self.register_button = QPushButton(
            "CRÉER MON COMPTE"
        )
        self.register_button.setObjectName(
            "registerButton"
        )
        self.register_button.setCursor(
            Qt.PointingHandCursor
        )

        self.register_button.clicked.connect(
            self.handle_register
        )

        card_layout.addWidget(
            self.register_button
        )

        # Entrée
        self.confirm_password_input.returnPressed.connect(
            self.handle_register
        )

        card_layout.addSpacing(12)

        # ======================================================
        # RETOUR CONNEXION
        # ======================================================

        login_button = QPushButton(
            "Vous avez déjà un compte ?  SE CONNECTER"
        )
        login_button.setObjectName(
            "loginButton"
        )
        login_button.setCursor(
            Qt.PointingHandCursor
        )

        login_button.clicked.connect(
            self.open_login
        )

        card_layout.addWidget(
            login_button
        )

        card_layout.addStretch()

        # ======================================================
        # FOOTER
        # ======================================================

        footer = QLabel(
            "Application locale • Données stockées sur cet ordinateur"
        )
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)

        card_layout.addWidget(footer)

        main_layout.addStretch(1)
        main_layout.addWidget(card)
        main_layout.addStretch(1)

    # ==========================================================
    # FEATURE DU PANNEAU GAUCHE
    # ==========================================================

    def add_feature(
        self,
        parent_layout,
        number,
        title_text,
        description_text
    ):
        """
        Ajoute une fonctionnalité dans le panneau gauche.
        """

        box = QFrame()
        box.setObjectName("featureBox")
        box.setMinimumHeight(72)

        layout = QHBoxLayout(box)
        layout.setContentsMargins(
            15,
            12,
            15,
            12
        )
        layout.setSpacing(14)

        icon = QLabel(number)
        icon.setObjectName("featureIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedWidth(32)

        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel(title_text)
        title.setObjectName("featureTitle")

        description = QLabel(description_text)
        description.setObjectName("featureText")
        description.setWordWrap(True)

        text_layout.addWidget(title)
        text_layout.addWidget(description)

        layout.addLayout(text_layout)

        parent_layout.addWidget(box)

    # ==========================================================
    # INSCRIPTION
    # ==========================================================

    def handle_register(self):
        """
        Vérifie les données puis crée le compte.
        """

        full_name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm_password = (
            self.confirm_password_input.text()
        )

        # ------------------------------------------------------
        # Vérification du nom
        # ------------------------------------------------------

        if not full_name:
            QMessageBox.warning(
                self,
                "Informations manquantes",
                "Veuillez saisir votre nom complet."
            )
            self.name_input.setFocus()
            return

        # ------------------------------------------------------
        # Vérification du téléphone
        # ------------------------------------------------------

        if not phone:
            QMessageBox.warning(
                self,
                "Informations manquantes",
                "Veuillez saisir votre numéro de téléphone."
            )
            self.phone_input.setFocus()
            return

        # ------------------------------------------------------
        # Vérification du mot de passe
        # ------------------------------------------------------

        if not password:
            QMessageBox.warning(
                self,
                "Mot de passe",
                "Veuillez saisir un mot de passe."
            )
            self.password_input.setFocus()
            return

        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Mot de passe",
                "Le mot de passe doit contenir au moins "
                "6 caractères."
            )
            self.password_input.setFocus()
            return

        # ------------------------------------------------------
        # Confirmation
        # ------------------------------------------------------

        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Confirmation",
                "Les deux mots de passe ne correspondent pas."
            )

            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()

            return

        # ------------------------------------------------------
        # Désactivation du bouton
        # ------------------------------------------------------

        self.register_button.setEnabled(False)
        self.register_button.setText(
            "CRÉATION DU COMPTE..."
        )

        try:

            # Tous les nouveaux utilisateurs sont WORKER.
            user = create_user(
                full_name=full_name,
                phone=phone,
                password=password,
                role="WORKER"
            )

            QMessageBox.information(
                self,
                "Compte créé",
                (
                    f"Bienvenue {user.full_name} !\n\n"
                    "Votre compte a été créé avec succès.\n\n"
                    "Vous pouvez maintenant vous connecter "
                    "avec votre numéro de téléphone et votre "
                    "mot de passe."
                )
            )

            self.open_login()

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Inscription impossible",
                str(error)
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Erreur",
                (
                    "Une erreur est survenue pendant "
                    "la création du compte.\n\n"
                    f"Détails : {error}"
                )
            )

        finally:

            self.register_button.setEnabled(True)
            self.register_button.setText(
                "CRÉER MON COMPTE"
            )

    # ==========================================================
    # RETOUR À LA CONNEXION
    # ==========================================================

    def open_login(self):
        """
        Retourne vers la page de connexion.
        """

        from ui.login import LoginWindow

        self.login_window = LoginWindow()

        # LoginWindow est déjà configurée en plein écran.
        self.login_window.show()

        self.close()

    # ==========================================================
    # AFFICHAGE PLEIN ÉCRAN
    # ==========================================================

    def showEvent(self, event):
        """
        Garantit que la fenêtre s'ouvre en plein écran.
        """

        super().showEvent(event)

        if not self.isFullScreen():
            self.showFullScreen()