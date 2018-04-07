from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('account-balances.json', views.json, name='json'),
]