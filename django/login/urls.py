from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('attempt_login', views.attempt_login, name='attempt_login'),
]