from django.test import TestCase, Client
from django.contrib.auth import get_user_model


from posts.models import Post, Group

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='Заголовок группы',
            slug='test_slug',
            description='Описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.author = User.objects.create_user(username='isauthor')
        self.not_author = User.objects.create_user(username='notauthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(user=self.not_author)
        self.group = Group.objects.create(
            title='Testitle',
            slug='test-slug',
            description='testdescription'
        )

        self.post = Post.objects.create(
            text='text',
            author=self.author,
            group=self.group
        )

        self.index_url = '/'
        self.group_list_url = '/group/test_slug/'
        self.profile_url = '/profile/TestUser/'
        self.post_detail_url = f'/posts/{self.post.pk}/'
        self.create_url = '/create/'
        self.edit_url = f'/posts/{self.post.pk}/edit/'
        self.undefinded_url = '/not_exit/'

    def test_urls_for_all_users(self):
        templates_url_names = {
            'posts/index.html': self.index_url,
            'posts/group_list.html': self.group_list_url,
            'posts/profile.html': self.profile_url,
            'posts/post_detail.html': self.post_detail_url
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_status_code_guest_redirect(self):
        response = self.guest_client.get(self.create_url)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_status_create_auth(self):
        response = self.authorized_client.get(self.create_url)
        self.assertEqual(response.status_code, 200, 'error')

    def test_urls_status_edit_author(self):
        response = self.authorized_client.get(self.edit_url)
        self.assertEqual(response.status_code, 200, 'error')

    def test_urls_status_edit_not_author(self):
        response = self.authorized_client_not_author.get(
            self.edit_url)
        self.assertRedirects(response, self.index_url)

    def test_urls_unexisting_page(self):
        response = self.guest_client.get(self.undefinded_url)
        self.assertEqual(response.status_code, 404, 'error')


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.index_url = '/'
        self.about_author_url = '/about/author/'
        self.about_tech_url = '/about/tech/'

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_author(self):
        response = self.guest_client.get(self.about_author_url)
        self.assertEqual(response.status_code, 200)

    def test_tech(self):
        response = self.guest_client.get(self.about_tech_url)
        self.assertEqual(response.status_code, 200)
