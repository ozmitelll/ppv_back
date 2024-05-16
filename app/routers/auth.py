from datetime import timedelta, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from app.dependencies import get_db
from app.models import User

router = APIRouter()

SECRET_KEY = '12312ecxzarw423cxzzw343252vcxvxcafas32432'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='api/v1/auth/token')


class CreateUserRequest(BaseModel):
    login: str
    name: str
    surname: str
    thirdname: str
    dateOfBirth: datetime
    password: str


class LoginForm(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


db_dependency = Annotated[Session, Depends(get_db)]


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = User(
        login=create_user_request.login,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        name=create_user_request.name,
        surname=create_user_request.surname,
        thirdname=create_user_request.thirdname,
        dateOfBirth=create_user_request.dateOfBirth
    )
    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: LoginForm, db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect credentials user.")
    token = create_access_token(user.login, user.name, user.surname,
                                user.thirdname, user.dateOfBirth,
                                user.id, user.is_admin,
                                timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(login: str, password: str, db):
    user = db.query(User).filter(User.login == login).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(login: str, name: str,
                        surname: str,
                        thirdname: str,
                        dateOfBirth: datetime,
                        user_id: int,
                        user_is_admin: bool,
                        expires_delta: timedelta):
    date_of_birth_str = dateOfBirth.isoformat()

    # Prepare the payload with all required fields
    payload = {
        'sub': login,
        'id': user_id,
        'name': name,
        'surname': surname,
        'thirdname': thirdname,
        'dateOfBirth': date_of_birth_str,
        'is_admin': user_is_admin,
        'exp': datetime.utcnow() + expires_delta
    }
    expires = datetime.utcnow() + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')
        name: str = payload.get('name')
        surname: str = payload.get('surname')
        thirdname: str = payload.get('thirdname')
        dateOfBirth: str = payload.get('dateOfBirth')
        is_admin: bool = payload.get('is_admin')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate credentials.')
        return {'username': username, 'user_id': user_id, 'name': name, 'surname': surname, 'thirdname': thirdname,
                'dateOfBirth': dateOfBirth, 'is_admin':is_admin}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
