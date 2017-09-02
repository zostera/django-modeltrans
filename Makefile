
test: pyclean
	./manage.py test --no-input
	flake8

pyclean:
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete

example:
	cd example && PYTHONPATH=.. ./manage.py runserver

shell:
	cd example && PYTHONPATH=.. ./manage.py shell_plus

isort:
	isort --recursive --diff --check modeltrans tests test_migrations example

.PHONY: test example
