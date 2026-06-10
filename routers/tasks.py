from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as datetime_date
import uuid
import models, schemas
from database import get_db
from security import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("")
def get_tasks(date: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not date: date = datetime_date.today().isoformat()
    return db.query(models.Task).filter(models.Task.user_id == current_user.id, models.Task.date == date).order_by(
        models.Task.id).all()


@router.post("")
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    series_id = uuid.uuid4().hex if len(task.dates) > 1 else None

    # ОПТИМИЗАЦИЯ СУБД: Пакетное разжалование прошлых фокус-задач за одну SQL-операцию
    if task.type == "focus":
        db.query(models.Task).filter(
            models.Task.type == "focus",
            models.Task.user_id == current_user.id,
            models.Task.date.in_(task.dates)
        ).update({"type": "routine"}, synchronize_session=False)

    # ОПТИМИЗАЦИЯ СУБД: Групповая вставка (Bulk Insert) за одно подключение
    new_tasks = [
        models.Task(
            name=task.name,
            type=task.type,
            done=False,
            date=current_date,
            series_id=series_id,
            user_id=current_user.id
        ) for current_date in task.dates
    ]

    db.add_all(new_tasks)
    db.commit()
    return {"status": "success", "created_count": len(new_tasks)}


@router.post("/{task_id}/toggle")
def toggle_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task: raise HTTPException(status_code=404, detail="Задача не найдена")
    task.done = not task.done
    db.commit()
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, delete_series: bool = False, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user.id).first()
    if not task: raise HTTPException(status_code=404, detail="Задача не найдена")

    if delete_series and task.series_id:
        db.query(models.Task).filter(models.Task.series_id == task.series_id,
                                     models.Task.user_id == current_user.id).delete()
    else:
        db.delete(task)

    db.commit()
    return {"status": "success"}