from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware

from app.dependencies import Base, engine, get_db
from app.routers.quizzes import router as quiz_router
from app.routers.auth import router as auth_router, get_current_user

app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8000",
    "http://172.20.10.3:8000",
    "http://localhost:3000",
    "http://172.20.10.3:3000",
    "http://172.20.10.3:3000/*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quiz_router, prefix='/api/v1/quizzes', tags=['Quizzes and Questions'])
app.include_router(auth_router, prefix='/api/v1/auth', tags=['Authentication'])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



def create_tables():
    Base.metadata.create_all(bind=engine)

@app.get("/user", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Auth failed")
    return {'user': user}


if __name__ == "__main__":
    create_tables()
    uvicorn.run(app, host="localhost", port=8001)


