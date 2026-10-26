
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.template import Template
from backend.app.models.user import User
from backend.app.schemas.template import TemplateListResponse, TemplateResponse

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.get("", response_model=TemplateListResponse)
def list_templates(
    category: str | None = Query(None, description="all, social, longform, newsletters, video"),
    search: str | None = Query(None, description="Search template title and formula"),
    db: Session = Depends(get_db),
):
    """Retrieve templates catalog with category filtering and keyword search."""
    query = db.query(Template)

    if category and category.lower() not in ["all", "all templates"]:
        query = query.filter(Template.category.ilike(f"%{category.strip()}%"))

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            (Template.title.ilike(term))
            | (Template.description.ilike(term))
            | (Template.formula_preview.ilike(term))
        )

    templates = query.order_by(Template.usage_count.desc()).all()
    return {"items": templates, "total": len(templates)}


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template_detail(template_id: int, db: Session = Depends(get_db)):
    """Fetch template formula and details."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template #{template_id} not found.",
        )
    return template


@router.post("/{template_id}/use")
def use_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Increment template usage counter and return pre-populated draft for Content Editor."""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template #{template_id} not found.",
        )

    template.usage_count += 1
    db.commit()

    return {
        "success": True,
        "template_id": template.id,
        "draft": {
            "title": template.title,
            "format": template.format.split("•")[0].strip() if "•" in template.format else template.format,
            "body": template.sample_body or template.formula_preview,
        },
    }
