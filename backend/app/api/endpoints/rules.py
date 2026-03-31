from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.rule import CustomRule
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse
import yaml

router = APIRouter()


@router.get("", response_model=List[RuleResponse])
async def get_rules(
    skip: int = 0,
    limit: int = 100,
    enabled: Optional[bool] = None,
    severity: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(CustomRule).order_by(CustomRule.created_at.desc())

    if enabled is not None:
        query = query.where(CustomRule.enabled == enabled)
    if severity:
        query = query.where(CustomRule.severity == severity)
    if language:
        query = query.where(CustomRule.language == language)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rules = result.scalars().all()

    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomRule).where(CustomRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("", response_model=RuleResponse)
async def create_rule(rule_data: RuleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(CustomRule).where(CustomRule.rule_id == rule_data.rule_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Rule ID already exists")

    rule = CustomRule(**rule_data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CustomRule).where(CustomRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = rule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomRule).where(CustomRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted"}


@router.post("/import")
async def import_rules(rules_yaml: str, db: AsyncSession = Depends(get_db)):
    try:
        rules_data = yaml.safe_load(rules_yaml)
        if not isinstance(rules_data, list):
            rules_data = [rules_data]

        imported = []
        for rule_data in rules_data:
            existing = await db.execute(
                select(CustomRule).where(CustomRule.rule_id == rule_data.get('id', ''))
            )
            if existing.scalar_one_or_none():
                continue

            rule = CustomRule(
                rule_id=rule_data['id'],
                name=rule_data['name'],
                severity=rule_data.get('severity', 'medium'),
                language=rule_data.get('language'),
                pattern=rule_data['pattern'],
                message=rule_data['message'],
                enabled=rule_data.get('enabled', True)
            )
            db.add(rule)
            imported.append(rule)

        await db.commit()
        return {"imported": len(imported)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")


@router.get("/export")
async def export_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomRule).where(CustomRule.enabled == True))
    rules = result.scalars().all()

    rules_data = []
    for rule in rules:
        rules_data.append({
            'id': rule.rule_id,
            'name': rule.name,
            'severity': rule.severity,
            'language': rule.language,
            'pattern': rule.pattern,
            'message': rule.message,
            'enabled': rule.enabled
        })

    return yaml.dump(rules_data, allow_unicode=True, sort_keys=False)
