import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator
from pydantic.types import conset, StringConstraints
from sqlalchemy import cast, func, select, Text
from sqlalchemy.orm import joinedload, Session
from typing import Annotated, Self

from ..auth import require_admin_mode
from ..database import get_db
from ..models import blombooru_implication_implied, blombooru_implication_targets, Media, Tag, TagImplication, User 
from ..utils.cache import invalidate_tag_cache
from ..utils.logger import logger
from ..utils.tag_utils import expand_implications, resolve_implications

router = APIRouter(prefix="/api/tag-implications", tags=["tag-implications"])

class TagRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TagImplicationResponse(BaseModel):
    id: int
    target_tags: List[TagRef]
    target_tag_patterns: List[str]
    implied_tags: List[TagRef]

    class Config:
        from_attributes = True

# Ensure a lower-case string stripped from whitespace with a minimum length of 1
Tag_Or_Pattern = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)]

class TagImplicationResolveRequest(BaseModel):
    tags: conset(Tag_Or_Pattern, min_length=1)

class TagImplicationCreate(BaseModel):
    target_tags: set[Tag_Or_Pattern] = set()
    target_tag_patterns: set[Tag_Or_Pattern] = set()
    implied_tags: conset(Tag_Or_Pattern, min_length=1)

    @model_validator(mode="after")
    def validate_target_presence(self) -> Self:
        if not self.target_tags and not self.target_tag_patterns:
            raise ValueError("either 'target_tags' or 'target_tag_patterns' is required")
        return self

def _resolve_tag_names(db: Session, tag_names: set[str]) -> List[Tag]:
    """Look up Tag objects by name. Raises 400 if any tag is not found."""
    tags = []
    for name in tag_names:
        normalized = name.strip().lower()
        if not normalized:
            continue
        tag = db.query(Tag).filter(Tag.name == normalized).first()
        if not tag:
            raise HTTPException(status_code=400, detail=f"Tag not found: {normalized}")
        tags.append(tag)
    return tags

def _clean_patterns(patterns: Optional[List[str]]) -> List[str]:
    """Normalize pattern list: strip whitespace, deduplicate, drop empties."""
    if not patterns:
        return []
    seen = set()
    result = []
    for p in patterns:
        p = p.strip().lower()
        if p and p not in seen:
            seen.add(p)
            result.append(p)
    return result

@router.get("/", response_model=List[TagImplicationResponse])
async def list_implications(
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
):
    """List all tag implications."""
    implications = db.query(TagImplication).all()

    # Filter out implications where cascading tag deletion left them empty
    results = []
    for imp in implications:
        patterns = imp.target_tag_patterns or []
        has_targets = len(imp.target_tags) > 0 or len(patterns) > 0
        if not has_targets or len(imp.implied_tags) == 0:
            # Clean up orphaned implications
            db.delete(imp)
            continue
        results.append(imp)

    if len(results) != len(implications):
        db.commit()

    # Ensure target_tag_patterns is always a list in the response
    for imp in results:
        if imp.target_tag_patterns is None:
            imp.target_tag_patterns = []

    return results

@router.post("/", response_model=TagImplicationResponse, status_code=201)
async def create_implication(
    data: TagImplicationCreate,
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
):
    """Create a new tag implication."""

    target_tags = _resolve_tag_names(db, data.target_tags) if data.target_tags else []
    implied_tags = _resolve_tag_names(db, data.implied_tags)

    target_ids = [tag.id for tag in target_tags]
    implied_ids = [tag.id for tag in implied_tags]

    def matching_count_sq(table, tag_set):
        """Generate a subquery selecting the count of matching tags (target or implied) for each implication"""
        return (
            select(func.count(table.c.tag_id))
            .where(
                table.c.implication_id == TagImplication.id,
                table.c.tag_id.in_([tag.id for tag in tag_set])
            )
            .scalar_subquery()
        )

    def total_count_sq(table):
        """Generate a subquery selecting the total count of tags (target or implied) for each implication"""
        return (
            select(func.count(table.c.tag_id))
            .where(
                table.c.implication_id == TagImplication.id
            )
            .scalar_subquery()
        )

    matching_implied_count = matching_count_sq(blombooru_implication_implied, implied_tags)
    total_implied_count = total_count_sq(blombooru_implication_implied)
    matching_target_count = matching_count_sq(blombooru_implication_targets, target_tags)
    total_target_count = total_count_sq(blombooru_implication_targets)

    stmt = (
        select(TagImplication)
        .where(
            matching_implied_count == len(implied_tags), # it must contain at least the implied tags
            total_implied_count == len(implied_tags),  # but it must not contain any more then those
            matching_target_count == len(target_tags),
            total_target_count == len(target_tags),
        )
    )

    implications = db.execute(stmt).scalars().all()
    exists = any(
        set(imp.target_tag_patterns or ()) == data.target_tag_patterns
        for imp in implications
    )

    if exists:
        raise HTTPException(status_code=409, detail="Implication already exist")

    implication = TagImplication()
    implication.target_tags = target_tags
    implication.target_tag_patterns = list(data.target_tag_patterns) if data.target_tag_patterns else None
    implication.implied_tags = implied_tags

    db.add(implication)
    db.commit()
    db.refresh(implication)
    invalidate_tag_cache()

    if implication.target_tag_patterns is None:
        implication.target_tag_patterns = []

    return implication

@router.put("/{implication_id}", response_model=TagImplicationResponse)
async def update_implication(
    implication_id: int,
    data: TagImplicationCreate,
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
):
    """Update an existing tag implication."""
    implication = db.query(TagImplication).filter(TagImplication.id == implication_id).first()
    if not implication:
        raise HTTPException(status_code=404, detail="Implication not found")

    patterns = _clean_patterns(data.target_tag_patterns)

    if not data.target_tags and not patterns:
        raise HTTPException(status_code=400, detail="At least one target tag or target pattern is required")
    if not data.implied_tags:
        raise HTTPException(status_code=400, detail="At least one implied tag is required")

    target_tags = _resolve_tag_names(db, data.target_tags)
    implied_tags = _resolve_tag_names(db, data.implied_tags)

    if not implied_tags:
        raise HTTPException(status_code=400, detail="At least one implied tag is required")

    implication.target_tags = target_tags
    implication.target_tag_patterns = patterns if patterns else None
    implication.implied_tags = implied_tags

    db.commit()
    db.refresh(implication)
    invalidate_tag_cache()

    if implication.target_tag_patterns is None:
        implication.target_tag_patterns = []

    return implication

@router.delete("/{implication_id}")
async def delete_implication(
    implication_id: int,
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
):
    """Delete a tag implication."""
    implication = db.query(TagImplication).filter(TagImplication.id == implication_id).first()
    if not implication:
        raise HTTPException(status_code=404, detail="Implication not found")

    db.delete(implication)
    db.commit()
    invalidate_tag_cache()

    return {"status": "success"}

@router.post("/simulate-apply-all")
async def simulate_apply_all_implications(
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
):
    """
    Simulate applying all tag implications to all media in the database.
    Runs asynchronously in an executor to avoid blocking the event loop.
    Returns a list of affected media along with the newly implied tags.
    """
    loop = asyncio.get_event_loop()

    def do_simulate_apply_all():
        implications = db.query(TagImplication).all()
        if not implications:
            return []

        media_items = db.query(Media).options(joinedload(Media.tags)).all()
        affected_media = []

        for media in media_items:
            tag_dict = {t.id: t for t in media.tags}
            original_tag_ids = set(tag_dict.keys())
            
            expand_implications(db, tag_dict, implications=implications)
            
            new_tag_ids = set(tag_dict.keys()) - original_tag_ids
            if new_tag_ids:
                added_tags = [tag_dict[tid].name for tid in new_tag_ids]
                affected_media.append({
                    "media_id": media.id,
                    "added_tags": added_tags
                })

        return affected_media

    affected_media = await loop.run_in_executor(None, do_simulate_apply_all)
    return {"affected_media": affected_media}

@router.post("/resolve")
async def implications_for(
    request: TagImplicationResolveRequest,
    current_user: User = Depends(require_admin_mode),
    db: Session = Depends(get_db)
) -> dict:
    """Resolve and return all implied tags for the given a tag set."""

    implied_tags = resolve_implications(db, request.tags)
    return {"tags": implied_tags}