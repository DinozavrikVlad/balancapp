from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import models
from database import engine

# Импортируем наши новые модули
from routers import auth, habits, finances, tasks

# Загружаем переменные окружения
load_dotenv()

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Баланс API")

# Подключаем роутеры к основному приложению
app.include_router(auth.router)
app.include_router(auth.users_router)
app.include_router(habits.router)
app.include_router(finances.router)
app.include_router(tasks.router)

# Раздача фронтенда (всегда в самом конце!)
app.mount("/", StaticFiles(directory="public", html=True), name="public")