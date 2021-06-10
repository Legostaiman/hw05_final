import unittest
from io import BytesIO, StringIO

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from posts.models import Group, Post, User
from posts.forms import PostForm
import logging
from django.core.files.uploadedfile import SimpleUploadedFile


class TestProfileCreate(TestCase):

    def test_profile_create(self):  # Это - test case.
        """Проверяем создается ли после регистрации пользователя
         его персональная страница (profile)"""
        # Создание нового пользователя
        user = User.objects.create_user(username='foo1',
                                        password='123')
        user.save()
        client = Client()
        # Запрос на страницу нового пользователя
        response = client.get(reverse('profile', args=[user]))
        status = response.status_code  # Проверка стасуса страницы
        # Проверка: идентичен ли результат вызова ожидаемому результату
        self.assertEqual(status, 200,
                         f'Страница пользователя не работает.\n'
                         f' Response.status_code {status}')
        user.delete()  # Удаляем созданого пользователя

    def test_user_create_post(self):
        """Авторизованный пользователь может опубликовать пост (new)"""
        client = Client()
        user = User.objects.create_user(username='foo2',
                                        password='123')
        client.force_login(user)
        # Определим текущее количество записей в модели Post
        current_posts_count = Post.objects.count()
        # Создаём новую публикацию, отправляя данные POST-запросом
        # Разрешаем редирект после отправки данных
        response = client.post(reverse('new_post'),
                               {'text': 'Это текст публикации'},
                               follow=True)
        # Проверим, что после размещения поста клиент был успешно перенаправлен
        self.assertEqual(response.status_code,
                         200,
                         f'Функция создания поста работает не правильно.\n'
                         f' Response.status_code {response.status_code}')
        self.assertEqual(Post.objects.count(),
                         current_posts_count + 1)
        user.delete()

    def test_unlogin_user_post(self):
        """Неавторизованный посетитель не может
         опубликовать пост (его редиректит на страницу входа)"""
        # Создаем экземпляр клиента
        # Авторизованного пользователя не создаём
        client = Client()
        # Запретим редирект, чтобы увидеть, какой статус вернёт страница /new/
        response = client.post(reverse('new_post'),
                               data={'text': 'Test_post',
                                     'group': 1},
                               follow=False)
        self.assertEqual(response.status_code,
                         302)

    def test_post_publication(self):
        """После публикации поста новая запись появляется на
        главной странице сайта (index), на персональной странице
        пользователя (profile), и на отдельной странице поста (post)"""
        client = Client()
        user = User.objects.create_user(username='foo3',
                                        password='123')
        client.force_login(user)
        group = Group(title='test', description='test', slug='test')
        group.save()
        client.post(reverse('new_post'),
                    data={'text': 'Это текст публикации',
                          'group': 1},
                    follow=True)
        post = Post.objects.get(author=user)
        responses = {'profile': [user],
                     'post': [user, post.pk],
                     'group': [group.slug]}
        response = client.get(reverse('index'))
        cache.clear()
        self.assertContains(response, post)
        for key, value in responses.items():
            if value is None:
                response = client.get(reverse(key))
                self.assertContains(response, post)
            else:
                response = client.get(reverse(key, args=value))
                self.assertContains(response, post)

    def test_post_edition(self):
        """Авторизованный пользователь может отредактировать свой пост,
        после этого содержимое поста изменится на всех связанных страницах."""
        client = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        client.force_login(user)
        group = Group(title='test', description='test', slug='test')
        group.save()
        client.post(reverse('new_post'),
                    {'text': 'Это текст публикации'},
                    follow=True)
        post = Post.objects.get(author=user)
        client.post(reverse('post_edit', args=[user, post.pk]),
                    {'text': 'Это изменённый текст публикации',
                     'group': 1},
                    follow=True)
        post_1 = Post.objects.get(author=user)
        cache.clear()
        response = client.get(reverse('index'))
        self.assertContains(response, post_1)
        responses = {'index': None,
                     'profile': [user],
                     'post': [user, post.pk],
                     'group': [group.slug]}

        for key, value in responses.items():
            cache.clear()
            response = client.get(reverse(key, args=value))
            self.assertContains(response, post_1)

    def test_404_error(self):
        """Данный тест проверяет возвращает ли сервер код 404,
         если страница не найдена."""
        client = Client()
        response = client.get('/404_error_page/')
        status = response.status_code
        self.assertEqual(status, 404)

    def test_img_post(self):
        client = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        client.force_login(user)
        # Тут начинает генерироваться изображение для теста
        file = BytesIO()
        img = Image.new('RGBA', (60, 30), color='red')
        img.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        # Тут прекращает генерироваться изображение для теста
        group = Group(title='test', description='test', slug='test')
        group.save()
        client.post(reverse('new_post'),
                    {'author': user,
                     'group': 1,
                     'text': 'post with image', 'image': file},
                    follow=True)
        cache.clear()
        group = Group.objects.get(slug='test')
        pages = {'index': None,
                 'profile': user,
                 'group': group}
        for x, y in pages.items():
            if y is None:
                request = client.get(reverse(x))
                self.assertContains(request, '<img')
            else:
                request = client.get(reverse(x, args=[y]))
                self.assertContains(request, '<img')

    def test_protect(self):
        client = Client()
        form = PostForm
        user = User.objects.create_user(username='foo1',
                                        password='123')
        client.force_login(user)
        image = SimpleUploadedFile('test.txt', b'this is text not image',
                                content_type='text/plain')
        request = client.post(reverse('new_post'),
                              {'author': user,
                               'text': 'post with image', 'image': image},
                              follow=True)
        self.assertFormError(request, 'form', 'image',
                             f'Загрузите правильное изображение. Файл, который'
                             f' вы загрузили, поврежден или не является '
                             f'изображением.')

    def test_cache_index(self):
        """Проверяем создается ли кеш главной страницы"""
        client = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        client.force_login(user)
        cache.clear()
        request = client.post(reverse('new_post'),
                              {'author': user,
                               'text': 'test_cache'},
                              follow=True)
        post = Post.objects.get(author=user)
        x = cache.get('index_page')
        x = cache._cache.keys()
        self.assertIn('index_page', f'{x}')

    def test_follow(self):
        """Проверка работы функции подписки"""
        client = Client()
        client_1 = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        user_1 = User.objects.create_user(username='foo2',
                                          password='123')
        client.force_login(user)
        cache.clear()
        client.post(reverse('new_post'),
                    {'author': user,
                     'text': 'test_post'},
                    follow=True)
        post = Post.objects.get(author=user)
        client_1.force_login(user_1)
        request_1 = client_1.post(reverse('profile_follow', args=[user]),
                                  follow=True)
        self.assertContains(request_1, post)

    def test_follow(self):
        """Проверка работы функции отписки"""
        client = Client()
        client_1 = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        user_1 = User.objects.create_user(username='foo2',
                                          password='123')
        client.force_login(user)
        cache.clear()
        client.post(reverse('new_post'),
                    {'author': user,
                     'text': 'test_post'},
                    follow=True)
        post = Post.objects.get(author=user)
        client_1.force_login(user_1)
        client_1.post(reverse('profile_follow', args=[user]),
                      follow=True)
        request_1 = client_1.post(reverse('profile_unfollow', args=[user]),
                                  follow=True)
        self.assertNotContains(request_1, post)

    def test_massage_feed(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
         подписан и не появляется в ленте тех, кто не подписан на него."""
        client = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        client.force_login(user)
        client.post(reverse('new_post'),
                    {'author': user,
                     'text': 'test_post'},
                    follow=True)
        post = Post.objects.get(author=user)
        client_1 = Client()
        user_1 = User.objects.create_user(username='foo2',
                                          password='123')
        client_1.force_login(user_1)
        request_1 = client_1.post(reverse('profile_follow', args=[user]),
                                  follow=True)
        self.assertContains(request_1, post)
        client_2 = Client()
        user_2 = User.objects.create_user(username='foo3',
                                          password='123')
        client_2.force_login(user_2)
        request_2 = client_2.post(reverse('follow_index'))
        self.assertNotContains(request_2, post)

    def test_log_user_post(self):
        """Только авторизированный пользователь может комментировать посты."""
        client = Client()
        user = User.objects.create_user(username='foo1',
                                        password='123')
        request = client.post(reverse('new_post'),
                    {'author': user,
                     'text': 'test_post'},
                    follow=True)
        self.assertContains(request, 'login')
