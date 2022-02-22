from django.test import TestCase
from ..models import Group, Post, User, Comment, Follow


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.some = User.objects.create_user(username='somebody')
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Текстовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Какой-то рандомно сгенерированный текст',
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

    def test_models_have_correct_object_names(self):
        """Проверка отображения текста поста и названия группы."""
        objs_dict = {
            str(self.post.text[:15]): self.post.text[:15],
            str(self.group.title): self.group.title
        }
        for string, value in objs_dict.items():
            with self.subTest(string=string):
                self.assertEqual(string, value)

    def test_verbose_name(self):
        """Verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        following = PostModelTest.following
        verbose_name_dict = {
            post._meta.get_field('text').verbose_name: 'Текст поста',
            post._meta.get_field('pub_date').verbose_name: 'Дата публикации',
            post._meta.get_field('author').verbose_name: 'Автор',
            post._meta.get_field('group').verbose_name: 'Группа',
            group._meta.get_field('title').verbose_name: 'Название группы',
            group._meta.get_field('slug').verbose_name: 'Ссылка на группу',
            group._meta.get_field('description').verbose_name: (
                'Описание группы'
            ),
            comment._meta.get_field('post').verbose_name: (
                'Комментарий к посту'
            ),
            comment._meta.get_field('author').verbose_name: (
                'Автор комментария'
            ),
            comment._meta.get_field('text').verbose_name: 'Текст комментария',
            following._meta.get_field('user').verbose_name: 'Подписчик',
            following._meta.get_field('author').verbose_name: (
                'Автор, на которого подписываться'
            )
        }
        for parametr, value in verbose_name_dict.items():
            with self.subTest(parametr=parametr):
                self.assertEqual(parametr, value)

    def test_help_text(self):
        """Help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        following = PostModelTest.following
        help_text_dict = {
            post._meta.get_field('text').help_text: 'Введите текст поста',
            post._meta.get_field('pub_date').help_text: (
                'Дата публикации поста'
            ),
            post._meta.get_field('author').help_text: 'Автора поста',
            post._meta.get_field('group').help_text: (
                'Группа, к которой будет относиться пост'
            ),
            group._meta.get_field('title').help_text: (
                'Задайте название группы'
            ),
            group._meta.get_field('slug').help_text: (
                'Задайте ссылку на группу'
            ),
            group._meta.get_field('description').help_text: (
                'Задайте описание группы'
            ),
            comment._meta.get_field('post').help_text: (
                'Напишите комментарий'
            ),
            comment._meta.get_field('author').help_text: (
                'Задайте автора комментария'
            ),
            comment._meta.get_field('text').help_text: (
                'Введите текст комментария'
            ),
            following._meta.get_field('user').help_text: (
                'Задайте описание подписчика'
            ),
            following._meta.get_field('author').help_text: (
                'Задайте автора'
            )
        }
        for parametr, value in help_text_dict.items():
            with self.subTest(parametr=parametr):
                self.assertEqual(parametr, value)
