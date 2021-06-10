from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField("Название группы", max_length=200)
    description = models.TextField()
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return f"{format(self.title)}"


class Post(models.Model):
    objects = None
    text = models.TextField()
    pub_date = models.DateTimeField("date published",
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="author_posts"
                               )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text


class Comment(models.Model):
    objects = None
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name="comments")  # Здесь нужно исправить налл
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="comments")  # Здесь нужно исправить налл
    text = models.TextField()
    created = models.DateTimeField("date published",
                                   auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.text


class Follow(models.Model):
    objects = None
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")  # Кто подписывается
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING,
                               related_name="following")  # На кого подписывается
    subscribe_date = models.DateTimeField("date published",
                                          auto_now_add=True,
                                          db_index=True)
    following = models.BooleanField(default=False)

    class Meta:
        ordering = ["-subscribe_date"]
        unique_together = ['user']
