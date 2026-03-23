from .models import Post

def trending_posts(request):
    """
    Context processor to add trending posts to the context of every template.
    Usually rendered in the footer globally.
    """
    try:
        # Fetch top 4 most commented or viewed published posts
        trends = Post.objects.filter(status='published').order_by('-comment_count', '-view_count')[:4]
    except Exception:
        trends = []
    
    return {
        'footer_trending_posts': trends
    }
