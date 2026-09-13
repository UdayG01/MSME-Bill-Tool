"""Private, tenant-scoped image storage for invoice branding."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image, ImageChops, ImageOps, UnidentifiedImageError
from fastapi import UploadFile
from sqlalchemy.orm import Session

from core.config import get_settings
from db import models
from services.errors import ServiceError

ALLOWED_TYPES = {"image/png", "image/jpeg"}


def prepare_image(content: bytes, mime_type: str) -> tuple[bytes, int, int]:
    """Normalize orientation and trim empty outer padding without stretching."""
    image = ImageOps.exif_transpose(Image.open(BytesIO(content)))
    image.load()
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = None
    if alpha.getextrema()[0] < 255:
        bbox = alpha.point(lambda value: 255 if value > 8 else 0).getbbox()
    else:
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
        difference = ImageChops.difference(rgb, background).convert("L")
        bbox = difference.point(lambda value: 255 if value > 18 else 0).getbbox()

    if bbox:
        left, top, right, bottom = bbox
        if right - left >= 5 and bottom - top >= 5:
            padding = max(2, round(max(right - left, bottom - top) * 0.05))
            crop_box = (
                max(0, left - padding),
                max(0, top - padding),
                min(image.width, right + padding),
                min(image.height, bottom + padding),
            )
            image = image.crop(crop_box)

    output = BytesIO()
    if mime_type == "image/jpeg":
        image.convert("RGB").save(output, format="JPEG", quality=92, optimize=True)
    else:
        image.save(output, format="PNG", optimize=True)
    return output.getvalue(), image.width, image.height


def _asset(db: Session, tenant_id: str, asset_id: str) -> models.MediaAsset:
    # Issued invoices retain their original asset IDs; inactive only means it is
    # no longer the company's current selection, not that history may vanish.
    asset = db.query(models.MediaAsset).filter_by(id=asset_id, tenant_id=tenant_id).first()
    if not asset:
        raise ServiceError(404, "Media asset not found")
    return asset


async def upload(db: Session, tenant_id: str, purpose: str, file: UploadFile) -> models.MediaAsset:
    if purpose not in {"logo", "signature"}:
        raise ServiceError(400, "Unsupported media purpose")
    content = await file.read()
    limit = get_settings().media_max_logo_bytes if purpose == "logo" else get_settings().media_max_signature_bytes
    if not content or len(content) > limit:
        raise ServiceError(400, f"{purpose.title()} must be a non-empty image under {limit // 1024} KB")
    if file.content_type not in ALLOWED_TYPES:
        raise ServiceError(400, "Only PNG and JPEG images are accepted")
    try:
        image = Image.open(BytesIO(content)); image.verify()
        image = ImageOps.exif_transpose(Image.open(BytesIO(content))); width, height = image.size
    except (UnidentifiedImageError, OSError):
        raise ServiceError(400, "The uploaded file is not a valid image")
    if width < 1 or height < 1 or width * height > 20_000_000:
        raise ServiceError(400, "Image dimensions are invalid or too large")
    content, width, height = prepare_image(content, file.content_type)
    suffix = ".png" if file.content_type == "image/png" else ".jpg"
    root = Path(get_settings().media_storage_path) / tenant_id
    root.mkdir(parents=True, exist_ok=True)
    key = f"{purpose}-{uuid.uuid4().hex}{suffix}"
    (root / key).write_bytes(content)
    previous_id = getattr(db.get(models.Tenant, tenant_id), f"{purpose}_asset_id")
    if previous_id:
        previous = db.query(models.MediaAsset).filter_by(id=previous_id, tenant_id=tenant_id).first()
        if previous: previous.is_active = False
    asset = models.MediaAsset(tenant_id=tenant_id, purpose=purpose, storage_key=f"{tenant_id}/{key}", mime_type=file.content_type, file_size=len(content), width=width, height=height, checksum=sha256(content).hexdigest())
    db.add(asset); db.flush()
    setattr(db.get(models.Tenant, tenant_id), f"{purpose}_asset_id", asset.id)
    db.commit(); db.refresh(asset)
    return asset


def remove(db: Session, tenant_id: str, purpose: str) -> None:
    tenant = db.get(models.Tenant, tenant_id); asset_id = getattr(tenant, f"{purpose}_asset_id")
    if asset_id:
        asset = db.query(models.MediaAsset).filter_by(id=asset_id, tenant_id=tenant_id).first()
        if asset: asset.is_active = False
        setattr(tenant, f"{purpose}_asset_id", None)
        db.commit()


def content(db: Session, tenant_id: str, asset_id: str) -> tuple[bytes, str]:
    asset = _asset(db, tenant_id, asset_id)
    path = Path(get_settings().media_storage_path) / asset.storage_key
    if not path.is_file(): raise ServiceError(404, "Media file is unavailable")
    return path.read_bytes(), asset.mime_type
