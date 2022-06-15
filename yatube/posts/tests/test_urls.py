from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Фанаты чтения по ночам',
            slug='night',
            description='Группа тех, кто любит читать ночью.',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись нового поста',
            id=1
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsUrlTest.user)

    def test_url_authorized_access(self):
        """Проверка доступа авторизированного пользователя"""
        url_status_authorized = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
        }
        for address, status in url_status_authorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_url_authorized_not_author_access(self):
        """Проверка доступа авторизированного пользователя
            к странице редактирования поста другого пользователя
        """
        not_author_user = User.objects.create_user(username='not_author_user')
        authorized_client_not_author = Client()
        authorized_client_not_author.force_login(not_author_user)
        response = authorized_client_not_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_unauthorized_access(self):
        """Проверка доступа неавторизированного пользователя"""
        url_status_unauthorized = {
            '/': HTTPStatus.OK,
            '/group/night/': HTTPStatus.OK,
            '/profile/test_user/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            '/posts/1/edit/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in url_status_unauthorized.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_url_templates(self):
        """Проверка соответствия шаблонов URL-адресу"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/night/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
