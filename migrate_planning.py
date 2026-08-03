import sqlite3
import os

def migrate_planning_table():
    db_path = 'marches_publics.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Vérifier les colonnes existantes
    cur.execute("PRAGMA table_info(market_plannings)")
    existing_columns = [row[1] for row in cur.fetchall()]
    
    print(f"Colonnes existantes: {existing_columns}")
    
    # Ajouter master_of_work si manquant
    if "master_of_work" not in existing_columns:
        print("➕ Ajout de la colonne 'master_of_work'...")
        cur.execute("ALTER TABLE market_plannings ADD COLUMN master_of_work VARCHAR(200) DEFAULT 'Commune'")
        conn.commit()
        print("✅ Colonne 'master_of_work' ajoutée")
    else:
        print("✅ Colonne 'master_of_work' existe déjà")
    
    # Ajouter progress_percentage si manquant
    if "progress_percentage" not in existing_columns:
        print("➕ Ajout de la colonne 'progress_percentage'...")
        cur.execute("ALTER TABLE market_plannings ADD COLUMN progress_percentage INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Colonne 'progress_percentage' ajoutée")
    else:
        print("✅ Colonne 'progress_percentage' existe déjà")
    
    conn.close()
    print("🎉 Migration terminée")

if __name__ == "__main__":
    migrate_planning_table()
