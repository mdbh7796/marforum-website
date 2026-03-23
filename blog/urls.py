from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('search/', views.live_search, name='live_search'),
    path('moderate/', views.ModerationDashboardView.as_view(), name='moderation_dashboard'),
    path('comment/<int:pk>/approve/', views.toggle_comment_approval, name='toggle_comment_approval'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('tag/<slug:slug>/', views.TagPostListView.as_view(), name='tag_posts'),
    path('category/<slug:slug>/', views.CategoryPostListView.as_view(), name='category_posts'),
    path('user/<str:username>/', views.UserPostListView.as_view(), name='user_posts'),
    
    # Footer Placeholder Routes
    path('about/', views.PlaceholderView.as_view(), name='about'),
    path('contact/', views.PlaceholderView.as_view(), name='contact'),
    path('privacy/', views.PlaceholderView.as_view(), name='privacy'),
    path('terms/', views.PlaceholderView.as_view(), name='terms'),
    path('cookies/', views.PlaceholderView.as_view(), name='cookies'),
    path('disclaimer/', views.PlaceholderView.as_view(), name='disclaimer'),
    path('faq/', views.PlaceholderView.as_view(), name='faq'),
    path('report/', views.PlaceholderView.as_view(), name='report'),
    path('categories/', views.PlaceholderView.as_view(), name='category_index'),
    path('latest/', views.PlaceholderView.as_view(), name='latest_discussions'),
    path('popular/', views.PlaceholderView.as_view(), name='popular_threads'),
]
