import sqlite3
import os
import glob

def trouver_la_base():
    """Cherche le fichier .db dans le projet."""
    chemins = ["*.db", "app/*.db", "data/*.db", "database/*.db", "./instance/*.db"]
    for pattern in chemins:
        fichiers = glob.glob(pattern)
        if fichiers:
            return fichiers[0]
    # Si rien trouvé, utilise le nom par défaut
    return "marches_publics.db"

def migrer():
    db_path = trouver_la_base()
    print(f"📁 Base détectée : {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"❌ Fichier de base de données introuvable: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cur.execute("PRAGMA table_info(markets)")
    colonnes = [row[1] for row in cur.fetchall()]
    
    if "planning_id" in colonnes:
        print("✅ La colonne 'planning_id' existe déjà. Aucune action nécessaire.")
    else:
        print("➕ Ajout de la colonne 'planning_id' à la table 'markets'...")
        cur.execute("""
            ALTER TABLE markets 
            ADD COLUMN planning_id INTEGER
        """)
        conn.commit()
        print("✅ Colonne ajoutée avec succès.")
        
        # Optionnel : créer un index pour accélérer les jointures
        cur.execute("CREATE INDEX IF NOT EXISTS ix_markets_planning_id ON markets(planning_id)")
        conn.commit()
        print("✅ Index créé.")
    
    conn.close()
    print("🎉 Migration terminée. Tu peux redémarrer l'application.")

if __name__ == "__main__":
    migrer()
