"""
Script de peuplement initial de la base de connaissances du chatbot
Documents réglementaires marocains des marchés publics
"""

import requests
import json


def seed_chatbot_knowledge():
    """
    Peuple la base de connaissances avec les documents réglementaires via l'API
    """
    from app.services.document_indexer import RegulatoryDocumentLoader
    
    loader = RegulatoryDocumentLoader()
    
    total_indexed = 0
    
    print("📚 Chargement des documents réglementaires...")
    
    # Charger et indexer le Décret 2-22-431
    print("\n📄 Décret n°2-22-431...")
    decret_articles = loader.load_decret_2_22_431()
    for article in decret_articles:
        try:
            response = requests.post(
                'http://localhost:8000/api/chatbot/knowledge',
                json={
                    'title': article['title'],
                    'content': article['content'],
                    'source': article['source'],
                    'category': article['category'],
                    'document_type': 'reglementation',
                    'tags': ['décret', '2-22-431', article['category']]
                }
            )
            if response.status_code == 200:
                print(f"  ✓ {article['title']}")
                total_indexed += 1
            else:
                print(f"  ✗ Erreur HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
    
    # Charger et indexer le CCAG Travaux
    print("\n📄 CCAG Travaux...")
    ccag_articles = loader.load_ccag_travaux()
    for article in ccag_articles:
        try:
            response = requests.post(
                'http://localhost:8000/api/chatbot/knowledge',
                json={
                    'title': article['title'],
                    'content': article['content'],
                    'source': article['source'],
                    'category': article['category'],
                    'document_type': 'reglementation',
                    'tags': ['ccag', 'travaux', article['category']]
                }
            )
            if response.status_code == 200:
                print(f"  ✓ {article['title']}")
                total_indexed += 1
            else:
                print(f"  ✗ Erreur HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
    
    # Charger et indexer le guide PMMP
    print("\n📄 Guide PMMP...")
    pmmp_articles = loader.load_pmmp_guide()
    for article in pmmp_articles:
        try:
            response = requests.post(
                'http://localhost:8000/api/chatbot/knowledge',
                json={
                    'title': article['title'],
                    'content': article['content'],
                    'source': article['source'],
                    'category': article['category'],
                    'document_type': 'guide',
                    'tags': ['pmmp', 'guide', article['category']]
                }
            )
            if response.status_code == 200:
                print(f"  ✓ {article['title']}")
                total_indexed += 1
            else:
                print(f"  ✗ Erreur HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
    
    print(f"\n✅ Peuplement terminé avec succès")
    print(f"📊 Total des documents indexés: {total_indexed}")


if __name__ == "__main__":
    seed_chatbot_knowledge()
