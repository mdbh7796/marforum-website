from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q, Prefetch, Count
from taggit.models import Tag

from .models import Post, Comment, Category, CustomUser, NewsletterSubscriber
from .forms import PostForm, CommentForm
from .rendering import render_markdown

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        return Post.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags').annotate(
            approved_comment_count=Count('comments', filter=Q(comments__status='approved'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = Post.objects.filter(
            is_featured=True, status='published'
        ).annotate(
            approved_comment_count=Count('comments', filter=Q(comments__status='approved'))
        )[:5]
        context['categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['popular_tags'] = Tag.objects.all()[:20]
        return context


class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_author_role
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.status == 'published':
            form.instance.published_at = timezone.now()
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create New Post'
        context['button_text'] = 'Publish Post'
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        user = self.request.user
        base = Post.objects.select_related(
            'author', 'category'
        ).prefetch_related('tags')
        if user.is_authenticated and (user.is_moderator_role or user.is_superuser):
            return base
        if user.is_authenticated:
            return base.filter(Q(status='published') | Q(author=user))
        return base.filter(status='published')
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        post = self.object
        session_key = f'viewed_post_{post.pk}'
        if not request.session.get(session_key, False):
            post.view_count += 1
            post.save(update_fields=['view_count'])
            request.session[session_key] = True
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Only fetch approved replies to prevent duplication and improve efficiency
        approved_replies = Prefetch(
            'replies',
            queryset=Comment.objects.filter(status='approved').select_related('author'),
            to_attr='approved_replies'
        )
        
        context['comment_form'] = kwargs.get('comment_form') or CommentForm()
        context['approved_comments'] = post.comments.filter(
            status='approved',
            parent=None
        ).select_related('author').prefetch_related(approved_replies)
        
        context['related_posts'] = Post.objects.filter(
            status='published',
            category=post.category
        ).exclude(pk=post.pk)[:4]
        
        context['rendered_content'] = post.rendered_content or render_markdown(post.content)
        
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        self.object = self.get_object()
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                # Security/Integrity check: parent comment must belong to the same post
                comment.parent = get_object_or_404(Comment, pk=parent_id, post=self.object)
            comment.save()
            messages.success(request, 'Your comment has been submitted for moderation!')
            return redirect('blog:post_detail', slug=self.object.slug)
        
        # If form is invalid, re-render the detail page with the form errors
        context = self.get_context_data(comment_form=form)
        return self.render_to_response(context)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    context_object_name = 'post'
    
    def test_func(self):
        post = self.get_object()
        return (self.request.user == post.author or 
                self.request.user.is_moderator_role or 
                self.request.user.is_superuser)
    
    def form_valid(self, form):
        if form.instance.status == 'published' and not form.instance.published_at:
            form.instance.published_at = timezone.now()
        messages.success(self.request, 'Post updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Post'
        context['button_text'] = 'Update Post'
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('blog:post_list')
    
    def test_func(self):
        post = self.get_object()
        return (self.request.user == post.author or 
                self.request.user.is_moderator_role or 
                self.request.user.is_superuser)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Post deleted successfully!')
        return super().delete(request, *args, **kwargs)


def live_search(request):
    if request.htmx:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return HttpResponse('')
        
        posts = Post.objects.filter(
            Q(status='published') &
            (Q(title__icontains=query) | 
             Q(content__icontains=query) |
             Q(tags__name__icontains=query))
        ).distinct()[:10]
        
        context = {
            'posts': posts,
            'query': query,
        }
        return render(request, 'blog/search_results.html', context)
    
    return redirect('blog:post_list')


class TagPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Post.objects.filter(
            tags__slug=self.kwargs['slug'],
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['popular_tags'] = Tag.objects.all()[:20]
        return context


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.objects.filter(
            category=self.category,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['popular_tags'] = Tag.objects.all()[:20]
        return context


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        self.user = get_object_or_404(CustomUser, username=self.kwargs['username'])
        return Post.objects.filter(
            author=self.user,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.user
        context['categories'] = Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        context['popular_tags'] = Tag.objects.all()[:20]
        return context


class ModerationDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Comment
    template_name = 'blog/moderate_dashboard.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_moderate()
    
    def get_queryset(self):
        queryset = Comment.objects.select_related(
            'post', 'author'
        ).order_by('-created_at')
        
        filter_status = self.request.GET.get('status', 'pending')
        if filter_status in ['pending', 'approved', 'rejected']:
            queryset = queryset.filter(status=filter_status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = Comment.objects.filter(status='pending').count()
        context['approved_count'] = Comment.objects.filter(status='approved').count()
        context['rejected_count'] = Comment.objects.filter(status='rejected').count()
        context['current_filter'] = self.request.GET.get('status', 'pending')
        
        context['pending_posts'] = Post.objects.filter(
            status='pending_review'
        ).select_related('author') if self.request.user.is_admin_role else []
        
        return context


@login_required
def toggle_comment_approval(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    if not request.user.can_moderate() and not comment.can_be_approved_by(request.user):
        messages.error(request, 'You do not have permission to moderate this comment.')
        return redirect('blog:moderation_dashboard')
    
    if request.method == 'POST':
        if comment.status == 'approved':
            comment.status = 'pending'
            messages.success(request, 'Comment approval revoked.')
        else:
            comment.status = 'approved'
            messages.success(request, 'Comment approved successfully!')
        comment.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'blog:moderation_dashboard'))


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post = comment.post
    
    if not (request.user == comment.author or 
            request.user == post.author or 
            request.user.can_moderate()):
        messages.error(request, 'You do not have permission to delete this comment.')
        return redirect('blog:post_detail', slug=post.slug)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted.')
    
    return redirect('blog:post_detail', slug=post.slug)


def newsletter_signup(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()

        if email:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as EmailValidationError

            try:
                validate_email(email)
            except EmailValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return redirect('blog:post_list')

            NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            messages.success(request, 'Thanks for subscribing! You will hear from us soon.')
        else:
            messages.error(request, 'Please enter your email address.')

    return redirect('blog:post_list')


class PlaceholderView(TemplateView):
    template_name = 'blog/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_name = self.request.path.strip('/').replace('-', ' ').title()
        if not page_name:
            page_name = "Page"
        context['page_title'] = page_name
        return context
