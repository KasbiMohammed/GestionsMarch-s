"""
Utilitaires de gestion des dates
Fonctions pour le calcul des délais et le formatage des dates
"""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import re


def calculate_delay(planned_date: Optional[datetime], actual_date: Optional[datetime]) -> int:
    """
    Calcule le retard en jours entre une date prévue et une date réelle
    
    Args:
        planned_date: Date prévue
        actual_date: Date réelle
        
    Returns:
        Retard en jours (positif si en retard, négatif si en avance)
    """
    if not planned_date or not actual_date:
        return 0
    
    return (actual_date - planned_date).days


def get_alert_level(delay_days: int) -> str:
    """
    Détermine le niveau d'alerte en fonction du retard
    
    Args:
        delay_days: Nombre de jours de retard
        
    Returns:
        Niveau d'alerte ('green', 'orange', 'red')
    """
    if delay_days <= 0:
        return 'green'
    elif delay_days <= 7:
        return 'orange'
    else:
        return 'red'


def format_date(date: Optional[datetime], format_str: str = "%d/%m/%Y") -> str:
    """
    Formate une date selon le format spécifié
    
    Args:
        date: Date à formater
        format_str: Format de sortie
        
    Returns:
        Date formatée ou chaîne vide
    """
    if not date:
        return ""
    return date.strftime(format_str)


def parse_date(date_str: str, format_str: str = "%d/%m/%Y") -> Optional[datetime]:
    """
    Parse une chaîne de caractères en datetime
    
    Args:
        date_str: Chaîne de caractères représentant une date
        format_str: Format de la chaîne
        
    Returns:
        Objet datetime ou None
    """
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


def add_business_days(start_date: date, days: int) -> date:
    """
    Ajoute des jours ouvrables à une date
    
    Args:
        start_date: Date de départ
        days: Nombre de jours ouvrables à ajouter
        
    Returns:
        Date résultante
    """
    current_date = start_date
    added_days = 0
    
    while added_days < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Lundi = 0, Vendredi = 4
            added_days += 1
    
    return current_date


def get_date_range(start_date: date, end_date: date) -> list:
    """
    Génère une liste de dates entre deux dates
    
    Args:
        start_date: Date de début
        end_date: Date de fin
        
    Returns:
        Liste des dates
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def get_quarter(date: date) -> Tuple[int, int]:
    """
    Retourne le trimestre et l'année d'une date
    
    Args:
        date: Date
        
    Returns:
        Tuple (trimestre, année)
    """
    quarter = (date.month - 1) // 3 + 1
    return quarter, date.year


def get_week_number(date: date) -> int:
    """
    Retourne le numéro de semaine d'une date
    
    Args:
        date: Date
        
    Returns:
        Numéro de semaine
    """
    return date.isocalendar()[1]


def is_weekend(date: date) -> bool:
    """
    Vérifie si une date est un week-end
    
    Args:
        date: Date à vérifier
        
    Returns:
        True si c'est un week-end, False sinon
    """
    return date.weekday() >= 5  # Samedi = 5, Dimanche = 6


def get_age(date: date) -> int:
    """
    Calcule l'âge en années d'une date
    
    Args:
        date: Date de naissance
        
    Returns:
        Âge en années
    """
    today = date.today()
    return today.year - date.year - ((today.month, today.day) < (date.month, date.day))


def format_duration(days: int) -> str:
    """
    Formate une durée en jours en texte lisible
    
    Args:
        days: Nombre de jours
        
    Returns:
        Durée formatée (ex: "2 ans 3 mois 15 jours")
    """
    if days < 0:
        days = abs(days)
    
    years = days // 365
    remaining_days = days % 365
    months = remaining_days // 30
    remaining_days = remaining_days % 30
    
    parts = []
    if years > 0:
        parts.append(f"{years} an{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} mois")
    if remaining_days > 0 or not parts:
        parts.append(f"{remaining_days} jour{'s' if remaining_days > 1 else ''}")
    
    return " ".join(parts)


def parse_french_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date en français (ex: "15 janvier 2024")
    
    Args:
        date_str: Chaîne de caractères en français
        
    Returns:
        Objet datetime ou None
    """
    french_months = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
    }
    
    try:
        parts = date_str.lower().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month = french_months.get(parts[1])
            year = int(parts[2])
            
            if month:
                return datetime(year, month, day)
    except (ValueError, IndexError, KeyError):
        pass
    
    return None
