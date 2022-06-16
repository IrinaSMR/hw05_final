from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Group, Post, User

NEW_TEXT = 'Новый пост'
UPDATED_TEXT = 'Обновленный текст'


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Irina')
        cls.group = Group.objects.create(
            title=('Название тестовой группы'),
            slug='night',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст тестового поста'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'group': PostFormTests.group.id,
            'text': NEW_TEXT
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[PostFormTests.user]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text=NEW_TEXT).exists())

    def test_post_edit(self):
        form_data = {
            'group': self.group.id,
            'text': UPDATED_TEXT,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        result = Post.objects.get(id=self.post.id)
        self.assertEqual(result.text, UPDATED_TEXT)

    def test_post_with_image(self):
        count_posts = Post.objects.count()
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
        form_data = {
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=[PostFormTests.user.username])
        )


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.guest_client = Client()
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.user)
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='test_post',
            author=cls.user
        )

    def test_auth_user_can_comment(self):
        """Авторизованный пользователь может комментировать посты"""
        post = Post.objects.first()
        form_data = {
            'text': 'Комментарий от авторизованного пользователя'
        }

        self.authorized_not_author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists())
        response = CommentTest.authorized_not_author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        comment = Comment.objects.last()
        self.assertIn(
            comment, response.context['comments'], 'Комментарий отсутствует')

    def test_guest_user_cannot_comment(self):
        """Неавторизованный пользователь не может
         оставлять комментарии"""
        post = Post.objects.first()
        form_data = {
            'text': 'Комментарий от неавторизованного пользователя'
        }
        CommentTest.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.last()
        self.assertEqual(
            comment, None)
