from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from mptt.admin import MPTTModelAdmin
from .models import CustomUser, Post, Comment, Category


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'profile_picture', 'bio')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Profile', {
            'fields': ('role', 'profile_picture', 'bio')
        }),
    )
    
    actions = ['make_moderator', 'make_author', 'make_admin']
    
    @admin.action(description='Make selected users Moderators')
    def make_moderator(self, request, queryset):
        queryset.update(role='moderator')
    
    @admin.action(description='Make selected users Authors')
    def make_author(self, request, queryset):
        queryset.update(role='author')
    
    @admin.action(description='Make selected users Admins')
    def make_admin(self, request, queryset):
        queryset.update(role='admin')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'category', 'view_count', 'created_at']
    list_filter = ['status', 'category', 'is_featured', 'created_at', 'tags']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'status', 'category', 'is_featured')
        }),
        ('Content', {
            'fields': ('featured_image', 'excerpt', 'content', 'tags')
        }),
        ('Publishing', {
            'fields': ('published_at', 'view_count'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_posts', 'unpublish_posts', 'mark_pending_review']
    
    def publish_posts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} post(s) published.')
    
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished.')
    
    def mark_pending_review(self, request, queryset):
        updated = queryset.update(status='pending_review')
        self.message_user(request, f'{updated} post(s) marked for review.')


@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    list_display = ['short_content', 'author', 'post', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['content', 'author__username', 'post__title']
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'reject_comments']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} comment(s) approved.')
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} comment(s) rejected.')
