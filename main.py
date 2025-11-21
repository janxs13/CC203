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
    company_name = db.Column(db.String(200))
    company_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='employer', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='applicant', lazy=True, cascade='all, delete-orphan')
    
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
    status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    fullname = request.form['fullname']
    email = request.form['email']
    password = request.form['password']
    user_type = request.form.get('user_type', 'jobseeker')
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered. Please log in.", "warning")
        return redirect(url_for('index'))
    
    new_user = User(name=fullname, email=email, user_type=user_type)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    flash("Registration successful! You can now log in.", "success")
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
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
    
    user = User.query.get(session['user_id'])
    
    # Handle case where user doesn't exist
    if not user:
        session.clear()
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('index'))
    
    if user.user_type == 'admin':
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        users = User.query.filter(User.user_type != 'admin').order_by(User.created_at.desc()).all()
        return render_template('admin_dashboard.html', user=user, jobs=jobs, users=users)
    elif user.user_type == 'employer':
        my_jobs = Job.query.filter_by(user_id=user.id).order_by(Job.created_at.desc()).all()
        return render_template('employer_dashboard.html', user=user, jobs=my_jobs)
    else:
        jobs = Job.query.filter_by(status='approved').order_by(Job.created_at.desc()).all()
        my_applications = Application.query.filter_by(user_id=user.id).order_by(Application.applied_at.desc()).all()
        return render_template('jobseeker_dashboard.html', user=user, jobs=jobs, applications=my_applications)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.name = request.form['name']
        if user.user_type == 'employer':
            user.company_name = request.form.get('company_name')
            user.company_details = request.form.get('company_details')
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/post_job', methods=['POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('index'))
    
    title = request.form['title']
    description = request.form['description']
    location = request.form['location']
    salary = request.form.get('salary', '')
    
    new_job = Job(
        title=title,
        description=description,
        location=location,
        salary=salary,
        user_id=session['user_id'],
        status='pending'
    )
    
    db.session.add(new_job)
    db.session.commit()
    
    flash("Job posted successfully! Waiting for admin approval.", "success")
    return redirect(url_for('dashboard'))

@app.route('/approve_job/<int:job_id>')
def approve_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('index'))
    
    job = Job.query.get(job_id)
    if job:
        job.status = 'approved'
        db.session.commit()
        flash("Job approved successfully!", "success")
    
    return redirect(url_for('dashboard'))

@app.route('/reject_job/<int:job_id>')
def reject_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('index'))
    
    job = Job.query.get(job_id)
    if job:
        job.status = 'rejected'
        db.session.commit()
        flash("Job rejected.", "info")
    
    return redirect(url_for('dashboard'))

@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    job = Job.query.get(job_id)
    
    if job and (job.user_id == session['user_id'] or session['user_type'] == 'admin'):
        db.session.delete(job)
        db.session.commit()
        flash("Job deleted successfully!", "success")
    else:
        flash("You can only delete your own job posts.", "danger")
    
    return redirect(url_for('dashboard'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if user and user.user_type != 'admin':
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
    
    return redirect(url_for('dashboard'))

@app.route('/apply_job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'jobseeker':
        flash("You must be logged in as a job seeker to apply.", "danger")
        return redirect(url_for('index'))
    
    # Check if already applied
    existing = Application.query.filter_by(job_id=job_id, user_id=session['user_id']).first()
    if existing:
        flash("You have already applied to this job.", "warning")
        return redirect(url_for('dashboard'))
    
    cover_letter = request.form.get('cover_letter', '')
    
    application = Application(
        job_id=job_id,
        user_id=session['user_id'],
        cover_letter=cover_letter,
        status='pending'
    )
    
    db.session.add(application)
    db.session.commit()
    
    flash("Application submitted successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/job_applicants/<int:job_id>')
def job_applicants(job_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('index'))
    
    job = Job.query.get(job_id)
    if not job or job.user_id != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('dashboard'))
    
    applications = Application.query.filter_by(job_id=job_id).order_by(Application.applied_at.desc()).all()
    return render_template('applicants.html', job=job, applications=applications, user=user)
@app.route('/update_application/<int:app_id>/<status>')
def update_application(app_id, status):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('index'))
    
    application = Application.query.get(app_id)
    if application and application.job.user_id == session['user_id']:
        application.status = status
        db.session.commit()
        flash(f"Application {status}!", "success")
    
    return redirect(url_for('job_applicants', job_id=application.job_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        admin = User.query.filter_by(email='admin@jobfinder.com').first()
        if not admin:
            admin = User(name='Admin', email='admin@jobfinder.com', user_type='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@jobfinder.com / admin123")
        
        print("Database initialized successfully!")
    
    app.run(debug=True)