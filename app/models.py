import uuid

from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.dependencies import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True)
    hashed_password = Column(String)
    name = Column(String, nullable=True)
    surname = Column(String, nullable=True)
    thirdname = Column(String, nullable=True)
    dateOfBirth = Column(Date, nullable=True)
    is_admin = Column(Boolean, default=False)
    quizzes = relationship("UserQuiz", back_populates="user")


class Quiz(Base):
    __tablename__ = 'quizzes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, index=True, unique=True)
    questions = relationship("Question", back_populates="quiz")
    description = Column(String, index=True)
    time_for_test = Column(Integer, default=0)
    users = relationship("UserQuiz", back_populates="quiz")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey('quizzes.id'))
    answers = relationship("Answer", back_populates="question", cascade='all, delete-orphan')
    quiz = relationship("Quiz", back_populates="questions")


class Answer(Base):
    __tablename__ = 'answers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(String)
    is_correct = Column(Boolean)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    question = relationship("Question", back_populates="answers")


class UserQuiz(Base):
    __tablename__ = 'user_quizzes'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey('quizzes.id'), primary_key=True)
    completed = Column(Boolean, default=False, nullable=False)
    score = Column(Integer)


    user = relationship("User", back_populates="quizzes")
    quiz = relationship("Quiz", back_populates="users")