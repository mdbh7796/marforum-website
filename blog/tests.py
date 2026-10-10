from django.test import TestCase
from django.urls import reverse
from blog.models import Post, CustomUser, Category, NewsletterSubscriber
from blog.rendering import render_markdown

class PostModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name='Test Category', slug='test-category')

    def test_post_slug_generation(self):
        post1 = Post.objects.create(title='Test Post', author=self.user, content='Content', status='published')
        self.assertEqual(post1.slug, 'test-post')
        
        post2 = Post.objects.create(title='Test Post', author=self.user, content='Content 2', status='published')
        self.assertEqual(post2.slug, 'test-post-1')
        
        post3 = Post.objects.create(title='Test Post', author=self.user, content='Content 3', status='published')
        self.assertEqual(post3.slug, 'test-post-2')

    def test_tag_post_list_view(self):
        post = Post.objects.create(title='Tagged Post', author=self.user, content='Content', status='published')
        post.tags.add('python')
        
        url = reverse('blog:tag_posts', kwargs={'slug': 'python'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tagged Post')
        self.assertEqual(len(response.context['posts']), 1)

class CustomUserRoleTest(TestCase):
    def test_roles_and_permissions(self):
        author = CustomUser.objects.create_user(username='author', password='pw', role='author')
        moderator = CustomUser.objects.create_user(username='mod', password='pw', role='moderator')
        admin = CustomUser.objects.create_user(username='admin', password='pw', role='admin')
        superuser = CustomUser.objects.create_superuser(username='super', password='pw', email='a@test.com')
        
        # Author tests
        self.assertTrue(author.is_author_role)
        self.assertFalse(author.is_moderator_role)
        self.assertFalse(author.is_admin_role)
        self.assertFalse(author.can_moderate())
        
        # Moderator tests
        self.assertTrue(moderator.is_author_role)
        self.assertTrue(moderator.is_moderator_role)
        self.assertFalse(moderator.is_admin_role)
        self.assertTrue(moderator.can_moderate())
        
        # Admin tests
        self.assertTrue(admin.is_author_role)
        self.assertTrue(admin.is_moderator_role)
        self.assertTrue(admin.is_admin_role)
        self.assertTrue(admin.can_moderate())
        
        # Superuser tests (save method sets role to 'admin', but let's test it handles everything based on is_superuser)
        self.assertTrue(superuser.is_author_role)
        self.assertTrue(superuser.is_moderator_role)
        self.assertTrue(superuser.is_admin_role)
        self.assertTrue(superuser.can_moderate())


class RenderingTest(TestCase):
    def test_markdown_strips_script_tags(self):
        self.assertNotIn('<script>', render_markdown('<script>alert(1)</script>'))
        self.assertNotIn('onclick', render_markdown('<img src="x" onclick="alert(1)">'))
        self.assertNotIn('javascript:', render_markdown('[x](javascript:alert(1))'))

    def test_markdown_keeps_safe_html(self):
        result = render_markdown('**bold** and [link](https://example.com)')
        self.assertIn('<strong>bold</strong>', result)
        self.assertIn('href="https://example.com"', result)


class PostDetailAccessTest(TestCase):
    def setUp(self):
        self.author = CustomUser.objects.create_user(username='author1', password='pw')
        self.category = Category.objects.create(name='Cat', slug='cat')
        self.published = Post.objects.create(
            title='Published Post', content='Content', author=self.author,
            category=self.category, status='published'
        )
        self.draft = Post.objects.create(
            title='Draft Post', content='Content', author=self.author, status='draft'
        )

    def test_draft_not_visible_to_anonymous(self):
        url = reverse('blog:post_detail', kwargs={'slug': self.draft.slug})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_published_visible_to_anonymous(self):
        url = reverse('blog:post_detail', kwargs={'slug': self.published.slug})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_author_can_view_own_draft(self):
        self.client.force_login(self.author)
        url = reverse('blog:post_detail', kwargs={'slug': self.draft.slug})
        self.assertEqual(self.client.get(url).status_code, 200)


class TrendingContextProcessorTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='trendauthor', password='pw')
        self.post = Post.objects.create(
            title='Trending Post', content='Content', author=self.user, status='published'
        )

    def test_returns_published_posts_without_error(self):
        from blog.context_processors import trending_posts
        result = trending_posts(self.client.get('/'))
        self.assertIn('footer_trending_posts', result)
        self.assertEqual(len(result['footer_trending_posts']), 1)


class NewsletterSignupTest(TestCase):
    def test_subscribe_creates_subscriber(self):
        response = self.client.post(reverse('blog:newsletter_signup'), {'email': 'test@example.com'})
        self.assertRedirects(response, reverse('blog:post_list'))
        self.assertTrue(NewsletterSubscriber.objects.filter(email='test@example.com').exists())

    def test_duplicate_email_is_idempotent(self):
        NewsletterSubscriber.objects.create(email='dup@example.com')
        self.client.post(reverse('blog:newsletter_signup'), {'email': 'dup@example.com'})
        self.assertEqual(NewsletterSubscriber.objects.filter(email='dup@example.com').count(), 1)
