"""
Script de peuplement initial des paramètres de délais réglementaires
Conforme au Décret n°2-22-431 du 8 mars 2023 relatif aux marchés publics
"""

from sqlalchemy import text
from app.database import engine


def seed_deadline_settings():
    """
    Insère les configurations par défaut des délais réglementaires
    Basé sur le Décret n°2-22-431 du 8 mars 2023
    """
    
    settings = [
        # Publication
        {
            'deadline_type': 'publication_pmmp',
            'type_name': 'Publication PMMP',
            'description': 'Délai de publication sur le Portail Marocain des Marchés Publics',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 15
        },
        {
            'deadline_type': 'publication_presse',
            'type_name': 'Publication Presse',
            'description': 'Délai de publication dans la presse (lorsque requis par la réglementation)',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 15
        },
        
        # Délais avant ouverture
        {
            'deadline_type': 'delai_ouverture_plis',
            'type_name': 'Délai minimum avant ouverture des plis',
            'description': 'Délai minimum entre la publication et l\'ouverture des plis selon le type de procédure',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 21
        },
        
        # Éclaircissements
        {
            'deadline_type': 'delai_eclaircissement',
            'type_name': 'Délai de demande d\'éclaircissements',
            'description': 'Délai pour les soumissionnaires pour demander des éclaircissements',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 10
        },
        {
            'deadline_type': 'delai_reponse_eclaircissement',
            'type_name': 'Délai de réponse aux éclaircissements',
            'description': 'Délai pour le maître d\'ouvrage de répondre aux demandes d\'éclaircissements',
            'j1': 10,
            'j2': 5,
            'j3': 2,
            'critique': 1,
            'activation': True,
            'default_days': 5
        },
        
        # Reports
        {
            'deadline_type': 'report_ouverture',
            'type_name': 'Report d\'ouverture des plis',
            'description': 'Délai de report de l\'ouverture des plis',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 7
        },
        
        # Ouverture et évaluation
        {
            'deadline_type': 'ouverture_plis',
            'type_name': 'Ouverture des plis',
            'description': 'Date d\'ouverture des plis',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 0
        },
        {
            'deadline_type': 'validite_offres',
            'type_name': 'Validité des offres',
            'description': 'Durée de validité des offres (généralement 90 ou 120 jours)',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 90
        },
        
        # Délai d'attente (standstill)
        {
            'deadline_type': 'delai_attente_approbation',
            'type_name': 'Délai d\'attente (standstill)',
            'description': 'Délai d\'attente avant approbation de l\'attribution (10 jours minimum)',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 10
        },
        
        # Notification et ordre de service
        {
            'deadline_type': 'notification_attribution',
            'type_name': 'Notification d\'attribution',
            'description': 'Délai de notification de l\'attribution au soumissionnaire retenu',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 7
        },
        {
            'deadline_type': 'ordre_service',
            'type_name': 'Ordre de service',
            'description': 'Délai de notification de l\'ordre de service (début des travaux)',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 7
        },
        
        # Exécution
        {
            'deadline_type': 'debut_execution',
            'type_name': 'Début d\'exécution',
            'description': 'Date de début effectif de l\'exécution du marché',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 0
        },
        {
            'deadline_type': 'fin_execution',
            'type_name': 'Fin d\'exécution',
            'description': 'Date de fin prévue de l\'exécution du marché',
            'j1': 60,
            'j2': 30,
            'j3': 15,
            'critique': 7,
            'activation': True,
            'default_days': 365
        },
        
        # Réceptions
        {
            'deadline_type': 'reception_provisoire',
            'type_name': 'Réception provisoire',
            'description': 'Délai de réception provisoire des travaux/fournitures',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 30
        },
        {
            'deadline_type': 'reception_definitive',
            'type_name': 'Réception définitive',
            'description': 'Délai de réception définitive (après la période de garantie)',
            'j1': 60,
            'j2': 30,
            'j3': 15,
            'critique': 7,
            'activation': True,
            'default_days': 365
        },
        
        # Garanties
        {
            'deadline_type': 'garantie_soumissionnaire',
            'type_name': 'Garantie soumissionnaire',
            'description': 'Validité de la garantie soumissionnaire',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 120
        },
        {
            'deadline_type': 'garantie_execution',
            'type_name': 'Garantie d\'exécution',
            'description': 'Validité de la garantie d\'exécution',
            'j1': 60,
            'j2': 30,
            'j3': 15,
            'critique': 7,
            'activation': True,
            'default_days': 365
        },
        {
            'deadline_type': 'liberation_garantie',
            'type_name': 'Libération de garantie',
            'description': 'Délai de libération de la garantie après réception définitive',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 30
        },
        
        # Réclamations et recours
        {
            'deadline_type': 'delai_reclamation',
            'type_name': 'Délai de réclamation',
            'description': 'Délai pour déposer une réclamation (15 jours)',
            'j1': 15,
            'j2': 7,
            'j3': 3,
            'critique': 1,
            'activation': True,
            'default_days': 15
        },
        {
            'deadline_type': 'delai_recours',
            'type_name': 'Délai de recours',
            'description': 'Délai pour déposer un recours (30 jours)',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 30
        },
        
        # Paiements
        {
            'deadline_type': 'delai_paiement',
            'type_name': 'Délai de paiement',
            'description': 'Délai de paiement (30 à 90 jours selon le marché)',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 45
        },
        {
            'deadline_type': 'delai_paiement_partiel',
            'type_name': 'Délai de paiement partiel',
            'description': 'Délai de paiement des acomptes et situations',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 30
        },
        
        # Procédures spécifiques
        {
            'deadline_type': 'delai_consultation',
            'type_name': 'Délai de consultation',
            'description': 'Délai pour les procédures de consultation',
            'j1': 20,
            'j2': 10,
            'j3': 5,
            'critique': 2,
            'activation': True,
            'default_days': 15
        },
        {
            'deadline_type': 'delai_preselection',
            'type_name': 'Délai de présélection',
            'description': 'Délai pour les procédures avec présélection',
            'j1': 30,
            'j2': 15,
            'j3': 7,
            'critique': 3,
            'activation': True,
            'default_days': 21
        },
        {
            'deadline_type': 'delai_negociation',
            'type_name': 'Délai de négociation',
            'description': 'Délai pour les procédures négociées',
            'j1': 20,
            'j2': 10,
            'j3': 5,
            'critique': 2,
            'activation': True,
            'default_days': 15
        },
    ]
    
    with engine.connect() as conn:
        for setting in settings:
            try:
                conn.execute(text("""
                    INSERT OR REPLACE INTO deadline_settings 
                    (deadline_type, type_name, description, j1, j2, j3, critique, activation, default_days)
                    VALUES (:deadline_type, :type_name, :description, :j1, :j2, :j3, :critique, :activation, :default_days)
                """), setting)
                print(f"✓ Configuration insérée: {setting['type_name']}")
            except Exception as e:
                print(f"✗ Erreur lors de l'insertion de {setting['type_name']}: {e}")
        
        conn.commit()
    
    print("\nPeuplement des paramètres de délais terminé avec succès")
    print(f"Total des configurations insérées: {len(settings)}")


if __name__ == "__main__":
    seed_deadline_settings()
