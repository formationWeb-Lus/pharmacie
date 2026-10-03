from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models.user import Base, User
from utils.password import hash_password, verify_password


# ============================================================
# CHEMIN DE LA BASE DE DONNÉES
# ============================================================

APP_DATA_DIR = Path.home() / "AppData" / "Local" / "Pharmacie"

APP_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = APP_DATA_DIR / "pharmacie.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ============================================================
# ENGINE SQLALCHEMY
# ============================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


# ============================================================
# INITIALISATION
# ============================================================

def init_user_database():
    """
    Crée les tables nécessaires aux utilisateurs.
    """

    Base.metadata.create_all(engine)

    # Crée automatiquement le premier administrateur
    # seulement si aucun utilisateur n'existe.
    create_default_admin()


# ============================================================
# CRÉER L'ADMINISTRATEUR INITIAL
# ============================================================

def create_default_admin():
    """
    Crée un administrateur initial uniquement si
    aucun utilisateur n'existe dans la base.
    """

    with SessionLocal() as session:

        existing_user = session.scalar(
            select(User).limit(1)
        )

        # Un utilisateur existe déjà :
        # on ne crée pas un deuxième administrateur.
        if existing_user is not None:
            return

        admin = User(
            full_name="Administrateur",
            phone="0810946352",
            password_hash=hash_password("Admin123!"),
            role="ADMIN",
            is_active=True
        )

        session.add(admin)
        session.commit()

        print()
        print("=" * 60)
        print("ADMINISTRATEUR INITIAL CRÉÉ")
        print("=" * 60)
        print("Nom          : Administrateur")
        print("Téléphone    : 0810946352")
        print("Mot de passe : Admin123!")
        print("Rôle         : ADMIN")
        print("=" * 60)
        print()


# ============================================================
# CRÉER UN ADMINISTRATEUR
# ============================================================

def create_admin(
    phone: str,
    password: str,
    name: str = "Administrateur"
):
    """
    Crée un administrateur.

    Exemple :

        create_admin(
            phone="0810946352",
            password="Admin123!",
            name="Administrateur"
        )
    """

    phone = phone.strip()
    name = name.strip()

    if not phone:
        raise ValueError(
            "Le numéro de téléphone est obligatoire."
        )

    if not password:
        raise ValueError(
            "Le mot de passe est obligatoire."
        )

    if not name:
        raise ValueError(
            "Le nom est obligatoire."
        )

    with SessionLocal() as session:

        # Vérifier si le numéro existe déjà
        existing_user = session.scalar(
            select(User).where(
                User.phone == phone
            )
        )

        if existing_user is not None:

            # Si c'est déjà un ADMIN
            if str(existing_user.role).upper() == "ADMIN":

                raise ValueError(
                    "Un administrateur utilise déjà ce numéro."
                )

            # Si le numéro appartient à un autre utilisateur
            raise ValueError(
                "Ce numéro appartient déjà à un autre utilisateur."
            )

        admin = User(
            full_name=name,
            phone=phone,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True
        )

        session.add(admin)
        session.commit()

        session.refresh(admin)

        return admin


# ============================================================
# AUTHENTIFICATION
# ============================================================

def authenticate_user(
    phone: str,
    password: str
):
    """
    Vérifie le numéro et le mot de passe.

    Retourne l'utilisateur si les informations
    sont correctes.

    Retourne None sinon.
    """

    phone = phone.strip()

    if not phone or not password:
        return None

    with SessionLocal() as session:

        user = session.scalar(
            select(User).where(
                User.phone == phone
            )
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash
        ):
            return None

        return user


# ============================================================
# CRÉER UN UTILISATEUR
# ============================================================

def create_user(
    full_name: str,
    phone: str,
    password: str,
    role: str = "WORKER"
):
    """
    Crée un nouvel utilisateur.

    Rôles acceptés :
        ADMIN
        WORKER
    """

    full_name = full_name.strip()
    phone = phone.strip()
    role = role.upper().strip()

    if not full_name:
        raise ValueError(
            "Le nom est obligatoire."
        )

    if not phone:
        raise ValueError(
            "Le numéro de téléphone est obligatoire."
        )

    if not password:
        raise ValueError(
            "Le mot de passe est obligatoire."
        )

    if role not in ("ADMIN", "WORKER"):
        raise ValueError(
            "Le rôle doit être ADMIN ou WORKER."
        )

    with SessionLocal() as session:

        existing_user = session.scalar(
            select(User).where(
                User.phone == phone
            )
        )

        if existing_user is not None:
            raise ValueError(
                "Ce numéro existe déjà."
            )

        user = User(
            full_name=full_name,
            phone=phone,
            password_hash=hash_password(password),
            role=role,
            is_active=True
        )

        session.add(user)
        session.commit()

        session.refresh(user)

        return user


# ============================================================
# ACTIVER / DÉSACTIVER UN UTILISATEUR
# ============================================================

def set_user_active(
    user_id: int,
    is_active: bool
):
    """
    Active ou désactive un utilisateur.
    """

    with SessionLocal() as session:

        user = session.get(User, user_id)

        if user is None:
            raise ValueError(
                "Utilisateur introuvable."
            )

        user.is_active = is_active

        session.commit()

        session.refresh(user)

        return user


# ============================================================
# CHANGER LE RÔLE
# ============================================================

def change_user_role(
    user_id: int,
    role: str
):
    """
    Change le rôle d'un utilisateur.
    """

    role = role.upper().strip()

    if role not in ("ADMIN", "WORKER"):
        raise ValueError(
            "Le rôle doit être ADMIN ou WORKER."
        )

    with SessionLocal() as session:

        user = session.get(User, user_id)

        if user is None:
            raise ValueError(
                "Utilisateur introuvable."
            )

        user.role = role

        session.commit()

        session.refresh(user)

        return user