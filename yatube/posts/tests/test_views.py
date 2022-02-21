from http import HTTPStatus
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from ..forms import PostForm
from ..models import Follow, Post, Group, User, Comment
from yatube.settings import P_ON_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Добавлено в 6 спринте
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='название',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.post = Post.objects.create(
            text='тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.pages_name_and_template = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile', kwargs={'username': cls.user}
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ), 'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ), 'posts/create_post.html'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.user)
        cache.clear()

    def test_correct_template_for_pages(self):
        """Проверка использования ожимаемых шаблонов."""
        for page_name, template in self.pages_name_and_template:
            with self.subTest(page_name=page_name):
                response = self.authorized_client.get(page_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_home_page(self):
        """Проверка контекста главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('title', response.context)
        title_index = response.context['title']
        first_object = response.context['page_obj'][0]
        self.assertEqual(title_index, 'Последние обновления на сайте')
        self.assertEqual(first_object, self.post)
        # спринт 6: проверка появления картинки на главной странице
        self.assertEqual(first_object.image, self.post.image)

    # Добавлено в 6 спринте:
    def test_cache_index_page(self):
        """Тестирование использование кеширования"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(id=self.post.id)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)

    def test_correct_context_group_list(self):
        """Проверка контекста на странице с постами группы."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_post = response.context['page_obj'][0]
        post_group = first_post.group.title
        self.assertEqual(first_post, self.post)
        self.assertEqual(post_group, 'название')
        # спринт 6: проверка появления картинки на странице группы
        self.assertEqual(first_post.image, self.post.image)

    def test_correct_context_profile(self):
        """Проверка контекста на странице атора."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_post = response.context['page_obj'][0]
        author_post = first_post.author.username
        self.assertEqual(first_post, self.post)
        self.assertEqual(author_post, 'auth')
        # спринт 6: проверка появления картинки на странице профайла
        self.assertEqual(first_post.image, self.post.image)

    def test_correct_context_post_detail(self):
        """Проверка контекста страницы поста."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        test_post = response.context['post']
        title_post_detail = test_post.text
        self.assertEqual(test_post, self.post)
        self.assertEqual(title_post_detail, 'тестовый пост')
        # спринт 6: проверка появления картинки на странице поста
        self.assertEqual(test_post.image, self.post.image)

    def test_correct_form_create_post(self):
        """Проверка формы создания поста."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(
            response.context['form'], PostForm
        )

    def test_post_edit(self):
        """Проверка редактирования поста с правильным id."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        text_field = response.context['form'].initial['text']
        self.assertEqual(text_field, self.post.text)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Alex')
        cls.group = Group.objects.create(
            title='название',
            slug='test_slug',
            description='тестовое описание'
        )
        batch_size = 13
        objs = (Post(
            text=f'тестовый пост номер: {number}',
            author=cls.user,
            group=cls.group
        ) for number in range(batch_size))
        batch = list(objs)
        Post.objects.bulk_create(batch, batch_size)
        cls.url_amount_posts = {
            reverse('posts:index'): P_ON_PAGE,
            reverse('posts:index') + '?page=2': batch_size - P_ON_PAGE,
            reverse('posts:group_list', args=('test_slug',)): P_ON_PAGE,
            reverse('posts:group_list', args=('test_slug',)) + '?page=2': (
                batch_size - P_ON_PAGE
            ),
            reverse('posts:profile', args=(cls.user,)): P_ON_PAGE,
            reverse('posts:profile', args=(cls.user,)) + '?page=2': (
                batch_size - P_ON_PAGE
            )
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorTest.user)

    def test_paginator(self):
        """Проверка паджинатора на стриницах index, group_list и profile."""
        for url, quantity in self.url_amount_posts.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), quantity
                )


class ThirdTaskTest(TestCase):
    """Проверьте, что если при создании поста указать группу,
    то этот пост появляется:
    * на главной странице сайта,
    * на странице выбранной группы,
    * в профайле пользователя.
    Проверьте, что этот пост не попал в группу, для которой не предназначался.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.group_one = Group.objects.create(
            title='название',
            slug='group_slug',
            description='тестовое описание'
        )
        cls.group_two = Group.objects.create(
            title='название',
            slug='some_slug',
            description='тестовое описание'
        )
        cls.post = Post.objects.create(
            text='какой-то созданный текст',
            author=cls.user,
            group=cls.group_one
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ThirdTaskTest.user)

    def test_post_exist_on_page_index(self):
        """Пост появился на странице index."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response.context['page_obj'][0], self.post
        )
        self.assertEqual(
            response.context['page_obj'][0].group, self.post.group
        )

    def test_post_exist_on_page_of_group(self):
        """Пост появился на странице группы."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'group_slug'})
        )
        obj = response.context['page_obj'][0]
        obj_slug = obj.group.slug
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj_slug, self.group_one.slug)

    def test_post_exist_on_page_of_profile(self):
        """Пост появился в профайле пользователя."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        obj = response.context['page_obj'][0]
        author_obj = obj.author.username
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(author_obj, self.post.author.username)

    def test_does_not_exist_in_another_group(self):
        """Пост не появился в другой группе"""
        self.assertFalse(
            Post.objects.filter(
                text=self.post.text,
                group=self.group_two
            ).exists()
        )


# Добавлено в 6 спринте
class CommetsAndFollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # не подписанный юзер
        cls.not_follower = User.objects.create_user(username='not_foll')
        # комментрирующий и подписанный юзер
        cls.some = User.objects.create_user(username='somebody')
        # автор поста (на, которого подписан юзер somebody)
        cls.author = User.objects.create_user(username='Nameless')
        cls.post = Post.objects.create(
            text='какой-то созданный текст',
            author=cls.author
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.some,
            text='great'
        )
        cls.following = Follow.objects.create(
            user=cls.some,
            author=cls.author
        )

    def setUp(self):
        self.guest_client = Client()
        self.not_foll_client = Client()
        self.not_foll_client.force_login(CommetsAndFollowTest.not_follower)
        self.some_client = Client()
        self.some_client.force_login(CommetsAndFollowTest.some)
        self.author_client = Client()
        self.author_client.force_login(CommetsAndFollowTest.author)

    def test_onle_authorized_user_can_comment(self):
        """Неавторизованный пользователь не может
        комментировать и подписываться.
        """
        url_redirect = {
            reverse('posts:add_comment', args=(self.post.id,)): (
                f'/auth/login/?next=/posts/{self.post.id}/comment/'
            ),
            reverse(
                'posts:profile_follow', args=(self.author,)
            ): (
                f'/auth/login/?next=/profile/{self.author}/follow/'
            )
        }
        for url, redirected in url_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, redirected)

    def test_comment_exist_on_post_detail_page(self):
        """Комментарий появился на странице поста."""
        response = self.some_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertIn('comments', response.context)
        comment_post = response.context['comments'][0]
        self.assertEqual(self.comment, comment_post)

    def test_new_post_appear_for_follower(self):
        """Новая запись появляется в ленте подписчиков."""
        posts_count = Post.objects.count()
        response = self.some_client.get(reverse('posts:follow_index'))
        new_post_count = len(response.context['page_obj'])
        self.assertEqual(new_post_count, posts_count)
        follow_post = response.context['page_obj'][0]
        self.assertEqual(follow_post, self.post)

    def test_post_dosnt_appear_for_not_follower(self):
        """Новая запись не появляется у не подписанных."""
        response = self.not_foll_client.get(reverse('posts:follow_index'))
        new_post_count = len(response.context['page_obj'])
        self.assertIs(new_post_count, 0)
