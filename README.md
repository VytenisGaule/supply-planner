1. **Clone the repository:**
	```bash
	git clone <your-repo-url>
	cd supply-planner
	```

2. **Create and activate a virtual environment:**
	```bash
	python3 -m venv virtualEnvironment
	source virtualEnvironment/bin/activate
	```

3. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```

4. **Apply migrations:**
	```bash
	./virtualEnvironment/bin/python manage.py makemigrations
	./virtualEnvironment/bin/python manage.py migrate
	```

5. **(Optional) Create a superuser:**
	```bash
	./virtualEnvironment/bin/python manage.py createsuperuser
	```

6. **Run the development server:**
	```bash
	./virtualEnvironment/bin/python manage.py runserver
	```

**Notes:**
- Make sure you have Python 3.12+ installed.
- If you use custom environment variables, set them up as needed.
- For static files, run `./virtualEnvironment/bin/python manage.py collectstatic` if required.
