import shutil
import tempfile

from http import HTTPStatus
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
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
            author=cls.user,
            group=cls.group_one
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsFormsTest.user)

    def test_create_post_in_db(self):
        """Проверка созданиея нового поста с картинкой в БД."""
        posts_count = Post.objects.count()
        # Добавлено в 6 спринте
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
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.latest()
        comparison_dict = {
            form_data['text']: new_post.text,
            form_data['group']: new_post.group.id,
            self.user: new_post.author,
            # Добавлено в 6 спринте
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
        response = self.authorized_client.post(
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
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_create_post(self):
        """Неавторизованный пользователь не сможет создать пост."""
        posts_count = Post.objects.count()
        response = self.guest_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
