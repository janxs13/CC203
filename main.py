from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'job_finder_secret_key_2024'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobfinder.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), default='jobseeker')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='employer', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form.get('user_type', 'jobseeker')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('index'))
        
        # Create new user
        new_user = User(name=fullname, email=email, user_type=user_type)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_type'] = user.user_type
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get all jobs with employer information
    jobs = db.session.query(Job, User).join(User, Job.user_id == User.id).order_by(Job.created_at.desc()).all()
    
    user_data = {
        'id': session['user_id'],
        'name': session['user_name'],
        'email': session['user_email'],
        'user_type': session['user_type']
    }
    
    return render_template('dashboard.html', user=user_data, jobs=jobs)

@app.route('/post_job', methods=['POST'])
def post_job():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    title = request.form['title']
    description = request.form['description']
    location = request.form['location']
    salary = request.form.get('salary', '')
    
    # Create new job post
    new_job = Job(
        title=title,
        description=description,
        location=location,
        salary=salary,
        user_id=session['user_id']
    )
    
    db.session.add(new_job)
    db.session.commit()
    
    flash("Job posted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    job = Job.query.get(job_id)
    
    if job and job.user_id == session['user_id']:
        db.session.delete(job)
        db.session.commit()
        flash("Job deleted successfully!", "success")
    else:
        flash("You can only delete your own job posts.", "danger")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    app.run(debug=True)