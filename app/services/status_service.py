from typing import Optional
from app.models import Ticket
from app.services.ticket_service import TicketService


class StatusService:
    def __init__(self, ticket_service: TicketService):
        self.ticket_service = ticket_service

    def get_ticket_status(self, ticket_id: str) -> Optional[Ticket]:
        return self.ticket_service.get_ticket(ticket_id)
