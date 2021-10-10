from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile


from posts.models import Post, Group, Comment

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg')
        self.group_title = 'testtitle'
        self.group_slug = 'test_slug'
        self.group_description = 'testdescription'
        self.post_text = 'text'
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.author = User.objects.create_user(username='isauthor')
        self.not_author = User.objects.create_user(username='notauthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(user=self.not_author)
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
        self.comment_text = 'test text'
        self.posts_count = Post.objects.count()
        self.comment_count = Comment.objects.count()
        self.comment = Comment.objects.create(
            text=self.comment_text,
            author=self.author,
            post=self.post
        )
        self.url = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})

    def test_leave_comment_authorized_user(self):
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data={'text': 'test'},
            follow=True
        )
        post_with_comment = Comment.objects.first()
        self.assertEqual(post_with_comment.text, 'test')

    def test_leave_comment_guest_user(self):
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        response = self.guest_client.post(
            url,
            data={'text': 'test'},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + url)

    def test_create_post(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif')
        """Тестируем создание поста."""
        form_data = {'group': self.group.id,
                     'text': self.post_text,
                     'image': uploaded
                     }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        create_url = reverse('posts:profile', kwargs={'username': self.author})
        self.assertRedirects(response, create_url, HTTPStatus.FOUND)

    def test_create_post_guest(self):
        """Тестируем создание поста от гостя."""
        form_data = {'group': self.group.id,
                     'text': self.post_text}
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        lurl = reverse('users:login')
        purl = reverse('posts:post_create')
        response_url = (lurl + '?next=' + purl)
        self.assertRedirects(response, response_url)
        self.assertEqual(post_count, Post.objects.count())

    def test_post_edit(self):
        form_data = {
            'text': self.post_text,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.pk
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        post = Post.objects.first()
        self.assertEqual(post.text, self.post_text)
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.group)
