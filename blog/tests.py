from django.test import TestCase
from django.urls import reverse
from blog.models import Post, CustomUser, Category

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
