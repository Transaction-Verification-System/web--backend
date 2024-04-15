# My Site

Welcome to My Site! This is a Django project designed to [briefly describe your project's purpose or functionality].

## Installation

To run this project locally, follow these steps:

1. Clone this repository to your local machine:

```bash
git clone git@github.com:Sachit56/TVIS-backend.git


## Project Structure

- **my_site/**: Django project folder.
- **tvis_app/**: Django app folder containing models, serializers, views, and API configurations.

## Setup

1. Install dependencies: `pip install django djangorestframework`.
2. Create Django project and app: `django-admin startproject my_site && python manage.py startapp tvis_app`.
3. Configure settings in `myproject/settings.py`.
4. Create models, serializers, and views in `tvis_app/`.
5. Run migrations: `python manage.py makemigrations && python manage.py migrate`.
6. Start the development server: `python manage.py runserver`.


## Configure PostgreSQL Database for Django Project

In your Django project's `settings.py` file, configure the PostgreSQL database as follows:

```python
# In your my_site/settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tvis',
        'USER':'postgres',
        'PASSWORD':'admin@123',
        'HOST':'localhost',
        'PORT':'5432'
    }
}
```





