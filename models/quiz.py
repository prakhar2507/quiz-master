from extensions import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

# ✅ Many-to-Many Association Table for Quiz-Question Relationship
# ✅ Many-to-Many: Quiz <-> Questions
quiz_questions = db.Table(
    'quiz_questions',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True)
)

# 🟢 SUBJECT TABLE
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    chapters = db.relationship('Chapter', back_populates='subject', cascade='all, delete-orphan')


# 🟢 CHAPTER TABLE
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.Integer, nullable=False)

    subject = db.relationship('Subject', back_populates='chapters')
    quizzes = db.relationship('Quiz', back_populates='chapter', cascade='all, delete-orphan', passive_deletes=True)  # ✅ FIXED
    questions = db.relationship('Question', back_populates='chapter', cascade='all, delete-orphan', passive_deletes=True)


# 🟢 QUIZ TABLE
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))  # Optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    max_marks = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=False)

    # ✅ Chapter relationship
    chapter = db.relationship('Chapter', back_populates='quizzes')

    # ✅ Many-to-Many: Quiz <-> Questions
    questions = db.relationship('Question', secondary=quiz_questions, back_populates='quizzes')

    # ✅ One-to-Many: Quiz <-> Scores (FIXED)
    scores = db.relationship("Score", back_populates="quiz", lazy="dynamic")  # Removed backref

    # ✅ One-to-Many: Quiz <-> Attempts
    quiz_attempts = db.relationship("QuizAttempt", back_populates="quiz", lazy="dynamic")



# 🟢 QUESTION TABLE
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

    # Relationship: A question can belong to multiple quizzes
    quizzes = db.relationship('Quiz', secondary=quiz_questions, back_populates='questions')

    # ✅ ADD CHAPTER RELATIONSHIP
    chapter = db.relationship('Chapter', back_populates='questions')
    quiz_answers = db.relationship('QuizAnswer', back_populates='question', lazy=True)


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete='CASCADE'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)  # Stores when the user submits the quiz

    # Change from backref to back_populates to match the User model
    user = db.relationship('User', back_populates='quiz_attempts')
    quiz = db.relationship('Quiz', back_populates='quiz_attempts')
    answers = db.relationship('QuizAnswer', back_populates='attempt')
    __table_args__ = (UniqueConstraint('user_id', 'quiz_id', name='unique_user_quiz_attempt'),)



class QuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)  # Stores 'A', 'B', 'C', or 'D'
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    attempt = db.relationship('QuizAttempt', back_populates='answers')
    question = db.relationship('Question', back_populates='quiz_answers')
