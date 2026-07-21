"""
Utilitaires de validation
Fonctions pour valider les données d'entrée
"""

import re
from typing import Optional


def validate_market_number(market_number: str) -> bool:
    """
    Valide le format d'un numéro de marché
    
    Args:
        market_number: Numéro de marché à valider
        
    Returns:
        True si valide, False sinon
    """
    if not market_number or len(market_number) < 3:
        return False
    
    # Accepte les formats: XXXX-YYYY, XXX/YYYY, alphanumérique
    pattern = r'^[A-Za-z0-9\-/]+$'
    return bool(re.match(pattern, market_number))


def validate_amount(amount: float) -> bool:
    """
    Valide un montant
    
    Args:
        amount: Montant à valider
        
    Returns:
        True si valide, False sinon
    """
    return isinstance(amount, (int, float)) and amount >= 0


def validate_email(email: str) -> bool:
    """
    Valide une adresse email
    
    Args:
        email: Adresse email à valider
        
    Returns:
        True si valide, False sinon
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Valide un numéro de téléphone marocain
    
    Args:
        phone: Numéro de téléphone à valider
        
    Returns:
        True si valide, False sinon
    """
    # Format marocain: +212 6XX XXX XXX ou 06XX XXX XXX
    pattern = r'^(\+212|0)?[6-7]\d{8}$'
    phone_clean = re.sub(r'[\s\-]', '', phone)
    return bool(re.match(pattern, phone_clean))


def validate_rc_number(rc: str) -> bool:
    """
    Valide un numéro de registre de commerce marocain
    
    Args:
        rc: Numéro RC à valider
        
    Returns:
        True si valide, False sinon
    """
    # Format RC marocain: généralement 8-10 chiffres
    pattern = r'^\d{8,10}$'
    return bool(re.match(pattern, rc))


def validate_if_number(if_number: str) -> bool:
    """
    Valide un numéro d'identification fiscale marocain
    
    Args:
        if_number: Numéro IF à valider
        
    Returns:
        True si valide, False sinon
    """
    # Format IF marocain: généralement 8-10 chiffres
    pattern = r'^\d{8,10}$'
    return bool(re.match(pattern, if_number))


def validate_company_name(name: str) -> bool:
    """
    Valide un nom d'entreprise
    
    Args:
        name: Nom de l'entreprise à valider
        
    Returns:
        True si valide, False sinon
    """
    if not name or len(name) < 2:
        return False
    
    # Accepte les lettres, chiffres, espaces et certains caractères spéciaux
    pattern = r'^[A-Za-zÀ-ÿ0-9\s\-\.\,\'&]+$'
    return bool(re.match(pattern, name))


def validate_percentage(value: float) -> bool:
    """
    Valide un pourcentage
    
    Args:
        value: Valeur à valider
        
    Returns:
        True si valide, False sinon
    """
    return isinstance(value, (int, float)) and 0 <= value <= 100


def validate_url(url: str) -> bool:
    """
    Valide une URL
    
    Args:
        url: URL à valider
        
    Returns:
        True si valide, False sinon
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def sanitize_string(text: str) -> str:
    """
    Nettoie une chaîne de caractères pour éviter les injections
    
    Args:
        text: Texte à nettoyer
        
    Returns:
        Texte nettoyé
    """
    if not text:
        return ""
    
    # Supprimer les caractères dangereux
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()


def validate_file_size(size: int, max_size: int) -> bool:
    """
    Valide la taille d'un fichier
    
    Args:
        size: Taille du fichier en octets
        max_size: Taille maximale autorisée
        
    Returns:
        True si valide, False sinon
    """
    return size <= max_size


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """
    Valide le type d'un fichier
    
    Args:
        filename: Nom du fichier
        allowed_types: Liste des extensions autorisées (ex: ['.pdf', '.docx'])
        
    Returns:
        True si valide, False sinon
    """
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_types


def validate_iban(iban: str) -> bool:
    """
    Valide un numéro IBAN
    
    Args:
        iban: Numéro IBAN à valider
        
    Returns:
        True si valide, False sinon
    """
    # Nettoyer l'IBAN
    iban = iban.replace(' ', '').upper()
    
    # Vérifier la longueur minimale
    if len(iban) < 15:
        return False
    
    # Vérifier que tous les caractères sont alphanumériques
    if not iban.isalnum():
        return False
    
    # Déplacer les 4 premiers caractères à la fin
    iban = iban[4:] + iban[:4]
    
    # Remplacer les lettres par des nombres
    iban_numeric = ""
    for char in iban:
        if char.isdigit():
            iban_numeric += char
        else:
            iban_numeric += str(10 + ord(char) - ord('A'))
    
    # Vérifier le modulo 97
    try:
        return int(iban_numeric) % 97 == 1
    except:
        return False
