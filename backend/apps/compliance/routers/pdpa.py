"""PDPA Router
==============
Phase 6: Compliance & NParks Reporting

Django Ninja router for PDPA consent endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.core.auth import AuthenticationService
from apps.core.permissions import require_role

from ..models import PDPAConsentLog, PDPAAction
from ..schemas import (
    PDPAConsentUpdate,
    PDPAConsentLogResponse,
    PDPAConsentLogEntry,
    PDPAConsentCheckRequest,
    PDPAConsentCheckResponse,
)
from ..services.pdpa import PDPAService

logger = logging.getLogger(__name__)

router = Router(tags=["compliance", "pdpa"])


@router.post("/consent/update", response=PDPAConsentLogEntry)
def update_consent(
    request,
    data: PDPAConsentUpdate,
):
    """
    Update PDPA consent for customer.
    Logs to immutable audit trail.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")
    
    require_role(request, "admin", "management", "sales")
    
    # Validate action
    if data.action not in ("OPT_IN", "OPT_OUT"):
        raise HttpError(400, "action must be OPT_IN or OPT_OUT")
    
    # Get current state (placeholder - Phase 7 will implement actual customer check)
    current_state = PDPAService.get_latest_consent_state(data.customer_id)
    previous_state = current_state if current_state is not None else False
    
    # Determine new state
    new_state = data.action == "OPT_IN"
    
    # Validate change
    is_valid, error_msg = PDPAService.validate_consent_change(
        customer_id=data.customer_id,
        new_state=new_state,
        actor=user,
    )
    
    if not is_valid:
        raise HttpError(400, error_msg)
    
    try:
        # Log the change
        log = PDPAService.log_consent_change(
            customer_id=data.customer_id,
            action=data.action,
            previous_state=previous_state,
            new_state=new_state,
            actor=user,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        
        logger.info(
            f"PDPA consent updated: customer={data.customer_id}, "
            f"action={data.action}, actor={user.email}"
        )
        
        return PDPAConsentLogEntry.model_validate(log)
        
    except Exception as e:
        logger.error(f"PDPA consent update failed: {e}")
        raise HttpError(400, str(e))


@router.get("/consent/log/{customer_id}", response=PDPAConsentLogResponse)
def get_consent_log(
    request,
    customer_id: UUID,
    page: int = 1,
    per_page: int = 50,
):
    """
    Get PDPA consent history for customer.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")
    
    # Check access - management can see all, others only their entity
    if not user.has_role("management"):
        # Phase 7: Check customer belongs to user's entity
        pass
    
    try:
        logs = PDPAService.get_consent_log(customer_id, limit=per_page * page)
        
        # Simple pagination
        total = len(logs)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = logs[start:end]
        
        return PDPAConsentLogResponse(
            items=[PDPAConsentLogEntry.model_validate(l) for l in paginated],
            total=total,
            page=page,
            per_page=per_page,
        )
        
    except Exception as e:
        logger.error(f"PDPA log retrieval failed: {e}")
        raise HttpError(400, str(e))


@router.post("/blast/check", response=PDPAConsentCheckResponse)
def check_blast_eligibility(
    request,
    data: PDPAConsentCheckRequest,
):
    """
    Check blast eligibility for customer list.
    Returns eligible and excluded customers.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")
    
    require_role(request, "admin", "management", "sales")
    
    try:
        result = PDPAService.check_blast_eligibility(data.customer_ids)
        return result
        
    except Exception as e:
        logger.error(f"PDPA blast check failed: {e}")
        raise HttpError(400, str(e))


@router.get("/stats/{entity_id}")
def get_pdpa_stats(
    request,
    entity_id: UUID,
):
    """
    Get PDPA statistics for entity.
    Returns counts of consented vs opted-out customers.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")
    
    # Check access
    from apps.core.models import Entity
    
    try:
        entity = Entity.objects.get(id=entity_id)
    except Entity.DoesNotExist:
        raise HttpError(404, "Entity not found")
    
    if not user.has_role("management") and user.entity_id != entity_id:
        raise HttpError(403, "Access denied")
    
    # Get counts (Phase 7 will implement actual counting)
    consented = PDPAService.count_consented_customers(entity_id)
    opted_out = PDPAService.count_opted_out_customers(entity_id)
    
    return {
        "entity_id": str(entity_id),
        "entity_name": entity.name,
        "consented_count": consented,
        "opted_out_count": opted_out,
        "total": consented + opted_out,
        "consent_rate": round(consented / (consented + opted_out) * 100, 2) if (consented + opted_out) > 0 else 0,
    }


@router.get("/consent/check/{customer_id}")
def check_customer_consent(
    request,
    customer_id: UUID,
):
    """
    Check current consent status for customer.
    """
    user = AuthenticationService.get_user_from_request(request)
    if not user:
        raise HttpError(401, "Authentication required")
    
    # Phase 7: Add entity scoping check
    
    is_consented = PDPAService.is_consented(customer_id)
    
    return {
        "customer_id": str(customer_id),
        "is_consented": is_consented,
    }
