"""
Utilitaires de gestion des fichiers
Fonctions pour l'upload, le téléchargement et la gestion des fichiers
"""

import os
import uuid
from typing import Optional, Tuple
from datetime import datetime
import shutil
from pathlib import Path


def generate_unique_filename(original_filename: str) -> str:
    """
    Génère un nom de fichier unique en ajoutant un UUID
    
    Args:
        original_filename: Nom du fichier original
        
    Returns:
        Nom de fichier unique
    """
    ext = os.path.splitext(original_filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier en supprimant les caractères dangereux
    
    Args:
        filename: Nom du fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    # Caractères à remplacer
    dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les espaces au début et à la fin
    filename = filename.strip()
    
    # Limiter la longueur
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Récupère l'extension d'un fichier
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Extension du fichier (avec le point)
    """
    return os.path.splitext(filename)[1].lower()


def get_file_size(filepath: str) -> int:
    """
    Récupère la taille d'un fichier en octets
    
    Args:
        filepath: Chemin du fichier
        
    Returns:
        Taille du fichier en octets
    """
    return os.path.getsize(filepath)


def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille en octets en format lisible
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Taille formatée (ex: "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def create_directory(directory: str) -> bool:
    """
    Crée un répertoire s'il n'existe pas
    
    Args:
        directory: Chemin du répertoire
        
    Returns:
        True si succès, False sinon
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError:
        return False


def delete_file(filepath: str) -> bool:
    """
    Supprime un fichier
    
    Args:
        filepath: Chemin du fichier
        
    Returns:
        True si succès, False sinon
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except OSError:
        return False


def delete_directory(directory: str) -> bool:
    """
    Supprime un répertoire et son contenu
    
    Args:
        directory: Chemin du répertoire
        
    Returns:
        True si succès, False sinon
    """
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        return True
    except OSError:
        return False


def copy_file(source: str, destination: str) -> bool:
    """
    Copie un fichier
    
    Args:
        source: Chemin source
        destination: Chemin destination
        
    Returns:
        True si succès, False sinon
    """
    try:
        shutil.copy2(source, destination)
        return True
    except (OSError, shutil.Error):
        return False


def move_file(source: str, destination: str) -> bool:
    """
    Déplace un fichier
    
    Args:
        source: Chemin source
        destination: Chemin destination
        
    Returns:
        True si succès, False sinon
    """
    try:
        shutil.move(source, destination)
        return True
    except (OSError, shutil.Error):
        return False


def ensure_upload_directory(base_dir: str, subfolder: str = None) -> str:
    """
    S'assure que le répertoire d'upload existe et retourne son chemin
    
    Args:
        base_dir: Répertoire de base
        subfolder: Sous-dossier optionnel
        
    Returns:
        Chemin du répertoire d'upload
    """
    if subfolder:
        upload_dir = os.path.join(base_dir, subfolder)
    else:
        upload_dir = base_dir
    
    create_directory(upload_dir)
    return upload_dir


def generate_upload_path(base_dir: str, filename: str, subfolder: str = None) -> str:
    """
    Génère un chemin d'upload complet avec nom de fichier unique
    
    Args:
        base_dir: Répertoire de base
        filename: Nom du fichier original
        subfolder: Sous-dossier optionnel
        
    Returns:
        Chemin complet du fichier
    """
    upload_dir = ensure_upload_directory(base_dir, subfolder)
    unique_filename = generate_unique_filename(sanitize_filename(filename))
    return os.path.join(upload_dir, unique_filename)


def is_image_file(filename: str) -> bool:
    """
    Vérifie si un fichier est une image
    
    Args:
        filename: Nom du fichier
        
    Returns:
        True si c'est une image, False sinon
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']
    return get_file_extension(filename) in image_extensions


def is_pdf_file(filename: str) -> bool:
    """
    Vérifie si un fichier est un PDF
    
    Args:
        filename: Nom du fichier
        
    Returns:
        True si c'est un PDF, False sinon
    """
    return get_file_extension(filename) == '.pdf'


def is_document_file(filename: str) -> bool:
    """
    Vérifie si un fichier est un document
    
    Args:
        filename: Nom du fichier
        
    Returns:
        True si c'est un document, False sinon
    """
    document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.odt', '.ods']
    return get_file_extension(filename) in document_extensions


def get_mime_type(filename: str) -> str:
    """
    Récupère le type MIME d'un fichier basé sur son extension
    
    Args:
        filename: Nom du fichier
        
    Returns:
        Type MIME
    """
    mime_types = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
        '.rar': 'application/vnd.rar'
    }
    
    ext = get_file_extension(filename)
    return mime_types.get(ext, 'application/octet-stream')


def validate_file_upload(filename: str, file_size: int, 
                        max_size: int = 10485760, 
                        allowed_extensions: list = None) -> Tuple[bool, str]:
    """
    Valide un fichier uploadé
    
    Args:
        filename: Nom du fichier
        file_size: Taille du fichier
        max_size: Taille maximale autorisée (défaut: 10MB)
        allowed_extensions: Liste des extensions autorisées
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Vérifier la taille
    if file_size > max_size:
        return False, f"Le fichier dépasse la taille maximale de {format_file_size(max_size)}"
    
    # Vérifier l'extension si fournie
    if allowed_extensions:
        ext = get_file_extension(filename)
        if ext not in allowed_extensions:
            return False, f"Extension '{ext}' non autorisée. Extensions autorisées: {', '.join(allowed_extensions)}"
    
    return True, ""


def create_backup_directory(base_dir: str, timestamp: datetime = None) -> str:
    """
    Crée un répertoire de backup avec timestamp
    
    Args:
        base_dir: Répertoire de base
        timestamp: Timestamp optionnel
        
    Returns:
        Chemin du répertoire de backup
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    backup_name = timestamp.strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(base_dir, backup_name)
    
    create_directory(backup_dir)
    return backup_dir


def cleanup_old_files(directory: str, days: int = 30) -> int:
    """
    Nettoie les fichiers plus anciens qu'un certain nombre de jours
    
    Args:
        directory: Répertoire à nettoyer
        days: Nombre de jours
        
    Returns:
        Nombre de fichiers supprimés
    """
    from datetime import timedelta
    
    cutoff_time = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_time:
                    if delete_file(filepath):
                        deleted_count += 1
    except OSError:
        pass
    
    return deleted_count


def get_directory_size(directory: str) -> int:
    """
    Calcule la taille totale d'un répertoire
    
    Args:
        directory: Chemin du répertoire
        
    Returns:
        Taille totale en octets
    """
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
    except OSError:
        pass
    
    return total_size
