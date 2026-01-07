import os
import shutil
import subprocess

def run_command(command):
    print(f"Running: {command}")
    subprocess.run(command, shell=True)

def clean_migrations():
    # 1. Delete Database file if it exists (SQLite)
    if os.path.exists("db.sqlite3"):
        os.remove("db.sqlite3")
        print("Deleted db.sqlite3")
    
    # 2. Clear Migration folder
    migration_path = os.path.join("chat", "migrations")
    if os.path.exists(migration_path):
        for filename in os.listdir(migration_path):
            if filename != "__init__.py" and filename != "__pycache__":
                file_path = os.path.join(migration_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    print(f"Deleted: {filename}")
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

if __name__ == "__main__":
    print("--- STARTING CLEANUP ---")
    
    # Step A: Delete old migration files
    clean_migrations()
    
    print("\n--- RESETTING DATABASE ---")
    # Step B: Reset DB (For Postgres/SQLite both)
    # This clears all data and drops tables
    run_command("python manage.py flush --no-input")
    
    print("\n--- CREATING NEW MIGRATIONS ---")
    # Step C: Make new migrations
    run_command("python manage.py makemigrations chat")
    
    print("\n--- APPLYING MIGRATIONS ---")
    # Step D: Apply to DB
    run_command("python manage.py migrate --fake-initial")
    run_command("python manage.py migrate")
    
    print("\n✅ DONE! Database is fixed. Now run 'python manage.py runserver'")