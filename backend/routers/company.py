from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db import schemas, get_db
from core.session import get_current_session
from services import billing_settings_service, company_service, media_service
from services.pdf_service import build_company_preview_pdf

router = APIRouter(tags=["company"])


@router.get("/company", response_model=schemas.CompanyOut)
def get_company(session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.get_company(db, session["tenant_id"])


@router.post("/company/invoice-preview")
def preview_invoice(payload: schemas.CompanyUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    tenant = company_service.get_company(db, session["tenant_id"])
    settings = billing_settings_service.get_settings(db, session["tenant_id"])
    content = build_company_preview_pdf(tenant, settings, payload.model_dump(exclude_unset=True))
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="invoice-preview.pdf"'},
    )


@router.put("/company", response_model=schemas.CompanyOut)
def update_company(payload: schemas.CompanyUpdate, session=Depends(get_current_session), db: Session = Depends(get_db)):
    return company_service.update_company(db, session["tenant_id"], payload)


@router.post("/company/media/{purpose}", response_model=schemas.MediaAssetOut, status_code=201)
async def upload_media(purpose: str, file: UploadFile = File(...), session=Depends(get_current_session), db: Session = Depends(get_db)):
    return await media_service.upload(db, session["tenant_id"], purpose, file)


@router.delete("/company/media/{purpose}", status_code=204)
def remove_media(purpose: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    media_service.remove(db, session["tenant_id"], purpose)


@router.get("/company/media/{asset_id}")
def get_media(asset_id: str, session=Depends(get_current_session), db: Session = Depends(get_db)):
    content, mime_type = media_service.content(db, session["tenant_id"], asset_id)
    return Response(content=content, media_type=mime_type)
