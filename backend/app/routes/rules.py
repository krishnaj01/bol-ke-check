from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app import rules_engine
from app.models import CATEGORIES

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@router.get("")
def get_rules(category: Annotated[str, Query()] = "general") -> dict:
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"category must be one of {CATEGORIES}")
    return {
        "category": category,
        "families": rules_engine.FAMILIES,
        "disclosure": rules_engine.disclosure_spec().model_dump(),
        "rules": [rule.model_dump() for rule in rules_engine.rules_for(category)],
    }
