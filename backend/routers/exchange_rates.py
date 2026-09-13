from fastapi import APIRouter, Depends

from core.session import get_current_session
from db import schemas
from services.exchange_rate_service import current_rate_to_inr


router = APIRouter(prefix="/exchange-rates", tags=["exchange rates"])


@router.get("/{currency}/inr", response_model=schemas.ExchangeRateReferenceOut)
def get_current_rate(currency: str, _session=Depends(get_current_session)):
    return current_rate_to_inr(currency)
