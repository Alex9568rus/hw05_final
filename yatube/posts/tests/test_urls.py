from http import HTTPStatus
from django.test import TestCase, Client

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='тестовый пост',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test-slug',
            description='текстовое описание'
        )
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.id}/', 'posts/post_detail.html')
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html')
        )

    def setUp(self):
        self.guest_client = Client()
        self.not_author = User.objects.create_user('SomeOne')
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_public_urls(self):
        """Проверка доступности публичных страниц и их шаблонов."""
        for url, template in PostsURLTests.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_redirecting_guest(self):
        """Перенаправление неавторизованного пользователя"""
        redirect_dict = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/':
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        }
        for url, way in redirect_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, way)

    def test_private_urls(self):
        """Проверка доступности страниц для авторизованного
        пользователя и их шаблонов.
        """
        for url, template in PostsURLTests.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_author_access(self):
        """Доступ к редактированию только у автора"""
        response = self.not_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_unexisting_page(self):
        """Тест для несуществующей страницы."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Добавлено в 6 спринте (Финальное задание 1)
        self.assertTemplateUsed(response, 'core/404.html')
