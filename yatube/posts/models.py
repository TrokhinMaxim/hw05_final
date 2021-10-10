from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField('Описание')

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = ('Группа')
        verbose_name_plural = ('Группы')


class Post(models.Model):
    text = models.TextField('Текст')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts")
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-pub_date"]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        related_name="comments",
        blank=True,
        null=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments")
    text = models.TextField("Текст комментария")
    created = models.DateTimeField("Дата комментария", auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name="follower",
        on_delete=None
    )
    author = models.ForeignKey(
        User,
        related_name="following",
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Фолловер: '{self.user}', Автор: '{self.author}'"
