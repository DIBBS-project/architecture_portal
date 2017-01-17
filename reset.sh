#! /bin/bash

APPS=common_app\ contributor_app\ enduser_app

echo "[RESET] Resetting the application..."
rm -rf tmp
rm -rf db.sqlite3
for APP in $APPS; do
	rm -rf $APP/migrations
	python manage.py makemigrations $APP
done
python manage.py migrate
echo "[RESET] Creating superuser 'admin' with password 'pass'..."
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python manage.py shell
