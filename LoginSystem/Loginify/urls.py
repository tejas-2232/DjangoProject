from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.hello_world, name='hello_world'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    
    # CRUD Operations - Task 5
    path('users/', views.get_all_users_view, name='all_users'),
    re_path(r'^user/(?P<email>[^/]+)/update/$', views.update_user_view, name='update_user'),
    re_path(r'^user/(?P<email>[^/]+)/delete/$', views.delete_user_view, name='delete_user'),
    re_path(r'^user/(?P<email>[^/]+)/$', views.get_user_by_email_view, name='user_detail'),
] 