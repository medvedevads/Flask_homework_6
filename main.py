# Задание №2
# Создать веб-приложение на FastAPI, которое будет предоставлять API для
# работы с базой данных пользователей. Пользователь должен иметь
# следующие поля:
# ○ ID (автоматически генерируется при создании пользователя)
# ○ Имя (строка, не менее 2 символов)
# ○ Фамилия (строка, не менее 2 символов)
# ○ Дата рождения (строка в формате "YYYY-MM-DD")
# ○ Email (строка, валидный email)
# ○ Адрес (строка, не менее 5 символов)
# API должен поддерживать следующие операции:
# ○ Добавление пользователя в базу данных
# ○ Получение списка всех пользователей в базе данных
# ○ Получение пользователя по ID
# ○ Обновление пользователя по ID
# ○ Удаление пользователя по ID
# Приложение должно использовать базу данных SQLite3 для хранения пользователей.

from fastapi import FastAPI
import sqlalchemy
from pydantic import BaseModel, Field, EmailStr
import uvicorn
from typing import List
import databases
from datetime import datetime, date


DATABASE_URL = "sqlite:///users_data.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String(32)),
    sqlalchemy.Column("surname", sqlalchemy.String(32)),
    sqlalchemy.Column("birthday", sqlalchemy.Date),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("address", sqlalchemy.String(150)),
)

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


class User(BaseModel):
    username: str = Field(title="Username", min_length=2)
    surname: str = Field(title="Surname", min_length=2)
    birthday: date = Field(title="Birthday")
    email: EmailStr = Field(title="Email", max_length=128)
    address: str = Field(title="Address", min_length=5)


class User_with_ID(User):
    user_id: int = Field(title="ID")


@app.get("/fake_users/{count}")
async def create_note(count: int):
    for i in range(1, count + 1):
        query = users.insert().values(
            username=f"user{i}", surname=f"surname_user{i}",
            birthday=datetime.now(), email=f"mail{i}@mail.ru", address=f"city{i}")
        await database.execute(query)
    return {"message": f"{count} fake users create"}


@app.post("/users/", response_model=User_with_ID)
async def create_user(user: User):
    query = users.insert().values(
        username=user.username, surname=user.surname, birthday=user.birthday,
        email=user.email, address=user.address)
    last_record_id = await database.execute(query)
    return {**user.model_dump(), "user_id": last_record_id}


@app.get("/users/{user_id}", response_model=User_with_ID)
async def get_user(user_id: int):
    query = users.select().where(users.c.user_id == user_id)
    return await database.fetch_one(query)


@app.get("/users/", response_model=List[User_with_ID])
async def get_users():
    query = users.select()
    return await database.fetch_all(query)


@app.put("/users/{user_id}", response_model=User_with_ID)
async def update_user(user_id: int, new_user: User):
    query = users.update().where(
        users.c.user_id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "user_id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.user_id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)