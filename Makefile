
test: pyclean
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.app.settings django-admin test --no-input
	flake8

pyclean:
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete

example:
	cd example && PYTHONPATH=.. ./manage.py runserver

.PHONY: test example
