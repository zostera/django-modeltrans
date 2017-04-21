
test: pyclean
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.app.settings django-admin test

pyclean:
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete

.PHONY: test
