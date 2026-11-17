from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/add/', views.add_book, name='add_book'),
    path('books/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('books/<int:pk>/exchange/', views.propose_exchange, name='propose_exchange'),
    path('exchanges/', views.exchanges, name='exchanges'),
    path('exchanges/<int:pk>/<str:action>/', views.exchange_action, name='exchange_action'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile, name='public_profile'),
    path('moderation/', views.moderation, name='moderation'),
    path('moderation/<int:pk>/<str:action>/', views.moderate_book, name='moderate_book'),
]
