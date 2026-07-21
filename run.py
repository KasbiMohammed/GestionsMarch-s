"""
Script de démarrage de l'application
"""

import sys
import uvicorn
from app.config import settings
print("ARGV =", sys.argv)
# Port par défaut
port = 8000

# Lire le port depuis la ligne de commande
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Port invalide, utilisation de 8000.")

if __name__ == "__main__":
    print(f"Demarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Mode: {'Developpement' if settings.DEBUG else 'Production'}")
    print(f"Serveur: http://localhost:{port}")
    print(f"Documentation API: http://localhost:{port}/docs")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,   # mettre False pour tester
        log_level="info" if settings.DEBUG else "warning",
    )