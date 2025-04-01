from extensions import db
from datetime import datetime  # ✅ Import db from extensions

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Fixed type
    total_score = db.Column(db.Integer)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Fixed relationship to match Quiz.scores
    quiz = db.relationship('Quiz', back_populates='scores')  # Removed backref conflict
    user = db.relationship('User', back_populates='scores')

    def percentage(self):
        if self.quiz.max_marks and self.total_score is not None:
            return round((self.total_score / self.quiz.max_marks) * 100, 2)
        return 0  # Default if no score

    def __repr__(self):
        return f"<Score {self.id}>"
