from django.db.models import Count, Q

from .models import Post

def trending_posts(request):
    """
    Context processor to add trending posts to the context of every template.
    Usually rendered in the footer globally.
    """
    try:
        # Fetch top 4 most commented or viewed published posts
        trends = Post.objects.filter(status='published').annotate(
            approved_comment_count=Count('comments', filter=Q(comments__status='approved'))
        ).order_by('-approved_comment_count', '-view_count')[:4]
    except Exception:
        trends = []
    
    return {
        'footer_trending_posts': trends
    }