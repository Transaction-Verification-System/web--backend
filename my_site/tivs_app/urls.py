from django.urls import path
from .views import *

urlpatterns = [
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('logout/',LogoutView.as_view(),name='logout'),
    path('home/',UserView.as_view(),name='session'),
    path('transaction/',TransactionView.as_view(),name='transaction'),
    path('csrf/',get_csrf_token,name='csrf_token'),
    path('text/', chat_view, name='chat'),
    path('task/',queue_result, name='queue'),
    path('success/',sucess,name='success'),
]
