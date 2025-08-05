# DjangoProject

This Django project aims to create a robust system with features for user signup, login, and profile management. 

It includes functionalities such as user registration, user data, retrieval updating user details, and deleting user accounts.

The project utilises Django's built-in features for model creation, views implementation, URL routing, and template rendering to achieve seamless user interaction and data management

Additionally, thorough testing with Postman ensures the reliabiity and functionality of the CRUD operatios

# Task 1 - SETTING UP PROJECT 

Set up a Django project named "Login System" with a virtual environment and a Django application named "Loginify".
 

# Task 2 -CREATE VIEWS AND URLS FOR LOGIN SYSTEM

 Create views and define URL patterns for the "Login System" Django application to handle login functionality.

In ```Loginify/urls.py```, 
* we have used path and re_path to define URL patterns.
* re_path is used to define URL patterns that contain variables like email in the URL.

When to use path?
* simple URL patterns (Basic string/integer parameters)
* No special characters in parameters

__Example__

```python
path('signup/', views.signup_view, name='signup'),
```

When to use re_path?
* Complex parameters (like emails)
* Need precise pattern matching
* Special characters in URL parameters

__Example__
```python
re_path(r'^user/(?P<email>[^/]+)/$', views.user_detail)
```

# Task 3 - CREATE MODELS FOR LOGIN SYSTEM

Define models, implement views, and set up URLs and templates in Loginify.

# Task 4 - Models and Admin
Set up a superuser account using Django's manage.py command and verify the superuser endpoint by accessing the admin interface to ensure proper configuration and functionality.

# Task 5 - CRUD Operations

Implement CRUD (Create, Read, Update, Delete) operations for
 managing user data within the Django login system.