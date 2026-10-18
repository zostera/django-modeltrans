
test: pyclean
	./manage.py test --no-input

pre-commit:
	pre-commit run --all-files

pyclean:
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete

example:
	cd example && PYTHONPATH=.. ./manage.py runserver

shell:
	cd example && PYTHONPATH=.. ./manage.py shell_plus

notebook:
	cd example && PYTHONPATH=.. ./manage.py shell_plus --notebook

.PHONY: test example pre-commit
