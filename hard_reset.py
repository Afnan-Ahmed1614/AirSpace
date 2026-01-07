import os
import django

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airspace_project.settings")
django.setup()

from django.db import connection
from django.core.management import call_command

print("--- ⚠️ STARTING HARD RESET ---")

with connection.cursor() as cursor:
    # 1. Drop all chat tables forcefully
    tables = [
        "chat_message_likes", 
        "chat_message_dislikes", 
        "chat_message_hidden_by", 
        "chat_message", 
        "chat_profile", 
        "chat_room"
    ]
    for t in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
            print(f"🗑️ Dropped table: {t}")
        except Exception as e:
            print(f"⚠️ Could not drop {t}: {e}")

    # 2. Clear Django's memory of chat migrations
    print("🧹 Cleaning migration history...")
    cursor.execute("DELETE FROM django_migrations WHERE app='chat';")

# 3. Delete migration files
print("📂 Deleting migration files...")
mig_dir = os.path.join('chat', 'migrations')
if os.path.exists(mig_dir):
    for f in os.listdir(mig_dir):
        if f != '__init__.py' and f != '__pycache__':
            os.remove(os.path.join(mig_dir, f))

# 4. Re-create everything
print("\n--- 🛠️ REBUILDING DATABASE ---")
call_command('makemigrations', 'chat')
call_command('migrate', 'chat')

print("\n✅ SUCCESS! Database is completely fixed.")
print("Now run: python manage.py runserver")