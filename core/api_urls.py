from django.urls import path
from core import views

urlpatterns = [
    path('stats/', views.api_stats, name='api_stats'),

    path('events/', views.api_events, name='api_events'),
    path('events/<int:pk>/', views.api_event_detail, name='api_event_detail'),

    path('officials/', views.api_officials, name='api_officials'),
    path('officials/<int:pk>/', views.api_official_detail, name='api_official_detail'),

    path('members/', views.api_members, name='api_members'),
    path('members/<int:pk>/', views.api_member_detail, name='api_member_detail'),

    path('gallery/', views.api_gallery, name='api_gallery'),
    path('gallery/<int:pk>/', views.api_gallery_detail, name='api_gallery_detail'),

    path('announcements/', views.api_announcements, name='api_announcements'),
    path('announcements/<int:pk>/', views.api_announcement_detail, name='api_announcement_detail'),
]
