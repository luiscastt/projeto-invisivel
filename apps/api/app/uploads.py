import io
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from .db import get_db, uid
from .models import Evidence
from .security import require_user, optional_user
from .storage import put_evidence, read_evidence

router = APIRouter(tags=["Evidências"])
Image.MAX_IMAGE_PIXELS = 20_000_000


@router.post("/uploads", status_code=201)
async def upload(request: Request, file: UploadFile = File(...), caption: str = Form("", max_length=300), user=Depends(require_user), db: Session = Depends(get_db, scope="function")):
    raw = await file.read(5 * 1024 * 1024 + 1)
    await file.close()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Cada foto pode ter até 5 MiB.")
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(422, "Envie uma fotografia JPEG, PNG ou WebP.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(raw))
            if image.format not in ("JPEG", "PNG", "WEBP") or image.width * image.height > Image.MAX_IMAGE_PIXELS:
                raise ValueError()
            image.load()
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((2400, 2400))
            # New image buffer strips EXIF, ICC, GPS and arbitrary metadata.
            clean = Image.new("RGB", image.size)
            clean.paste(image)
            output = io.BytesIO()
            clean.save(output, "JPEG", quality=88, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "Imagem inválida ou com dimensões excessivas.")
    id_ = uid()
    relative = f"uploads/{id_}.jpg"
    put_evidence(request.app.state.settings, relative, output.getvalue())
    db.add(Evidence(id=id_, owner_id=user.id, path=relative, caption=caption))
    return {"id": id_, "caption": caption}


@router.get("/media/{evidence_id}")
def media(evidence_id: str, request: Request, user=Depends(optional_user), db: Session = Depends(get_db, scope="function")):
    evidence = db.get(Evidence, evidence_id)
    if evidence is None or (not evidence.approved and not (user and (user.id == evidence.owner_id or user.role == "admin"))):
        raise HTTPException(404, "Evidência não disponível publicamente.")
    content = read_evidence(request.app.state.settings, evidence.path)
    if content is None:
        raise HTTPException(404, "Arquivo indisponível.")
    return Response(content, media_type="image/jpeg", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": "inline"})
