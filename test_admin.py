from database.user_database import (
    DATABASE_PATH,
    init_user_database,
    SessionLocal,
)
from models.user import User


print("=" * 60)
print("DIAGNOSTIC ADMIN")
print("=" * 60)

print("Base utilisée :")
print(DATABASE_PATH)
print()

init_user_database()

with SessionLocal() as session:

    users = session.query(User).all()

    print(f"Nombre d'utilisateurs : {len(users)}")
    print()

    if not users:
        print("❌ Aucun utilisateur dans la base.")

    else:
        for user in users:
            print("-" * 40)
            print("ID       :", user.id)
            print("Nom      :", user.full_name)
            print("Téléphone:", repr(user.phone))
            print("Rôle     :", repr(user.role))
            print("Actif    :", user.is_active)

print()
print("=" * 60)