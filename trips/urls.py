from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('enter/', views.enter, name='enter'),
    path('join/', views.join_trip_info, name='join_trip_info'),
    path('create/', views.create_trip, name='create_trip'),
    path('trip/<int:pk>/', views.trip_detail, name='trip_detail'),
    path('my-trips/', views.my_trips, name='my_trips'),
    path('trip/<int:pk>/delete/', views.delete_trip, name='delete_trip'),
    path('trip/<int:trip_pk>/category/<int:category_pk>/add/', views.add_proposal, name='add_proposal'),
    path('proposal/<int:pk>/vote/', views.vote_proposal, name='vote_proposal'),
    path('proposal/<int:pk>/lock/', views.lock_proposal, name='lock_proposal'),
    path('proposal/<int:pk>/unlock/', views.unlock_proposal, name='unlock_proposal'),
    path('proposal/<int:pk>/edit/', views.edit_proposal, name='edit_proposal'),
    path('trip/<int:pk>/invite/', views.send_invites, name='send_invites'),
    path('trip/<int:pk>/join/', views.join_trip, name='join_trip'),
    path('trip/<int:pk>/chat/', views.trip_chat, name='trip_chat'),
    path('proposal/<int:pk>/delete/', views.delete_proposal, name='delete_proposal'),
    path('trip/<int:pk>/leave/', views.leave_trip, name='leave_trip'),
]
