from main import app, db, Application, User, Job

with app.app_context():
    print("\n=== ALL APPLICATIONS ===")
    applications = Application.query.all()
    
    if not applications:
        print("❌ No applications found in database")
    else:
        for app in applications:
            print(f"\n Application ID: {app.id}")
            print(f"  Job: {app.job.title}")
            print(f"  Applicant: {app.applicant.name}")
            print(f"  Status: {app.status}")
            print(f"  Applied: {app.applied_at}")
    
    print("\n=== ALL JOBS ===")
    jobs = Job.query.all()
    for job in jobs:
        print(f"\nJob: {job.title} (Status: {job.status})")
        print(f"  Applications: {len(job.applications)}")
    
    print("\n=== ALL USERS ===")
    users = User.query.all()
    for user in users:
        print(f"{user.name} - {user.email} - {user.user_type}")