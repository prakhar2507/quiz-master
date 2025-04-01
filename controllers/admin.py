from flask import jsonify, Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from models.admin import Admin
from models.user import User
from models.score import Score
from models.quiz import Quiz, Chapter, Subject, Question, QuizAttempt, QuizAnswer
from extensions import db, login_manager
from .decorators import admin_required

admin_bp = Blueprint('admin', __name__)

# ---------------------- Dashboard ----------------------
@admin_bp.route('/admin-dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).limit(8).all()
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_quizzes = Quiz.query.filter_by(active=True).count()

    latest_quizzes = Quiz.query.order_by(Quiz.created_at.desc()).limit(5).all()

    quiz_attempt_counts = {
        quiz.id: QuizAttempt.query.filter_by(quiz_id=quiz.id).count()
        for quiz in latest_quizzes
    }

    return render_template(
        'admin/admin_dashboard.html',
        users=users,
        total_users=total_users,
        active_users=active_users,
        total_quizzes=total_quizzes,
        latest_quizzes=latest_quizzes,
        quiz_attempt_counts=quiz_attempt_counts
    )

# ---------------------- Users Management ----------------------
@admin_bp.route('/admin/users')
@login_required
@admin_required
def manage_users():
    return render_template('admin/manage_users.html', users=User.query.all())

@admin_bp.route('/admin/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        email, password, full_name = request.form.get('email'), request.form.get('password'), request.form.get('full_name')
        qualification, dob = request.form.get('qualification'), request.form.get('dob')

        if not email or not password or not full_name:
            flash('Email, Password, and Full Name are required!', 'danger')
            return redirect(url_for('admin.manage_users'))

        new_user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            qualification=qualification,
            dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        user.full_name = request.form.get('full_name').strip()
        user.email = request.form.get('email').strip()
        user.qualification = request.form.get('qualification').strip()
        user.dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d") if request.form.get('dob') else None

        # Update password if a new one is provided
        new_password = request.form.get('password')
        if new_password:  
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("User updated successfully!", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        # Delete all related scores first
        Score.query.filter_by(user_id=user.id).delete()
        
        # Delete quiz attempts and their answers
        attempts = QuizAttempt.query.filter_by(user_id=user.id).all()
        for attempt in attempts:
            QuizAnswer.query.filter_by(attempt_id=attempt.id).delete()
        QuizAttempt.query.filter_by(user_id=user.id).delete()
        
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Deletion failed: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_users'))

# ---------------------- Subjects Management ----------------------
@admin_bp.route('/admin/manage_subjects', methods=['GET'])
@login_required
@admin_required
def manage_subjects():
    return render_template('admin/manage_subjects.html', subjects=Subject.query.all())

@admin_bp.route('/admin/add_subject', methods=['POST'])
@login_required
@admin_required
def add_subject():
    subject_name = request.form.get('subject_name').strip()
    
    if Subject.query.filter_by(name=subject_name).first():
        flash(f"Subject '{subject_name}' already exists!", "danger")
    else:
        db.session.add(Subject(name=subject_name))
        db.session.commit()
        flash("Subject added successfully!", "success")

    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/admin/edit_subject/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    try:
        subject = Subject.query.get_or_404(subject_id)
        new_name = request.form.get('subject_name').strip()

        # Ensure unique subject name
        if Subject.query.filter(Subject.id != subject_id, Subject.name == new_name).first():
            flash(f"Subject '{new_name}' already exists!", "danger")
        else:
            subject.name = new_name
            db.session.commit()
            flash("Subject updated successfully!", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    try:
        subject = Subject.query.get_or_404(subject_id)
        
        # Handle all related chapters
        for chapter in subject.chapters:
            # Handle quizzes in chapter
            for quiz in chapter.quizzes:
                # Delete related scores
                Score.query.filter_by(quiz_id=quiz.id).delete()
                # Delete attempts and answers
                attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
                for attempt in attempts:
                    QuizAnswer.query.filter_by(attempt_id=attempt.id).delete()
                QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
                # Clear quiz-question relationships
                quiz.questions = []
            
            # Delete chapter questions and answers
            for question in chapter.questions:
                QuizAnswer.query.filter_by(question_id=question.id).delete()
        
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    return redirect(url_for('admin.manage_subjects'))

# ---------------------- Chapters Management ----------------------
@admin_bp.route('/admin/manage_chapters/<int:subject_id>', methods=['GET'])
@login_required
@admin_required
def manage_chapters(subject_id):
    return render_template('admin/manage_chapters.html', subject=Subject.query.get_or_404(subject_id), chapters=Chapter.query.filter_by(subject_id=subject_id).all())

@admin_bp.route('/admin/manage_chapters/<int:subject_id>/add', methods=['POST'])
@login_required
@admin_required
def add_chapter(subject_id):
    chapter_name = request.form.get('chapter_name', '').strip()
    if chapter_name:
        last_chapter = Chapter.query.filter_by(subject_id=subject_id).order_by(Chapter.number.desc()).first()
        db.session.add(Chapter(name=chapter_name, subject_id=subject_id, number=(last_chapter.number + 1) if last_chapter else 1))
        db.session.commit()
        flash("Chapter added successfully!", "success")
    else:
        flash("Chapter name is required!", "danger")

    return redirect(url_for('admin.manage_chapters', subject_id=subject_id))

@admin_bp.route('/admin/edit_chapter/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def edit_chapter(chapter_id):
    try:
        chapter = Chapter.query.get_or_404(chapter_id)
        new_name = request.form.get('chapter_name').strip()
        new_number = request.form.get('chapter_number')

        # Ensure unique chapter name in the same subject
        if Chapter.query.filter(Chapter.id != chapter_id, Chapter.name == new_name, Chapter.subject_id == chapter.subject_id).first():
            flash("A chapter with this name already exists in this subject!", "danger")
        else:
            chapter.name = new_name
            chapter.number = int(new_number) if new_number else chapter.number
            db.session.commit()
            flash("Chapter updated successfully!", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.manage_chapters', subject_id=chapter.subject_id))

@admin_bp.route('/get_chapters/<int:subject_id>', methods=['GET'])
@login_required
@admin_required
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify({
        'chapters': [{'id': chapter.id, 'name': chapter.name} for chapter in chapters]
    })

@admin_bp.route('/admin/delete_chapter/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def delete_chapter(chapter_id):
    try:
        chapter = Chapter.query.get_or_404(chapter_id)
        subject_id = chapter.subject_id
        
        # Handle quizzes in chapter
        for quiz in chapter.quizzes:
            # Delete related scores
            Score.query.filter_by(quiz_id=quiz.id).delete()
            # Delete attempts and answers
            attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
            for attempt in attempts:
                QuizAnswer.query.filter_by(attempt_id=attempt.id).delete()
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            # Clear quiz-question relationships
            quiz.questions = []
        
        # Handle chapter questions
        for question in chapter.questions:
            # Remove from quizzes first
            question.quizzes = []
            # Delete related answers
            QuizAnswer.query.filter_by(question_id=question.id).delete()
        
        db.session.delete(chapter)
        db.session.commit()
        flash("Chapter deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    return redirect(url_for('admin.manage_chapters', subject_id=subject_id))

# ---------------------- Questions Management ----------------------
@admin_bp.route('/admin/manage_questions/<int:subject_id>/<int:chapter_id>', methods=['GET'])
@login_required
@admin_required
def manage_questions(subject_id, chapter_id):
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    questions = Question.query.filter_by(chapter_id=chapter_id).all()
    
    return render_template('admin/manage_questions.html', subject=subject, chapter=chapter, questions=questions)

@admin_bp.route('/admin/add_question/<int:subject_id>/<int:chapter_id>', methods=['POST'])
@login_required
@admin_required
def add_question(subject_id, chapter_id):
    try:
        question_text = request.form.get('question_text', '').strip()
        option_a, option_b = request.form.get('option_a').strip(), request.form.get('option_b').strip()
        option_c, option_d = request.form.get('option_c').strip(), request.form.get('option_d').strip()
        correct_answer = request.form.get('correct_option').strip()

        # print(question_text, option_a, option_b, option_c, option_d, correct_answer)
        
        # Validate input
        if not question_text or not correct_answer:
            flash("Question text and correct answer are required!", "danger")
            return redirect(url_for('admin.manage_questions', subject_id=subject_id, chapter_id=chapter_id))

        # Check for duplicate questions in the same chapter
        existing_question = Question.query.filter_by(chapter_id=chapter_id, question_text=question_text).first()
        if existing_question:
            flash("This question already exists in the chapter!", "danger")
            return redirect(url_for('admin.manage_questions', subject_id=subject_id, chapter_id=chapter_id))

        # Create and save the question
        new_question = Question(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b, 
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_answer,
            chapter_id=chapter_id
        )

        db.session.add(new_question)
        db.session.commit()
        print("Question added successfully to the database")
        flash("Question added successfully!", "success")

    except Exception as e:
        db.session.rollback()
        # print(f"Error: {str(e)}")
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.manage_questions', subject_id=subject_id, chapter_id=chapter_id))

@admin_bp.route('/admin/edit_question/<int:question_id>', methods=['POST'])
@login_required
@admin_required
def edit_question(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        question.question_text = request.form.get('question_text').strip()
        question.option_a = request.form.get('option_a').strip()
        question.option_b = request.form.get('option_b').strip()
        question.option_c = request.form.get('option_c').strip()
        question.option_d = request.form.get('option_d').strip()
        question.correct_option = request.form.get('correct_option').strip()
        
        db.session.commit()
        flash("Question updated successfully!", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.manage_questions', subject_id=question.chapter.subject_id, chapter_id=question.chapter_id))

@admin_bp.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    try:
        question = Question.query.get_or_404(question_id)
        subject_id = question.chapter.subject_id
        chapter_id = question.chapter_id
        
        # Remove from all quizzes first
        question.quizzes = []
        
        # Delete related answers
        QuizAnswer.query.filter_by(question_id=question.id).delete()
        
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    return redirect(url_for('admin.manage_questions', subject_id=subject_id, chapter_id=chapter_id))
# ---------------------- Quiz Management ----------------------
@admin_bp.route('/admin/manage_quizzes')
@login_required
@admin_required
def manage_quizzes():
    return render_template("admin/manage_quizzes.html", quizzes=Quiz.query.all(), subjects=Subject.query.all())

@admin_bp.route('/admin/add_quiz', methods=['POST'])
@login_required
@admin_required
def add_quiz():
    try:
        name, subject_id, chapter_id = request.form.get('name'), int(request.form.get('subject_id')), int(request.form.get('chapter_id'))
        start_time, end_time, duration, total_marks = request.form.get('start_time'), request.form.get('end_time'), request.form.get('duration'), request.form.get('total_marks')

        quiz = Quiz(
            name=name,
            description=request.form.get('description', ''),
            chapter_id=chapter_id,
            start_time=datetime.strptime(start_time, '%Y-%m-%dT%H:%M') if start_time else None,
            end_time=datetime.strptime(end_time, '%Y-%m-%dT%H:%M') if end_time else None,
            duration=int(duration) if duration else None,
            max_marks=int(total_marks) if total_marks else None
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz added successfully!', 'success')

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_quizzes'))

@admin_bp.route('/admin/edit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        quiz.description = request.form.get('description', '').strip()
        quiz.chapter_id = int(request.form.get('chapter_id'))
        quiz.name = request.form.get('name').strip()
        quiz.start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M') if request.form.get('start_time') else None
        quiz.end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M') if request.form.get('end_time') else None
        quiz.duration = int(request.form.get('duration')) if request.form.get('duration') else None
        quiz.max_marks = int(request.form.get('total_marks')) if request.form.get('total_marks') else None

        db.session.commit()
        flash("Quiz updated successfully!", "success")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))  # Redirect back to the edit page in case of an error

    return redirect(url_for('admin.manage_quizzes'))

@admin_bp.route('/admin/toggle_quiz_status/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def toggle_quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.active = not quiz.active  # Toggle the status
    db.session.commit()

    flash(f"Quiz status changed to {'Active' if quiz.active else 'Inactive'}!", "success")
    return redirect(url_for('admin.manage_quizzes'))

@admin_bp.route('/admin/add_question_to_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question_to_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    subject_id = quiz.chapter.subject_id
    questions = Question.query.filter_by(chapter_id=quiz.chapter_id).all()  # Get questions related to the quiz's chapter

    if request.method == 'POST':
        question_ids = request.form.getlist('questions')  # Get list of selected question IDs
        try:
            for question_id in question_ids:
                question = Question.query.get_or_404(question_id)
                if question.chapter_id == quiz.chapter_id:  # Ensure question belongs to the same chapter as the quiz
                    quiz.questions.append(question)  # Link question to quiz
                else:
                    flash(f"Question '{question.question_text}' doesn't belong to this quiz's chapter!", 'danger')

            db.session.commit()
            flash(f"Questions added to quiz '{quiz.name}' successfully!", 'success')
        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
            db.session.rollback()

        return redirect(url_for('admin.manage_quizzes'))

    return render_template('admin/add_question_to_quiz.html', quiz=quiz, questions=questions)

@admin_bp.route('/admin/preview_quiz/<int:quiz_id>', methods=['GET'])
@login_required
@admin_required
def preview_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('admin/quiz_preview.html', quiz=quiz, questions=quiz.questions)

@admin_bp.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Delete related scores
        Score.query.filter_by(quiz_id=quiz.id).delete()
        
        # Delete attempts and answers
        attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
        for attempt in attempts:
            QuizAnswer.query.filter_by(attempt_id=attempt.id).delete()
        QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
        
        # Clear quiz-question relationships
        quiz.questions = []
        
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion failed: {str(e)}", "danger")
    return redirect(url_for('admin.manage_quizzes'))