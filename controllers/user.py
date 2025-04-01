from flask import render_template, session, redirect, url_for, Blueprint,request,flash
from flask_login import current_user, login_required
from models.user import User
from models.quiz import Quiz, Question,QuizAttempt, QuizAnswer
from models.score import Score
from extensions import db, login_manager
from datetime import datetime
from .decorators import user_required

user_bp = Blueprint('user', __name__)

# @login_manager.user_loader
# def load_user(user_id):
#     user = User.query.get(int(user_id))
#     return user


@user_bp.route('/dashboard')
@login_required
@user_required  # ✅ Ensures user must be logged in
def dashboard():
    try:
        user = User.query.get(current_user.id)  # Ensure you are getting the full user object

        if not user:
            flash("User not found!", "danger")
            return redirect(url_for("auth.user_login"))  # Redirect if user doesn't exist

        quizzes = Quiz.query.all()
        scores = Score.query.filter_by(user_id=current_user.id).all()
        score_data = [(score, score.quiz.max_marks) for score in scores]

        print(f"User Data: {user.__dict__}")  # Debugging to check if `created_at` exists
        print(f"Score Data: {score_data}")

        return render_template('users/user_dashboard.html', user=user, quizzes=quizzes, scores=score_data)

    except Exception as e:
        print(f"Error: {str(e)}")
        flash("An error occurred while loading the dashboard.", "danger")
        return redirect(url_for("auth.user_login"))

# 📝 Route for Attempt Quiz
@user_bp.route('/quiz/<int:quiz_id>/attempt', methods=['GET', 'POST'])
@login_required
@user_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.active:
        flash("This quiz is inactive and cannot be attempted.", "danger")
        return redirect(url_for('user.dashboard'))
    
    # Load questions for this quiz
    questions = quiz.questions  # This gets the questions from the many-to-many relationship

    # ❌ Prevent re-attempt if already submitted
    attempt = QuizAttempt.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).first()
    if attempt and attempt.submitted_at:
        flash("You have already completed this quiz.", "warning")
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        selected_options = request.form.to_dict()
        attempt = attempt or QuizAttempt(user_id=current_user.id, quiz_id=quiz.id, started_at=datetime.utcnow())
        db.session.add(attempt)
        db.session.commit()

        # ✅ Store user answers & correctness
        for question_id, selected_option in selected_options.items():
            if question_id.isdigit():  # Make sure it's a question ID
                question = Question.query.get(int(question_id))
                if question:
                    is_correct = (selected_option == question.correct_option)
                    answer = QuizAnswer(attempt_id=attempt.id, question_id=question.id, 
                                       selected_option=selected_option, is_correct=is_correct)
                    db.session.add(answer)

        # ✅ Calculate score
        db.session.commit()
        correct_answers = QuizAnswer.query.filter_by(attempt_id=attempt.id, is_correct=True).count()
        total_questions = QuizAnswer.query.filter_by(attempt_id=attempt.id).count()
        
        score = Score(
            quiz_id=quiz.id,
            user_id=current_user.id,
            total_score=correct_answers,
            attempted_at=datetime.utcnow()
        )
        db.session.add(score)
        
        attempt.submitted_at = datetime.utcnow()
        db.session.commit()

        flash("Quiz submitted successfully!", "success")
        return redirect(url_for('user.quiz_result', attempt_id=attempt.id))

    return render_template('users/attempt_quiz.html', quiz=quiz, attempt=attempt)

# ✅ Show available quizzes
@user_bp.route('/available-quizzes')
@login_required
@user_required
def available_quizzes():
    quizzes = Quiz.query.all()  # Fetch all available quizzes
    return render_template('available_quizzes.html', quizzes=quizzes)


@user_bp.route('/quiz_result/<int:attempt_id>')
@login_required
@user_required
def quiz_result(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    # ❌ Prevent access to others' results
    if attempt.user_id != current_user.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('user.dashboard'))

    user_answers = QuizAnswer.query.filter_by(attempt_id=attempt.id).all()
    correct_answers = {ans.question_id: ans.question.correct_option for ans in user_answers}

    correct_count = sum(1 for ans in user_answers if ans.selected_option == correct_answers[ans.question_id])
    total_questions = len(user_answers)
    score_percentage = (correct_count / total_questions) * 100 if total_questions else 0

    return render_template('users/quiz_result.html', attempt=attempt, score=score_percentage, user_answers=user_answers)

# 📊 Dummy route for My Scores
@user_bp.route('/scores')
@login_required
@user_required
def scores():
    user_scores = Score.query.filter_by(user_id=current_user.id).join(Quiz).add_columns(
        Quiz.name.label('quiz_name'),
        Score.total_score,
        Score.attempted_at
    ).order_by(Score.attempted_at.desc()).all()

    return render_template('users/user_scores.html', user_scores=user_scores)
