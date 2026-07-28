"""
Export PDF avec ReportLab
Fonctions pour générer des rapports PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from typing import List
import os

from app.models.market import Market
from app.models.market_planning import MarketPlanning


def setup_pdf_document(filepath: str):
    """
    Configure le document PDF avec les polices et styles
    
    Args:
        filepath: Chemin du fichier PDF
        
    Returns:
        Document PDF et styles
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Styles personnalisés - vérifier s'ils existent déjà
    if 'Title' not in styles:
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
    
    if 'Subtitle' not in styles:
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12
        ))
    
    if 'NormalRight' not in styles:
        styles.add(ParagraphStyle(
            name='NormalRight',
            parent=styles['Normal'],
            alignment=TA_RIGHT
        ))
    
    if 'HeaderCell' not in styles:
        styles.add(ParagraphStyle(
            name='HeaderCell',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
    
    return doc, styles


def create_market_title_table(market: Market):
    """
    Crée un tableau avec les informations de titre du marché
    
    Args:
        market: Objet Market
        
    Returns:
        Tableau ReportLab
    """
    data = [
        ["Numéro du marché:", market.market_number, "Date:", datetime.now().strftime("%d/%m/%Y")],
        ["Objet:", market.object, "", ""],
        ["Maître d'ouvrage:", market.master_of_work, "", ""],
        ["Type:", market.market_type.value if market.market_type else "", "Mode de passation:", market.procurement_method.value if market.procurement_method else ""],
    ]
    
    table = Table(data, colWidths=[4*cm, 8*cm, 2*cm, 4*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    
    return table


def create_market_info_table(market: Market):
    """
    Crée un tableau avec les informations détaillées du marché
    
    Args:
        market: Objet Market
        
    Returns:
        Tableau ReportLab
    """
    data = [
        ["Informations Générales"],
        ["Montant estimé:", f"{market.estimated_amount:,.2f} MAD", "Montant définitif:", f"{market.definitive_amount:,.2f} MAD" if market.definitive_amount else "N/A"],
        ["Budget:", f"{market.budget:,.2f} MAD" if market.budget else "N/A", "Crédits:", f"{market.credits:,.2f} MAD" if market.credits else "N/A"],
        ["Service responsable:", market.responsible_service or "N/A", "Responsable suivi:", market.follow_up_responsible or "N/A"],
        ["Statut:", market.status.value if market.status else "N/A", "Progression:", f"{market.progress_percentage}%"],
        ["", "", "", ""],
        ["Dates Importantes"],
        ["Publication:", market.publication_date.strftime("%d/%m/%Y") if market.publication_date else "N/A", "Ouverture:", market.opening_date.strftime("%d/%m/%Y") if market.opening_date else "N/A"],
        ["Attribution:", market.attribution_date.strftime("%d/%m/%Y") if market.attribution_date else "N/A", "Notification:", market.notification_date.strftime("%d/%m/%Y") if market.notification_date else "N/A"],
        ["Début:", market.start_date.strftime("%d/%m/%Y") if market.start_date else "N/A", "Fin prévue:", market.expected_end_date.strftime("%d/%m/%Y") if market.expected_end_date else "N/A"],
        ["Fin réelle:", market.actual_end_date.strftime("%d/%m/%Y") if market.actual_end_date else "N/A", "Réception provisoire:", market.provisional_acceptance_date.strftime("%d/%m/%Y") if market.provisional_acceptance_date else "N/A"],
        ["Réception définitive:", market.definitive_acceptance_date.strftime("%d/%m/%Y") if market.definitive_acceptance_date else "N/A", "", ""],
    ]
    
    table = Table(data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (3, 0), colors.lightblue),
        ('BACKGROUND', (0, 6), (3, 6), colors.lightblue),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (3, 6), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (3, 0)),
        ('SPAN', (0, 6), (3, 6)),
    ]))
    
    return table


def create_companies_table(market: Market):
    """
    Crée un tableau avec les entreprises participantes
    
    Args:
        market: Objet Market
        
    Returns:
        Tableau ReportLab
    """
    if not market.companies:
        return None
    
    data = [["Entreprise", "Montant offre", "Rang", "Attributaire", "Score"]]
    
    for company in market.companies:
        data.append([
            company.name,
            f"{company.offer_amount:,.2f} MAD" if company.offer_amount else "N/A",
            str(company.offer_rank) if company.offer_rank else "N/A",
            "Oui" if company.is_attributed else "Non",
            f"{company.total_score:.2f}" if company.total_score else "N/A"
        ])
    
    table = Table(data, colWidths=[5*cm, 3*cm, 2*cm, 2*cm, 2*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    return table


def export_market_to_pdf(market: Market, filepath: str):
    """
    Exporte un marché vers un fichier PDF
    
    Args:
        market: Objet Market à exporter
        filepath: Chemin du fichier PDF de sortie
    """
    doc, styles = setup_pdf_document(filepath)
    story = []
    
    # Titre
    title = Paragraph("Fiche du Marché Public", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Tableau de titre
    title_table = create_market_title_table(market)
    story.append(title_table)
    story.append(Spacer(1, 1*cm))
    
    # Informations générales
    subtitle = Paragraph("Informations du Marché", styles['Subtitle'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*cm))
    
    info_table = create_market_info_table(market)
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    # Entreprises
    if market.companies:
        subtitle = Paragraph("Entreprises Participantes", styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.3*cm))
        
        companies_table = create_companies_table(market)
        if companies_table:
            story.append(companies_table)
    
    # Observations
    if market.observations:
        story.append(Spacer(1, 1*cm))
        subtitle = Paragraph("Observations", styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.3*cm))
        
        obs_paragraph = Paragraph(market.observations, styles['Normal'])
        story.append(obs_paragraph)
    
    # Pied de page
    story.append(Spacer(1, 2*cm))
    footer = Paragraph(
        f"Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['NormalRight']
    )
    story.append(footer)
    
    # Générer le PDF
    doc.build(story)


def generate_monthly_report(markets: List[Market], month: int, year: int, filepath: str):
    """
    Génère un rapport mensuel des marchés
    
    Args:
        markets: Liste des marchés du mois
        month: Numéro du mois
        year: Année
        filepath: Chemin du fichier PDF de sortie
    """
    doc, styles = setup_pdf_document(filepath)
    story = []
    
    # Titre
    month_names = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    title = Paragraph(f"Rapport Mensuel - {month_names[month-1]} {year}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Statistiques
    total_markets = len(markets)
    total_amount = sum(m.estimated_amount for m in markets if m.estimated_amount)
    
    stats_data = [
        ["Statistique", "Valeur"],
        ["Nombre de marchés", str(total_markets)],
        ["Montant total estimé", f"{total_amount:,.2f} MAD"],
        ["Marchés en cours", str(len([m for m in markets if m.status.value == "en_cours"]))],
        ["Marchés terminés", str(len([m for m in markets if m.status.value == "termine"]))],
    ]
    
    stats_table = Table(stats_data, colWidths=[6*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 1*cm))
    
    # Liste des marchés
    if markets:
        subtitle = Paragraph("Liste des Marchés", styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.3*cm))
        
        market_data = [["Numéro", "Objet", "Montant", "Statut", "Progression"]]
        
        for market in markets:
            market_data.append([
                market.market_number,
                market.object[:50] + "..." if len(market.object) > 50 else market.object,
                f"{market.estimated_amount:,.2f} MAD",
                market.status.value if market.status else "N/A",
                f"{market.progress_percentage}%"
            ])
        
        market_table = Table(market_data, colWidths=[3*cm, 6*cm, 3*cm, 3*cm, 2*cm])
        market_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(market_table)
    
    # Pied de page
    story.append(Spacer(1, 2*cm))
    footer = Paragraph(
        f"Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['NormalRight']
    )
    story.append(footer)
    
    # Générer le PDF
    doc.build(story)


def create_planning_title_table(planning: MarketPlanning):
    """
    Crée un tableau avec les informations de titre de la planification
    
    Args:
        planning: Objet MarketPlanning
        
    Returns:
        Tableau ReportLab
    """
    data = [
        ["Numéro de planification:", planning.planning_number, "Date:", datetime.now().strftime("%d/%m/%Y")],
        ["Intitulé:", planning.title, "", ""],
        ["Exercice:", str(planning.fiscal_year), "Statut:", planning.status.value if planning.status else ""],
    ]
    
    table = Table(data, colWidths=[4*cm, 8*cm, 2*cm, 4*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    
    return table


def create_planning_info_table(planning: MarketPlanning):
    """
    Crée un tableau avec les informations détaillées de la planification
    
    Args:
        planning: Objet MarketPlanning
        
    Returns:
        Tableau ReportLab
    """
    data = [
        ["Informations Générales"],
        ["Type de projet:", planning.project_type.value if planning.project_type else "N/A", "Type de procédure:", planning.procedure_type.value if planning.procedure_type else "N/A"],
        ["Budget estimatif:", f"{planning.estimated_budget:,.2f} MAD" if planning.estimated_budget else "N/A", "Source financement:", planning.funding_source or "N/A"],
        ["Service demandeur:", planning.requesting_service_name or "N/A", "Responsable:", planning.responsible_name or "N/A"],
        ["Priorité:", planning.priority.value if planning.priority else "N/A", "", ""],
        ["", "", "", ""],
        ["Calendrier Prévisionnel"],
        ["Lancement:", planning.launch_date.strftime("%d/%m/%Y") if planning.launch_date else "N/A", "Ouverture des plis:", planning.bid_opening_date.strftime("%d/%m/%Y") if planning.bid_opening_date else "N/A"],
        ["Attribution:", planning.attribution_date.strftime("%d/%m/%Y") if planning.attribution_date else "N/A", "Notification:", planning.notification_date.strftime("%d/%m/%Y") if planning.notification_date else "N/A"],
        ["Ordre de service:", planning.service_order_date.strftime("%d/%m/%Y") if planning.service_order_date else "N/A", "Début:", planning.start_date.strftime("%d/%m/%Y") if planning.start_date else "N/A"],
        ["Fin:", planning.end_date.strftime("%d/%m/%Y") if planning.end_date else "N/A", "", ""],
    ]
    
    table = Table(data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (3, 0), colors.lightblue),
        ('BACKGROUND', (0, 6), (3, 6), colors.lightblue),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 6), (3, 6), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (3, 0)),
        ('SPAN', (0, 6), (3, 6)),
    ]))
    
    return table


def export_planning_to_pdf(planning: MarketPlanning, filepath: str):
    """
    Exporte une planification vers un fichier PDF
    
    Args:
        planning: Objet MarketPlanning à exporter
        filepath: Chemin du fichier PDF de sortie
    """
    doc, styles = setup_pdf_document(filepath)
    story = []
    
    # Titre
    title = Paragraph("Fiche de Planification de Marché", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Tableau de titre
    title_table = create_planning_title_table(planning)
    story.append(title_table)
    story.append(Spacer(1, 1*cm))
    
    # Informations générales
    subtitle = Paragraph("Informations de la Planification", styles['Subtitle'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*cm))
    
    info_table = create_planning_info_table(planning)
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    # Description
    if planning.description:
        subtitle = Paragraph("Description", styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.3*cm))
        
        desc_paragraph = Paragraph(planning.description, styles['Normal'])
        story.append(desc_paragraph)
        story.append(Spacer(1, 1*cm))
    
    # Observations
    if planning.observations:
        subtitle = Paragraph("Observations", styles['Subtitle'])
        story.append(subtitle)
        story.append(Spacer(1, 0.3*cm))
        
        obs_paragraph = Paragraph(planning.observations, styles['Normal'])
        story.append(obs_paragraph)
    
    # Pied de page
    story.append(Spacer(1, 2*cm))
    footer = Paragraph(
        f"Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['NormalRight']
    )
    story.append(footer)
    
    # Générer le PDF
    doc.build(story)


def export_dashboard_to_pdf(stats: dict, filepath: str):
    """
    Exporte les statistiques du dashboard vers un fichier PDF
    
    Args:
        stats: Dictionnaire des statistiques du dashboard
        filepath: Chemin du fichier PDF de sortie
    """
    doc, styles = setup_pdf_document(filepath)
    story = []
    
    # Titre
    title = Paragraph("Rapport du Tableau de Bord", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Date de génération
    date_paragraph = Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['NormalRight']
    )
    story.append(date_paragraph)
    story.append(Spacer(1, 1*cm))
    
    # Statistiques des marchés
    subtitle = Paragraph("Statistiques des Marchés", styles['Subtitle'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*cm))
    
    market_stats = stats.get('markets', {})
    market_data = [
        ["Métrique", "Valeur"],
        ["Total des marchés", str(market_stats.get('total', 0))],
        ["En cours", str(market_stats.get('en_cours', 0))],
        ["Terminés", str(market_stats.get('termine', 0))],
        ["En retard", str(market_stats.get('en_retard', 0))],
        ["En attente", str(market_stats.get('en_attente', 0))],
        ["Annulés", str(market_stats.get('annule', 0))],
        ["Suspendus", str(market_stats.get('suspendu', 0))],
    ]
    
    market_table = Table(market_data, colWidths=[8*cm, 4*cm])
    market_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(market_table)
    story.append(Spacer(1, 1*cm))
    
    # Montants
    subtitle = Paragraph("Montants Budgétaires", styles['Subtitle'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*cm))
    
    amounts = stats.get('amounts', {})
    amount_data = [
        ["Métrique", "Valeur"],
        ["Montant estimé total", f"{amounts.get('total_estimated', 0):,.2f} MAD"],
        ["Montant définitif total", f"{amounts.get('total_definitive', 0):,.2f} MAD"],
        ["Montant attribué", f"{amounts.get('total_attributed', 0):,.2f} MAD"],
        ["Montant payé", f"{amounts.get('total_paid', 0):,.2f} MAD"],
        ["Budget restant", f"{amounts.get('remaining', 0):,.2f} MAD"],
        ["Écart estimation/attribution", f"{amounts.get('variance', 0):,.2f} MAD"],
    ]
    
    amount_table = Table(amount_data, colWidths=[8*cm, 4*cm])
    amount_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(amount_table)
    story.append(Spacer(1, 1*cm))
    
    # Planification
    subtitle = Paragraph("Planification", styles['Subtitle'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*cm))
    
    planning = stats.get('planning', {})
    planning_data = [
        ["Métrique", "Valeur"],
        ["Total planifications", str(planning.get('total', 0))],
        ["Budget planifié", f"{planning.get('budget', 0):,.2f} MAD"],
        ["Validées", str(planning.get('validated', 0))],
        ["Programmées", str(planning.get('programmed', 0))],
    ]
    
    planning_table = Table(planning_data, colWidths=[8*cm, 4*cm])
    planning_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(planning_table)
    
    # Pied de page
    story.append(Spacer(1, 2*cm))
    footer = Paragraph(
        f"Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles['NormalRight']
    )
    story.append(footer)
    
    # Générer le PDF
    doc.build(story)
