import hashlib
import hmac
import secrets


# Nombre d'itérations utilisé pour le hash PBKDF2
ITERATIONS = 310_000


def hash_password(password: str) -> str:
    """
    Transforme un mot de passe en hash sécurisé.
    """

    if not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")

    # Génération d'un sel aléatoire
    salt = secrets.token_bytes(32)

    # Création du hash
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    # Format :
    # algorithme$iterations$salt$hash
    return (
        f"pbkdf2_sha256$"
        f"{ITERATIONS}$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Vérifie si le mot de passe correspond au hash enregistré.
    """

    try:
        # Séparer les différentes parties du hash
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        # Vérifier l'algorithme
        if algorithm != "pbkdf2_sha256":
            return False

        # Convertir le nombre d'itérations
        iterations = int(iterations)

        # Reconvertir le sel
        salt = bytes.fromhex(salt_hex)

        # Hash attendu
        expected_hash = bytes.fromhex(hash_hex)

        # Calculer le hash du mot de passe fourni
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        # Comparaison sécurisée
        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False