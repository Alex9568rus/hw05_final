import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.some = User.objects.create_user(username='somebody')
        cls.author = User.objects.create_user(username='Nameless')
        cls.group_one = Group.objects.create(
            title='название',
            slug='test-slug',
            description='тестовое описание'
        )
        cls.group_two = Group.objects.create(
            title='New group',
            slug='New_slug',
            description='New_description'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group_one
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.foll_client = Client()
        self.foll_client.force_login(PostsFormsTest.follower)
        self.some_client = Client()
        self.some_client.force_login(PostsFormsTest.some)
        self.author_client = Client()
        self.author_client.force_login(PostsFormsTest.author)

    def test_create_post_in_db(self):
        """Проверка созданиея нового поста с картинкой в БД."""
        posts_count = Post.objects.count()
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
            'text': 'Тестовый текст',
            'group': self.group_one.id,
            'image': uploaded
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest()
        comparison_dict = {
            form_data['text']: new_post.text,
            form_data['group']: new_post.group.id,
            self.author: new_post.author,
            form_data['image']: uploaded
        }
        for field, new_field in comparison_dict.items():
            with self.subTest(field=field):
                self.assertEqual(field, new_field)

    def test_change_post_id_in_db(self):
        """Проверка редактирование поста в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Update post',
            'group': self.group_two.id
        }
        self.author_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        change_post = Post.objects.get(id=self.post.id)
        compar_dict = {
            form_data['text']: change_post.text,
            form_data['group']: change_post.group.id
        }
        for field, new_field in compar_dict.items():
            with self.subTest(field=field):
                self.assertEqual(field, new_field)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_cant_create_post(self):
        """Неавторизованный пользователь не сможет создать пост."""
        form_data = {
            'text': 'Ничего не получится',
            'author': self.author,
            'group': self.group_one
        }
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_count = Post.objects.count()
        self.assertEqual(posts_count, new_count)
        self.assertNotIn('post', response.context)

    def test_guest_cant_create_comment(self):
        """Неавторизованный пользователь не может комментировать."""
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.some,
            'text': 'комментарий, которого не будет'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
            )
        self.assertNotIn('comment', response.context)
        new_count = Comment.objects.count()
        self.assertEqual(comments_count, new_count)

    def test_guest_cant_follow(self):
        """Неавторизованный пользователь не может подписаться."""
        following_count = Follow.objects.count()
        form_data = {
            'user': 'user_1',
            'author': self.author
        }
        response = self.guest_client.post(
            'posts:profile_follow', args=(self.author,),
            data=form_data,
            follow=True
        )
        new_count = Follow.objects.count()
        self.assertNotIn('following', response.context)
        self.assertEqual(following_count, new_count)

    def test_authorized_user_can_create_comment(self):
        """Авторизованный пользователь может оставить комментарий."""
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.some,
            'text': 'awesome'
        }
        self.some_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        new_comment = Comment.objects.latest('id')
        comp_dict = {
            form_data['author']: new_comment.author,
            form_data['post']: new_comment.post,
            form_data['text']: new_comment.text
        }
        for field, value in comp_dict.items():
            with self.subTest(field=field):
                self.assertEqual(field, value)
        new_count = Comment.objects.count()
        self.assertEqual(new_count, comments_count + 1)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        following_count = Follow.objects.count()
        form_data = {
            'user': self.follower,
            'author': self.author
        }
        self.foll_client.post(
            reverse('posts:profile_follow', args=(self.author.username,)),
            data=form_data,
            follow=True
        )
        new_follower = Follow.objects.latest('id')
        comp_dict = {
            self.follower: new_follower.user,
            self.author: new_follower.author
        }
        for field, value in comp_dict.items():
            with self.subTest(field=field):
                self.assertEqual(field, value)
        new_count = Follow.objects.count()
        self.assertEqual(new_count, following_count + 1)

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        foll_count = Follow.objects.count()
        self.foll_client.get(
            reverse('posts:profile_unfollow', args=(self.author.username,))
        )
        new_count = Follow.objects.count()
        self.assertEqual(new_count, foll_count - 1)
