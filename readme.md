# TVIS Backend

This repository contains the backend code for the TVIS project. It is built using Django and Django REST Framework.

## Project Structure

- **my_site/**: Django project folder.
- **tvis_app/**: Django app folder containing models, serializers, views, and API configurations.

## Setup

1. **Clone the Repository**: 

2. **Install Dependencies**: 

3. **Create Django Project and App**: 

4. **Configuration**:
- Configure settings in `my_site/settings.py`.
- Configure PostgreSQL database settings as shown below:

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

5. **Create Models, Serializers, and Views**: 
- Create models, serializers, and views in `tvis_app/`.

6. **Run Migrations**: 

7. **Start the Development Server**: 

## Contributing

Feel free to contribute to this project by forking the repository and sending pull requests. Please ensure that any changes are appropriately tested and documented.

## License

This project is licensed under the [MIT License](LICENSE).



