from typing import List, Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..dependencies import get_db

from .. import schemas, models
from ..models import Quiz, Question, Answer, UserQuiz, User
from ..schemas import QuizDescription, UserInfo, QuizResults

router = APIRouter()

user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get('', response_model=List[schemas.QuizBase])
def get_quizzes(db: Session = Depends(get_db), user_id: int = None):
    try:
        quizzes = db.query(Quiz).outerjoin(UserQuiz, (UserQuiz.quiz_id == Quiz.id) & (UserQuiz.user_id == user_id)) \
            .filter((UserQuiz.user_id == None) | (UserQuiz.completed.is_(False))).distinct().all()
        result = []
        for quiz in quizzes:
            question_count = len(quiz.questions)  # Calculate number of questions
            quiz_info = schemas.QuizBase(
                id=quiz.id,
                title=quiz.title,
                question_count=question_count
            )
            result.append(quiz_info)
        return result
    except HTTPException as e:
        return {'error': e}


@router.post('', response_model=schemas.QuizBase)
def create_quiz(quiz: schemas.QuizBaseCreate, db: Session = Depends(get_db)):
    db_quiz = Quiz(title=quiz.title)
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)

    return db_quiz


@router.get('/{quiz_id}', response_model=schemas.Quiz)
def get_quiz(quiz_id: UUID, db: Session = Depends(get_db)):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        return quiz
    except HTTPException as e:
        return {'error': e}


@router.post('/{quiz_id}/complete', status_code=200)
def complete_quiz(quiz_id: UUID, result: schemas.QuizResult, db: Session = Depends(get_db)):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        existing_entry = db.query(UserQuiz).filter_by(user_id=result.user_id, quiz_id=quiz_id).first()
        if existing_entry:
            existing_entry.completed = True
            existing_entry.score = result.score
        else:
            new_user_quiz = UserQuiz(user_id=result.user_id, quiz_id=quiz_id, completed=True, score=result.score)
            db.add(new_user_quiz)
        db.commit()
        return {"message": "Quiz completed successfully", "score": result.score}
    except HTTPException as e:
        return {'error': e}


@router.put('/{quiz_id}', response_model=schemas.Quiz)
def update_quiz_description(quiz_id: UUID, qd: schemas.QuizDescription, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz.description = qd.description
    quiz.time_for_test = qd.time_for_test
    db.commit()
    return quiz


@router.post('/{quiz_id}/questions', response_model=schemas.Question)
def create_questions(quiz_id: UUID, question: schemas.QuestionBase, db: Session = Depends(get_db)):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        new_question = Question(
            text=question.text,
            image_url=question.image_url,
            quiz_id=quiz_id
        )
        db.add(new_question)
        db.commit()
        db.refresh(new_question)

        return new_question
    except HTTPException as e:
        return {'error': e}


@router.delete('/{quiz_id}/questions/{question_id}', status_code=200)
def delete_questions(quiz_id: UUID, question_id: UUID, db: Session = Depends(get_db)):
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        db.delete(question)
        db.commit()

        return {'message': 'Question and its answers successfully deleted'}
    except HTTPException as e:
        return {'error': e}


@router.post('/{quiz_id}/questions/{question_id}/answers', response_model=schemas.Answer, status_code=201)
def create_answer(quiz_id: UUID, question_id: UUID, answer_data: schemas.AnswerBase, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    new_answer = Answer(
        text=answer_data.text,
        is_correct=answer_data.is_correct,
        question_id=question_id
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return new_answer


@router.get('/{quiz_id}/questions/{question_id}/answers', response_model=List[schemas.AnswerBase])
def get_answers(quiz_id: UUID, question_id: UUID, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    return answers


@router.get('/{quiz_id}/results', response_model=QuizResults)
def get_quiz_results(quiz_id: UUID, db: Session = Depends(get_db)):
    # Check if the quiz exists
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Fetch all UserQuiz records where the quiz is completed
    results = db.query(UserQuiz).join(User).filter(UserQuiz.quiz_id == quiz_id, UserQuiz.completed == True).all()

    participants = [UserInfo(
        id=user_quiz.user.id,
        name=user_quiz.user.name,
        surname=user_quiz.user.surname,
        thirdname=user_quiz.user.thirdname,
        score=user_quiz.score,
        completed=user_quiz.completed
    ) for user_quiz in results]

    return QuizResults(
        quiz_id=quiz.id,
        title=quiz.title,
        participants=participants
    )