import shutil
import tempfile

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.cache import cache


from posts.models import Post, Group, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.group_title = 'testtitle'
        self.group_slug = 'test_slug'
        self.group_description = 'testdescription'
        self.post_text = 'text'
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.user2 = User.objects.create_user(username='TestUser2')
        self.author = User.objects.create_user(username='isauthor')
        self.not_author = User.objects.create_user(username='notauthor')
        self.not_author2 = User.objects.create_user(username='notauthor2')
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(user=self.not_author)
        self.authorized_client_not_author2 = Client()
        self.authorized_client_not_author2.force_login(user=self.not_author2)
        self.group = Group.objects.create(
            title=self.group_title,
            slug=self.group_slug,
            description=self.group_description
        )
        self.group2 = Group.objects.create(
            title=self.group_title + '2',
            slug=self.group_slug + '_2',
            description=self.group_description + '2'
        )
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif')

        self.post = Post.objects.create(
            image=self.uploaded,
            text=self.post_text,
            author=self.author,
            group=self.group
        )
        self.follower = Follow.objects.create(
            user=self.user,
            author=self.author
        )

    def test_follow_unfollow_auth(self):
        profile_follow_url = reverse(
            'posts:profile_follow', args=[self.author.username])
        profile_unfollow_url = reverse(
            'posts:profile_unfollow', args=[self.author.username])
        self.authorized_client_not_author.get(profile_follow_url)
        self.assertTrue(
            Follow.objects.filter(
                user=self.not_author, author=self.author).exists()
        )
        self.authorized_client_not_author.get(profile_unfollow_url)
        self.assertFalse(
            Follow.objects.filter(
                user=self.not_author, author=self.author).exists()
        )

    def test_follower_have_new_record_and_not_follower_dont_have(self):
        Follow.objects.create(user=self.not_author, author=self.author)
        self.post = Post.objects.create(
            image=self.uploaded,
            text='AAAAAAAAAAAAAAAAAAAAAAAA',
            author=self.author,
        )
        page_obj = self.authorized_client_not_author.get(
            reverse('posts:follow_index')).context['page_obj']
        foreign_page_obj = self.authorized_client_not_author2.get(
            reverse('posts:follow_index')).context['page_obj']
        self.assertIn(self.post, page_obj)
        self.assertNotIn(self.post, foreign_page_obj)

    def test_cache(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.get(
            reverse('posts:index')).content
        Post.objects.create(
            text='text', author=self.author, group=self.group
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(
            response, self.authorized_client.get(
                reverse('posts:index')).content)
        cache.clear()
        self.assertNotEqual(
            response, self.authorized_client.get(
                reverse('posts:index')).content)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={'slug': 'test_slug'})):
            'posts/group_list.html',
            (reverse('posts:profile', kwargs={
                'username': self.author.username})):
                'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
                reverse('posts:post_detail', kwargs={
                    'post_id': self.post.pk}): 'posts/post_detail.html',
            (reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk})): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        group_title_0 = first_object.group.title
        group_slug_0 = first_object.group.slug
        group_description_0 = first_object.group.description
        self.assertEqual(group_title_0, self.group_title)
        self.assertEqual(group_description_0, self.group_description)
        self.assertEqual(group_slug_0, self.group_slug)
        self.assertTrue(first_object.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            (reverse('posts:group_list', kwargs={'slug': 'test_slug'})))
        first_object = response.context['page_obj'][0]
        group_title_0 = first_object.group.title
        group_slug_0 = first_object.group.slug
        group_description_0 = first_object.group.description
        self.assertEqual(group_title_0, self.group_title)
        self.assertEqual(group_description_0, self.group_description)
        self.assertEqual(group_slug_0, self.group_slug)
        self.assertTrue(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            (reverse('posts:profile', kwargs={
                'username': self.author.username})))
        count = response.context['count']
        test_count = Post.objects.filter(author=self.author).count()
        self.assertEqual(count, test_count)
        author = response.context['author']
        self.assertEqual(author, self.author)
        first_object = response.context['page_obj'][0]
        text_object_0 = first_object.text
        self.assertEqual(text_object_0, self.post.text)
        self.assertTrue(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk})))
        count = response.context['count']
        test_count = Post.objects.filter(author=self.post.author).count()
        self.assertEqual(count, test_count)
        test_post = self.post
        text_object = response.context['post']
        image_object = text_object.image
        self.assertEqual(test_post, text_object)
        self.assertTrue(image_object, self.post.image)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        test_text = 'text'
        response = self.authorized_client.post(reverse(
            'posts:post_create'), data={
                'text': test_text, 'group': self.group})
        self.assertEqual(response.status_code, 200, 'invalid_post_create')
        post = Post.objects.all().first()
        response = self.authorized_client.get(reverse('posts:index'))
        first_object_index = response.context['page_obj'][0]
        self.assertEqual(first_object_index, post)
        response = self.authorized_client.get(
            (reverse('posts:group_list', kwargs={'slug': 'test_slug'})))
        first_object_group_list = response.context['page_obj'][0]
        self.assertEqual(first_object_group_list, post)
        response = self.authorized_client.get(
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk})))
        first_object_post_detail = response.context['post']
        self.assertEqual(first_object_post_detail, post)
        response = self.authorized_client.get(
            (reverse('posts:group_list', kwargs={'slug': self.group2.slug})))
        self.assertNotIn(post, response.context['page_obj'])

    class PaginatorViewsTest(TestCase):
        def test_first_page_contains_ten_records_index(self):
            for i in range(1, 13):
                Post.objects.create(
                    text=self.post_text,
                    author=self.author,
                    group=self.group
                )
            response = self.client.get(reverse('index'))
            self.assertEqual(len(response.context['object_list']), 10)

        def test_second_page_contains_three_records_index(self):
            response = self.client.get(reverse('index') + '?page=2')
            self.assertEqual(len(response.context['object_list']), 3)

        def test_first_page_contains_ten_records_group_list(self):
            for i in range(1, 13):
                Post.objects.create(
                    text=self.post_text,
                    author=self.author,
                    group=self.group
                )
            response = self.client.get(reverse('group_list'))
            self.assertEqual(len(response.context['object_list']), 10)

        def test_second_page_contains_three_records_group_list(self):
            response = self.client.get(reverse('group_list') + '?page=2')
            self.assertEqual(len(response.context['object_list']), 3)

        def test_first_page_contains_ten_records_profile(self):
            for i in range(1, 13):
                Post.objects.create(
                    text=self.post_text,
                    author=self.author,
                    group=self.group
                )

            response = self.client.get(reverse('profile'))
            self.assertEqual(len(response.context['object_list']), 10)

        def test_second_page_contains_three_records_profile(self):
            response = self.client.get(reverse('group_list') + '?page=2')
            self.assertEqual(len(response.context['object_list']), 3)
