"""
Service Calendrier Intelligent
Agrégation des événements depuis les modules existants et suivi budgétaire
Module dédié - ne modifie pas les fonctionnalités existantes
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_

from app.models.calendar import CalendarEvent, BudgetTracking, EventType
from app.models.market import Market
from app.models.market_planning import MarketPlanning
from app.models.stage import Stage
from app.models.deadline import Deadline
from app.models.commission import Commission
from app.models.publication import Publication


class CalendarEventAggregator:
    """Agrégateur d'événements depuis les modules existants"""
    
    # Configuration des couleurs par type d'événement
    EVENT_COLORS = {
        EventType.PLANNIFICATION: "#6f42c1",  # violet
        EventType.PREPARATION: "#0dcaf0",  # cyan
        EventType.PUBLICATION: "#198754",  # vert
        EventType.COMMISSION: "#fd7e14",  # orange
        EventType.OUVERTURE_PLIS: "#ffc107",  # jaune
        EventType.ATTRIBUTION: "#20c997",  # turquoise
        EventType.NOTIFICATION: "#dc3545",  # rouge
        EventType.ORDRE_SERVICE: "#6610f2",  # indigo
        EventType.EXECUTION: "#0d6efd",  # bleu
        EventType.RECEPTION: "#d63384",  # rose
        EventType.ALERTE: "#dc3545",  # rouge
        EventType.DELAI: "#6c757d",  # gris
        EventType.AUTRE: "#adb5bd",  # gris clair
    }
    
    # Configuration des icônes par type d'événement
    EVENT_ICONS = {
        EventType.PLANNIFICATION: "bi-calendar-check",
        EventType.PREPARATION: "bi-file-earmark-text",
        EventType.PUBLICATION: "bi-newspaper",
        EventType.COMMISSION: "bi-people",
        EventType.OUVERTURE_PLIS: "bi-envelope-open",
        EventType.ATTRIBUTION: "bi-check-circle",
        EventType.NOTIFICATION: "bi-bell",
        EventType.ORDRE_SERVICE: "bi-file-text",
        EventType.EXECUTION: "bi-gear",
        EventType.RECEPTION: "bi-box-seam",
        EventType.ALERTE: "bi-exclamation-triangle",
        EventType.DELAI: "bi-clock",
        EventType.AUTRE: "bi-calendar-event",
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def aggregate_all_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """
        Agrège tous les événements depuis les modules existants
        """
        events = []
        
        # Événements de planification
        events.extend(self.aggregate_planning_events(start_date, end_date))
        
        # Événements de préparation
        events.extend(self.aggregate_preparation_events(start_date, end_date))
        
        # Événements de publication
        events.extend(self.aggregate_publication_events(start_date, end_date))
        
        # Événements de commission
        events.extend(self.aggregate_commission_events(start_date, end_date))
        
        # Événements d'ouverture des plis
        events.extend(self.aggregate_ouverture_plis_events(start_date, end_date))
        
        # Événements d'attribution
        events.extend(self.aggregate_attribution_events(start_date, end_date))
        
        # Événements d'ordre de service
        events.extend(self.aggregate_ordre_service_events(start_date, end_date))
        
        # Événements d'exécution
        events.extend(self.aggregate_execution_events(start_date, end_date))
        
        # Événements de réception
        events.extend(self.aggregate_reception_events(start_date, end_date))
        
        # Événements de délais
        events.extend(self.aggregate_deadline_events(start_date, end_date))
        
        return events
    
    def aggregate_planning_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de planification"""
        query = self.db.query(MarketPlanning)
        
        if start_date:
            query = query.filter(MarketPlanning.planned_date >= start_date)
        if end_date:
            query = query.filter(MarketPlanning.planned_date <= end_date)
        
        plannings = query.all()
        events = []
        
        for planning in plannings:
            event = CalendarEvent(
                source_module="market_planning",
                source_entity_id=planning.id,
                source_entity_type="market_planning",
                event_type=EventType.PLANNIFICATION,
                title=f"Planification: {planning.title}",
                description=f"Montant: {planning.budget or 0} - Service: {planning.service or 'N/A'}",
                start_date=planning.planned_date,
                end_date=planning.planned_date,
                is_all_day=True,
                service=planning.service,
                responsible=planning.responsible,
                procedure=planning.procedure,
                status=planning.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.PLANNIFICATION],
                icon=self.EVENT_ICONS[EventType.PLANNIFICATION],
                doc_metadata={
                    'budget': planning.budget,
                    'validated': planning.validated
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_preparation_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de préparation"""
        query = self.db.query(Market).filter(
            Market.status.in_(['en_preparation', 'en_validation'])
        )
        
        if start_date:
            query = query.filter(Market.start_date >= start_date)
        if end_date:
            query = query.filter(Market.start_date <= end_date)
        
        markets = query.all()
        events = []
        
        for market in markets:
            event = CalendarEvent(
                source_module="market",
                source_entity_id=market.id,
                source_entity_type="market",
                event_type=EventType.PREPARATION,
                title=f"Préparation: {market.market_number} - {market.object}",
                description=f"Type: {market.market_type} - Montant: {market.estimated_amount or 0}",
                start_date=market.start_date,
                end_date=market.expected_end_date,
                is_all_day=False,
                service=market.service,
                responsible=market.responsible,
                procedure=market.procedure,
                status=market.status,
                priority="medium",
                color=self.EVENT_COLORS[EventType.PREPARATION],
                icon=self.EVENT_ICONS[EventType.PREPARATION],
                doc_metadata={
                    'market_number': market.market_number,
                    'estimated_amount': market.estimated_amount
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_publication_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de publication"""
        query = self.db.query(Publication)
        
        if start_date:
            query = query.filter(Publication.publication_date >= start_date)
        if end_date:
            query = query.filter(Publication.publication_date <= end_date)
        
        publications = query.all()
        events = []
        
        for pub in publications:
            event = CalendarEvent(
                source_module="publication",
                source_entity_id=pub.id,
                source_entity_type="publication",
                event_type=EventType.PUBLICATION,
                title=f"Publication: {pub.publication_type}",
                description=f"Journal: {pub.newspaper or 'N/A'}",
                start_date=pub.publication_date,
                end_date=pub.publication_date,
                is_all_day=True,
                service=pub.service,
                responsible=pub.responsible,
                procedure=pub.procedure,
                status=pub.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.PUBLICATION],
                icon=self.EVENT_ICONS[EventType.PUBLICATION],
                doc_metadata={
                    'newspaper': pub.newspaper,
                    'market_id': pub.market_id
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_commission_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de commission"""
        query = self.db.query(Commission)
        
        if start_date:
            query = query.filter(Commission.commission_date >= start_date)
        if end_date:
            query = query.filter(Commission.commission_date <= end_date)
        
        commissions = query.all()
        events = []
        
        for comm in commissions:
            event = CalendarEvent(
                source_module="commission",
                source_entity_id=comm.id,
                source_entity_type="commission",
                event_type=EventType.COMMISSION,
                title=f"Commission: {comm.commission_type}",
                description=f"Lieu: {comm.location or 'N/A'}",
                start_date=comm.commission_date,
                end_date=comm.commission_date,
                is_all_day=False,
                service=comm.service,
                responsible=comm.responsible,
                procedure=comm.procedure,
                status=comm.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.COMMISSION],
                icon=self.EVENT_ICONS[EventType.COMMISSION],
                doc_metadata={
                    'location': comm.location,
                    'market_id': comm.market_id
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_ouverture_plis_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements d'ouverture des plis"""
        query = self.db.query(Stage).filter(
            Stage.name.ilike('%ouverture%')
        )
        
        if start_date:
            query = query.filter(Stage.planned_date >= start_date)
        if end_date:
            query = query.filter(Stage.planned_date <= end_date)
        
        stages = query.all()
        events = []
        
        for stage in stages:
            market = self.db.query(Market).filter(Market.id == stage.market_id).first()
            market_number = market.market_number if market else "N/A"
            
            event = CalendarEvent(
                source_module="stage",
                source_entity_id=stage.id,
                source_entity_type="stage",
                event_type=EventType.OUVERTURE_PLIS,
                title=f"Ouverture des plis: {market_number}",
                description=f"Étape: {stage.name}",
                start_date=stage.planned_date,
                end_date=stage.planned_date,
                is_all_day=False,
                service=stage.service,
                responsible=stage.responsible,
                procedure=stage.procedure,
                status=stage.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.OUVERTURE_PLIS],
                icon=self.EVENT_ICONS[EventType.OUVERTURE_PLIS],
                doc_metadata={
                    'market_id': stage.market_id,
                    'stage_name': stage.name
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_attribution_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements d'attribution"""
        query = self.db.query(Stage).filter(
            Stage.name.ilike('%attribution%')
        )
        
        if start_date:
            query = query.filter(Stage.planned_date >= start_date)
        if end_date:
            query = query.filter(Stage.planned_date <= end_date)
        
        stages = query.all()
        events = []
        
        for stage in stages:
            market = self.db.query(Market).filter(Market.id == stage.market_id).first()
            market_number = market.market_number if market else "N/A"
            
            event = CalendarEvent(
                source_module="stage",
                source_entity_id=stage.id,
                source_entity_type="stage",
                event_type=EventType.ATTRIBUTION,
                title=f"Attribution: {market_number}",
                description=f"Étape: {stage.name}",
                start_date=stage.planned_date,
                end_date=stage.planned_date,
                is_all_day=False,
                service=stage.service,
                responsible=stage.responsible,
                procedure=stage.procedure,
                status=stage.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.ATTRIBUTION],
                icon=self.EVENT_ICONS[EventType.ATTRIBUTION],
                doc_metadata={
                    'market_id': stage.market_id,
                    'stage_name': stage.name
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_ordre_service_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements d'ordre de service"""
        query = self.db.query(Stage).filter(
            Stage.name.ilike('%ordre%service%')
        )
        
        if start_date:
            query = query.filter(Stage.planned_date >= start_date)
        if end_date:
            query = query.filter(Stage.planned_date <= end_date)
        
        stages = query.all()
        events = []
        
        for stage in stages:
            market = self.db.query(Market).filter(Market.id == stage.market_id).first()
            market_number = market.market_number if market else "N/A"
            
            event = CalendarEvent(
                source_module="stage",
                source_entity_id=stage.id,
                source_entity_type="stage",
                event_type=EventType.ORDRE_SERVICE,
                title=f"Ordre de service: {market_number}",
                description=f"Étape: {stage.name}",
                start_date=stage.planned_date,
                end_date=stage.planned_date,
                is_all_day=False,
                service=stage.service,
                responsible=stage.responsible,
                procedure=stage.procedure,
                status=stage.status,
                priority="medium",
                color=self.EVENT_COLORS[EventType.ORDRE_SERVICE],
                icon=self.EVENT_ICONS[EventType.ORDRE_SERVICE],
                doc_metadata={
                    'market_id': stage.market_id,
                    'stage_name': stage.name
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_execution_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements d'exécution"""
        query = self.db.query(Market).filter(
            Market.status == 'en_cours'
        )
        
        if start_date:
            query = query.filter(Market.start_date >= start_date)
        if end_date:
            query = query.filter(Market.expected_end_date <= end_date)
        
        markets = query.all()
        events = []
        
        for market in markets:
            event = CalendarEvent(
                source_module="market",
                source_entity_id=market.id,
                source_entity_type="market",
                event_type=EventType.EXECUTION,
                title=f"Exécution: {market.market_number} - {market.object}",
                description=f"Progression: {market.progress_percentage or 0}%",
                start_date=market.start_date,
                end_date=market.expected_end_date,
                is_all_day=False,
                service=market.service,
                responsible=market.responsible,
                procedure=market.procedure,
                status=market.status,
                priority="medium",
                color=self.EVENT_COLORS[EventType.EXECUTION],
                icon=self.EVENT_ICONS[EventType.EXECUTION],
                doc_metadata={
                    'market_number': market.market_number,
                    'progress_percentage': market.progress_percentage
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_reception_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de réception"""
        query = self.db.query(Stage).filter(
            Stage.name.ilike('%réception%')
        )
        
        if start_date:
            query = query.filter(Stage.planned_date >= start_date)
        if end_date:
            query = query.filter(Stage.planned_date <= end_date)
        
        stages = query.all()
        events = []
        
        for stage in stages:
            market = self.db.query(Market).filter(Market.id == stage.market_id).first()
            market_number = market.market_number if market else "N/A"
            
            event = CalendarEvent(
                source_module="stage",
                source_entity_id=stage.id,
                source_entity_type="stage",
                event_type=EventType.RECEPTION,
                title=f"Réception: {market_number}",
                description=f"Étape: {stage.name}",
                start_date=stage.planned_date,
                end_date=stage.planned_date,
                is_all_day=False,
                service=stage.service,
                responsible=stage.responsible,
                procedure=stage.procedure,
                status=stage.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.RECEPTION],
                icon=self.EVENT_ICONS[EventType.RECEPTION],
                doc_metadata={
                    'market_id': stage.market_id,
                    'stage_name': stage.name
                }
            )
            events.append(event)
        
        return events
    
    def aggregate_deadline_events(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CalendarEvent]:
        """Agrège les événements de délais"""
        query = self.db.query(Deadline)
        
        if start_date:
            query = query.filter(Deadline.deadline_date >= start_date)
        if end_date:
            query = query.filter(Deadline.deadline_date <= end_date)
        
        deadlines = query.all()
        events = []
        
        for deadline in deadlines:
            event = CalendarEvent(
                source_module="deadline",
                source_entity_id=deadline.id,
                source_entity_type="deadline",
                event_type=EventType.DELAI,
                title=f"Délai: {deadline.deadline_type}",
                description=f"Description: {deadline.description or 'N/A'}",
                start_date=deadline.deadline_date,
                end_date=deadline.deadline_date,
                is_all_day=True,
                service=deadline.service,
                responsible=deadline.responsible,
                procedure=deadline.procedure,
                status=deadline.status,
                priority="high",
                color=self.EVENT_COLORS[EventType.DELAI],
                icon=self.EVENT_ICONS[EventType.DELAI],
                doc_metadata={
                    'deadline_type': deadline.deadline_type,
                    'market_id': deadline.market_id
                }
            )
            events.append(event)
        
        return events


class BudgetTrackingService:
    """Service de suivi budgétaire"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_annual_budget(self, year: int, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcule le budget annuel
        """
        query = self.db.query(Market)
        
        # Filtrer par année
        query = query.filter(
            text("strftime('%Y', start_date) = :year")
        ).params(year=str(year))
        
        # Filtrer par service si spécifié
        if service:
            query = query.filter(Market.service == service)
        
        markets = query.all()
        
        # Calculer les montants
        budget_voted = sum(m.estimated_amount or 0 for m in markets)
        budget_engaged = sum(m.definitive_amount or 0 for m in markets if m.status in ['en_cours', 'en_retard'])
        budget_consumed = sum(m.definitive_amount or 0 for m in markets if m.status == 'termine')
        budget_remaining = budget_voted - budget_engaged
        
        # Répartition par procédure
        procedure_breakdown = {}
        for market in markets:
            procedure = market.procedure or 'Autre'
            amount = market.definitive_amount or market.estimated_amount or 0
            procedure_breakdown[procedure] = procedure_breakdown.get(procedure, 0) + amount
        
        return {
            'year': year,
            'service': service,
            'budget_voted': budget_voted,
            'budget_engaged': budget_engaged,
            'budget_consumed': budget_consumed,
            'budget_remaining': budget_remaining,
            'total_markets': len(markets),
            'total_amount': budget_voted,
            'procedure_breakdown': procedure_breakdown
        }
    
    def calculate_monthly_budget(self, year: int, service: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Calcule le budget mensuel pour une année
        """
        monthly_data = []
        
        for month in range(1, 13):
            query = self.db.query(Market)
            
            # Filtrer par année et mois
            query = query.filter(
                text("strftime('%Y-%m', start_date) = :year_month")
            ).params(year_month=f"{year}-{month:02d}")
            
            # Filtrer par service si spécifié
            if service:
                query = query.filter(Market.service == service)
            
            markets = query.all()
            
            # Calculer les montants
            budget_voted = sum(m.estimated_amount or 0 for m in markets)
            budget_engaged = sum(m.definitive_amount or 0 for m in markets if m.status in ['en_cours', 'en_retard'])
            budget_consumed = sum(m.definitive_amount or 0 for m in markets if m.status == 'termine')
            budget_remaining = budget_voted - budget_engaged
            
            monthly_data.append({
                'year': year,
                'month': month,
                'service': service,
                'budget_voted': budget_voted,
                'budget_engaged': budget_engaged,
                'budget_consumed': budget_consumed,
                'budget_remaining': budget_remaining,
                'total_markets': len(markets),
                'total_amount': budget_voted
            })
        
        return monthly_data
    
    def sync_budget_tracking(self, year: int, service: Optional[str] = None):
        """
        Synchronise le suivi budgétaire dans la base de données
        """
        # Synchroniser le budget annuel
        annual_data = self.calculate_annual_budget(year, service)
        
        annual_tracking = self.db.query(BudgetTracking).filter(
            BudgetTracking.year == year,
            BudgetTracking.month.is_(None),
            BudgetTracking.service == service if service else BudgetTracking.service.is_(None)
        ).first()
        
        if annual_tracking:
            annual_tracking.budget_voted = annual_data['budget_voted']
            annual_tracking.budget_engaged = annual_data['budget_engaged']
            annual_tracking.budget_consumed = annual_data['budget_consumed']
            annual_tracking.budget_remaining = annual_data['budget_remaining']
            annual_tracking.total_markets = annual_data['total_markets']
            annual_tracking.total_amount = annual_data['total_amount']
            annual_tracking.procedure_breakdown = annual_data['procedure_breakdown']
            annual_tracking.updated_at = datetime.utcnow()
        else:
            annual_tracking = BudgetTracking(
                year=year,
                month=None,
                service=service,
                budget_voted=annual_data['budget_voted'],
                budget_engaged=annual_data['budget_engaged'],
                budget_consumed=annual_data['budget_consumed'],
                budget_remaining=annual_data['budget_remaining'],
                total_markets=annual_data['total_markets'],
                total_amount=annual_data['total_amount'],
                procedure_breakdown=annual_data['procedure_breakdown']
            )
            self.db.add(annual_tracking)
        
        # Synchroniser les budgets mensuels
        monthly_data = self.calculate_monthly_budget(year, service)
        
        for month_data in monthly_data:
            monthly_tracking = self.db.query(BudgetTracking).filter(
                BudgetTracking.year == year,
                BudgetTracking.month == month_data['month'],
                BudgetTracking.service == service if service else BudgetTracking.service.is_(None)
            ).first()
            
            if monthly_tracking:
                monthly_tracking.budget_voted = month_data['budget_voted']
                monthly_tracking.budget_engaged = month_data['budget_engaged']
                monthly_tracking.budget_consumed = month_data['budget_consumed']
                monthly_tracking.budget_remaining = month_data['budget_remaining']
                monthly_tracking.total_markets = month_data['total_markets']
                monthly_tracking.total_amount = month_data['total_amount']
                monthly_tracking.updated_at = datetime.utcnow()
            else:
                monthly_tracking = BudgetTracking(
                    year=year,
                    month=month_data['month'],
                    service=service,
                    budget_voted=month_data['budget_voted'],
                    budget_engaged=month_data['budget_engaged'],
                    budget_consumed=month_data['budget_consumed'],
                    budget_remaining=month_data['budget_remaining'],
                    total_markets=month_data['total_markets'],
                    total_amount=month_data['total_amount']
                )
                self.db.add(monthly_tracking)
        
        self.db.commit()
