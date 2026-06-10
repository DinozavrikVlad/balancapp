from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date as datetime_date
import models, schemas
from database import get_db
from security import get_current_user

router = APIRouter(prefix="/api/habits", tags=["Habits"])


@router.get("")
def get_habits(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_habits = db.query(models.Habit).filter(models.Habit.user_id == current_user.id).order_by(models.Habit.id).all()
    if not user_habits:
        db.add_all([
            models.Habit(name="Вода 1.5л", done=True, user_id=current_user.id),
            models.Habit(name="Медитация 10м", done=False, user_id=current_user.id),
            models.Habit(name="Чтение 15м", done=True, user_id=current_user.id),
            models.Habit(name="Спорт 30м", done=False, user_id=current_user.id)
        ])
        db.commit()
        user_habits = db.query(models.Habit).filter(models.Habit.user_id == current_user.id).order_by(
            models.Habit.id).all()

    today_str = datetime_date.today().isoformat()

    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Пакетный запрос (Bulk Query) вместо N+1
    habit_ids = [h.id for h in user_habits]
    today_logs = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id.in_(habit_ids),
        models.HabitLog.date == today_str
    ).all()
    logs_dict = {log.habit_id: log for log in today_logs}

    changed = False
    for habit in user_habits:
        log = logs_dict.get(habit.id)
        is_done_today = log.done if log else False
        if habit.done != is_done_today:
            habit.done = is_done_today
            changed = True

    if changed:
        db.commit()
    return user_habits


@router.post("")
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    new_habit = models.Habit(name=habit.name, done=False, user_id=current_user.id)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit


@router.put("/{habit_id}")
def update_habit(habit_id: int, habit_data: schemas.HabitUpdate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.user_id == current_user.id).first()
    if not habit: raise HTTPException(status_code=404, detail="Привычка не найдена")
    habit.name = habit_data.name
    db.commit()
    return habit


@router.delete("/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.user_id == current_user.id).first()
    if not habit: raise HTTPException(status_code=404, detail="Привычка не найдена")
    db.delete(habit)
    db.commit()
    return {"status": "success"}


@router.post("/{habit_id}/toggle")
def toggle_habit(habit_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.user_id == current_user.id).first()
    if not habit: raise HTTPException(status_code=404, detail="Привычка не найдена")
    habit.done = not habit.done
    today_str = datetime_date.today().isoformat()
    log = db.query(models.HabitLog).filter(models.HabitLog.habit_id == habit.id,
                                           models.HabitLog.date == today_str).first()
    if not log:
        db.add(models.HabitLog(habit_id=habit.id, date=today_str, done=habit.done))
    else:
        log.done = habit.done
    db.commit()
    db.refresh(habit)
    return habit


@router.get("/stats")
def get_habits_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # АРХИТЕКТУРНОЕ ИСПРАВЛЕНИЕ: Выполняем SQL-агрегацию на стороне СУБД для экономии памяти сервера
    results = db.query(
        models.HabitLog.date,
        func.sum(case((models.HabitLog.done == True, 1), else_=0)),
        func.count(models.HabitLog.id)
    ).join(models.Habit, models.Habit.id == models.HabitLog.habit_id) \
        .filter(models.Habit.user_id == current_user.id) \
        .group_by(models.HabitLog.date).all()

    return {
        date_str: round((done_count / total_count) * 100) if total_count > 0 else 0
        for date_str, done_count, total_count in results
    }