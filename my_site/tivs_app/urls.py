from django.urls import path
from .views import *

urlpatterns = [
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('home/',UserView.as_view(),name='session'),
    path('verify/',verify_token,name='verify'),
    path('chat/',chat_view,name='chat')
]
