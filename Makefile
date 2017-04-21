
test:
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=tests.app.settings django-admin test



.PHONY: test
