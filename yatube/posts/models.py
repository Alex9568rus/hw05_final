from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Задайте название группы'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Ссылка на группу',
        help_text='Задайте ссылку на группу'
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Задайте описание группы'
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        help_text='Дата публикации поста',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Автора поста',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        get_latest_by = 'pub_date'
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Комментарий к посту',
        help_text='Напишите комментарий',
        related_name='comments',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        help_text='Задайте автора комментария',
        related_name='comments',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        help_text='Задайте описание подписчика',
        related_name='follower',
        null=True,
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор, на которого подписываться',
        help_text='Задайте автора',
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_links'
            ),
        ]
