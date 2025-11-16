 🔍 Local Job Finder

A complete Flask-based job portal with three user roles: Admin, Employer, and Job Seeker.

 📋 Installation Steps

 1. Install Python Dependencies
```bash
pip install flask flask-sqlalchemy
```

 2. Run the Application
```bash
python main.py
```

3. Access the Website
Open your browser: `http://127.0.0.1:5000/`

🔑 Default Admin Login

 Email: admin@jobfinder.com
 Password: admin123

📁 Project Structure
```
LocalJobFWEB/
├── main.py
├── jobfinder.db (auto-created)
├── static/
│   └── styles.css
└── templates/
    ├── base.html
    ├── index.html
    ├── admin_dashboard.html
    ├── employer_dashboard.html
    ├── jobseeker_dashboard.html
    ├── applicants.html
    └── profile.html
```

 ✨ Features

 Admin:
- Approve/reject job posts
- Manage users
- Delete jobs and users

 Employer:
- Create company profile
- Post jobs (requires approval)
- Manage applicants
- Accept/reject applications

 Job Seeker:
- Browse approved jobs
- Apply with cover letter
- Track application status

🎯 How to Test

1. **Login as Admin**: admin@jobfinder.com / admin123
2. **Register as Employer**: Create account, add company info, post job
3. **Admin approves**: Login as admin, approve the job
4. **Register as Job Seeker**: Create account, browse jobs, apply
5. **Employer reviews**: Check applicants, accept/reject

---

**Made with ❤️ for Local Job Finding**
