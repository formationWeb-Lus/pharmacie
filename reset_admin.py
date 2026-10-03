from database.user_database import (
    SessionLocal,
    init_user_database,
)
from models.user import User
from utils.password import hash_password


# ============================================================
# CONFIGURATION DE L'ADMIN
# ============================================================

ADMIN_NAME = "Administrateur"
ADMIN_PHONE = "0810946352"
ADMIN_PASSWORD = "Admin123!"


# ============================================================
# CRÉER OU RÉINITIALISER L'ADMIN
# ============================================================

def reset_admin():

    # S'assurer que la table users existe
    init_user_database()

    with SessionLocal() as session:

        # Rechercher l'utilisateur avec ce numéro
        user = (
            session.query(User)
            .filter(User.phone == ADMIN_PHONE)
            .first()
        )

        # ----------------------------------------------------
        # CAS 1 : L'utilisateur n'existe pas
        # ----------------------------------------------------

        if user is None:

            user = User(
                full_name=ADMIN_NAME,
                phone=ADMIN_PHONE,
                password_hash=hash_password(
                    ADMIN_PASSWORD
                ),
                role="ADMIN",
                is_active=True
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            print()
            print("=" * 60)
            print("ADMINISTRATEUR CRÉÉ")
            print("=" * 60)
            print("ID           :", user.id)
            print("Nom          :", user.full_name)
            print("Téléphone    :", user.phone)
            print("Mot de passe :", ADMIN_PASSWORD)
            print("Rôle         :", user.role)
            print("Actif        :", user.is_active)
            print("=" * 60)
            print()

            return

        # ----------------------------------------------------
        # CAS 2 : L'utilisateur existe déjà
        # ----------------------------------------------------

        user.full_name = ADMIN_NAME
        user.password_hash = hash_password(
            ADMIN_PASSWORD
        )
        user.role = "ADMIN"
        user.is_active = True

        session.commit()
        session.refresh(user)

        print()
        print("=" * 60)
        print("ADMINISTRATEUR RÉINITIALISÉ")
        print("=" * 60)
        print("ID           :", user.id)
        print("Nom          :", user.full_name)
        print("Téléphone    :", user.phone)
        print("Mot de passe :", ADMIN_PASSWORD)
        print("Rôle         :", user.role)
        print("Actif        :", user.is_active)
        print("=" * 60)
        print()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    reset_admin()