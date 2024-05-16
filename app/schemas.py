from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class UserInfo(BaseModel):
    id: int
    name: Optional[str]
    surname: Optional[str]
    thirdname: Optional[str]
    score: Optional[int]


class QuizResults(BaseModel):
    quiz_id: UUID
    title: str
    participants: List[UserInfo]
class AnswerBase(BaseModel):
    text: str
    is_correct: bool


class AnswerCreate(AnswerBase):
    pass


class Answer(AnswerBase):
    id: UUID
    question_id: UUID

    class Config:
        orm_mode = True


class QuestionBase(BaseModel):
    text: Optional[str] = None  # Text can be None if there is an image
    image_url: Optional[str] = None  # URL to the image

class QuizResult(BaseModel):
    score: Optional[int] = None
    user_id: Optional[int] = None

class QuestionCreate(QuestionBase):
    answers: List[AnswerCreate]


class Question(QuestionBase):
    id: UUID
    quiz_id: UUID
    answers: List[Answer]

    class Config:
        orm_mode = True


class QuizBase(BaseModel):
    id: UUID
    title: str
    question_count: Optional[int] = Field(0, description="The number of questions in the quiz")
    time_for_test: Optional[int] = None
class QuizBaseCreate(BaseModel):
    title:str


class QuizCreate(QuizBase):
    questions: List[QuestionCreate]

class QuizDescription(BaseModel):
    description: Optional[str] = None
    time_for_test: Optional[int] = None
class Quiz(QuizBase):
    id: UUID
    title: str
    description: Optional[str] = None
    questions: List[Question]
    time_for_test: Optional[int] = None

    class Config:
        orm_mode = True
