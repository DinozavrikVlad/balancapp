from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
from database import get_db
from security import get_current_user

router = APIRouter(tags=["Finances"])

@router.get("/api/budget")
def get_budget(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    total_spent = db.query(models.Transaction).filter(models.Transaction.amount > 0, models.Transaction.user_id == current_user.id).all()
    return {
        "monthly": current_user.monthly_budget,
        "dailyLimit": current_user.daily_limit,
        "spentToday": float(sum([t.amount for t in total_spent]))
    }

@router.put("/api/budget")
def update_budget(budget: schemas.BudgetUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.monthly_budget = budget.monthly_budget
    current_user.daily_limit = budget.daily_limit
    db.commit()
    return {"status": "success"}

@router.get("/api/categories")
def get_categories(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cats = db.query(models.Category).filter(models.Category.user_id == current_user.id).order_by(models.Category.id).all()
    if not cats:
        default_cats = ["🍎 Продукты", "🚕 Транспорт", "☕ Кафе", "🎬 Развлечения", "📦 Разное"]
        db.add_all([models.Category(name=c, user_id=current_user.id) for c in default_cats])
        db.commit()
        cats = db.query(models.Category).filter(models.Category.user_id == current_user.id).order_by(models.Category.id).all()
    return cats

@router.post("/api/categories")
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_cat = models.Category(name=cat.name, user_id=current_user.id)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.delete("/api/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    cat = db.query(models.Category).filter(models.Category.id == cat_id, models.Category.user_id == current_user.id).first()
    if not cat: raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(cat)
    db.commit()
    return {"status": "success"}

@router.get("/api/transactions")
def get_transactions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).order_by(models.Transaction.id.desc()).all()

@router.get("/api/transactions/summary")
def get_transactions_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    results = db.query(models.Transaction.category, func.sum(models.Transaction.amount)).filter(models.Transaction.user_id == current_user.id).group_by(models.Transaction.category).all()
    return {category: float(amount) for category, amount in results}

# ИСПРАВЛЕНО: @app.post заменено на @router.post
@router.post("/api/transactions")
def add_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_tx = models.Transaction(amount=tx.amount, category=tx.category, user_id=current_user.id)
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx

@router.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id, models.Transaction.user_id == current_user.id).first()
    if not tx: raise HTTPException(status_code=404, detail="Транзакция не найдена")
    db.delete(tx)
    db.commit()
    return {"status": "success"}