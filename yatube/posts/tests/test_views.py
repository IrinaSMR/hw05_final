import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='test_author'
        )

        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author,
            image=uploaded,
        )

        cls.template_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[cls.group.slug]):
                'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}):
                'posts/create_post.html',
            reverse('posts:profile', args=[cls.author.username]):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.pk}):
                'posts/post_detail.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_author_client = Client()
        self.auth_author_client.force_login(self.author)
        self.authorized_not_author_client = Client()
        self.authorized_not_author_client.force_login(self.not_author)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for url, template in PostPagesTest.template_names.items():
            with self.subTest(template=template):
                response = self.auth_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(response_post.image, PostPagesTest.post.image)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', args=[PostPagesTest.author.username])
        )
        response_author = response.context.get('author')
        response_count = response.context.get('post_count')
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(PostPagesTest.author, response_author)
        self.assertEqual(1, response_count)
        self.assertEqual(response_post.image, PostPagesTest.post.image)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTest.post.pk})
        )
        response_post = response.context.get('post')
        response_count = response.context.get('post_count')
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(PostPagesTest.post, response_post)
        self.assertEqual(1, response_count)
        self.assertEqual(response_post.image, PostPagesTest.post.image)

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:post_create')
        )
        for field, expected in PostPagesTest.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTest.post.pk}))

        for field, expected in PostPagesTest.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_author_client.get(
            reverse('posts:group_list', args=[PostPagesTest.group.slug])
        )
        response_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_post.author, PostPagesTest.author)
        self.assertEqual(response_post.group, PostPagesTest.group)
        self.assertEqual(response_post.text, PostPagesTest.post.text)
        self.assertEqual(response_post.image, PostPagesTest.post.image)

    def test_index_page_cache(self):
        """Проверка работы кэша на странице index."""
        page_1 = self.guest_client.get(reverse('posts:index')).content
        Post.objects.create(text='Текст', author=self.author)
        page_2 = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(page_1, page_2)
        cache.clear()
        page_3 = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(page_1, page_3)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'test_post{i}',
                group=cls.group,
                author=cls.author
            )

        cls.templates = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.group.slug]),
            reverse('posts:profile', args=[cls.author.username])
        ]

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        for address in PaginatorViewsTest.templates:
            with self.subTest():
                response = self.client.get(address)
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), settings.ITEMS_COUNT)

    def test_second_page_contains_three_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        for address in PaginatorViewsTest.templates:
            with self.subTest():
                response = self.client.get(address + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), 3)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='Irina')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(text='Тестовый пост',
                                       author=cls.user)

    def test_authorized_client_can_follow(self):
        """Авторизованный пользователь может подписываться."""
        follow = Follow.objects.filter(
            user=self.user, author=self.author).count()
        self.assertEqual(follow, 0)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        follow = Follow.objects.filter(
            user=self.user, author=self.author).count()
        self.assertEqual(follow, 1)

    def test_not_authorized_client_cannot_follow(self):
        """Неавторизованный пользователь не может подписываться."""
        response = self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Авторизуйтесь, чтобы оставить комментарий.')
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 0)

    def test_authorized_client_cannot_follow_twice(self):
        """Проверка наличия ограничения на подписку на уровне БД."""
        Follow.objects.create(user=self.user, author=self.author)
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 1)
        with self.assertRaises(Exception):
            Follow.objects.create(user=self.user, author=self.author)

    def test_authorized_client_cannot_follow_twice(self):
        """Проверка уникальности подписки авторизованного пользователя
         (вызов метода get_or_create во view-функции)."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        follow = Follow.objects.filter(
            user=self.user, author=self.author).count()
        self.assertEqual(follow, 1)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        follow = Follow.objects.filter(
            user=self.user, author=self.author).count()
        self.assertEqual(follow, 1)

    def test_authorized_client_can_unfollow(self):
        """Только авторизованный пользователь может отписываться."""
        Follow.objects.create(user=self.user, author=self.author)
        self.guest_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 1)
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author})
        )
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 0)

    def test_new_post_for_follower(self):
        """В ленте подписчика появляется новая запись автора,
         на которого он подписан."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author})
        )
        Post.objects.create(text='Пост для ленты', author=self.author)
        Post.objects.create(text='Пост для главной', author=self.user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertEqual(count, 1)
        author = response.context['page_obj'][0].author
        self.assertEqual(author, self.author)

    def test_new_post_for_not_follower(self):
        """Новая запись автора не появляется к ленте тех,
         кто на него не подписан."""
        follow = Follow.objects.all().count()
        self.assertEqual(follow, 0)
        Post.objects.create(text='Пост для ленты', author=self.author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertEqual(count, 0)


class ViewTestClass(TestCase):
    def test_page_not_found(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
