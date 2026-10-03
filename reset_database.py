from database.database import engine, Base
from database.models import Product, ProductBatch, Sale, SaleItem


def reset_database():
    print("=" * 70)
    print("VIDAGE DES DONNÉES DE LA BASE DE DONNÉES")
    print("=" * 70)

    confirmation = input(
        "\nATTENTION : toutes les données seront supprimées.\n"
        "Les tables et la structure de la base seront conservées.\n\n"
        "Tapez OUI pour continuer : "
    )

    if confirmation.strip().upper() != "OUI":
        print("\nOpération annulée.")
        return

    try:
        with engine.begin() as connection:

            # Désactiver temporairement les contraintes SQLite
            connection.exec_driver_sql("PRAGMA foreign_keys = OFF")

            # Supprimer les données dans l'ordre
            connection.execute(SaleItem.__table__.delete())
            connection.execute(Sale.__table__.delete())
            connection.execute(ProductBatch.__table__.delete())
            connection.execute(Product.__table__.delete())

            # Réactiver les contraintes
            connection.exec_driver_sql("PRAGMA foreign_keys = ON")

        print("\n" + "=" * 70)
        print("✓ BASE DE DONNÉES VIDÉE AVEC SUCCÈS")
        print("=" * 70)
        print("\nLes tables existent toujours.")
        print("Toutes les données ont été supprimées.")

    except Exception as e:
        print("\n❌ ERREUR :", e)


if __name__ == "__main__":
    reset_database()