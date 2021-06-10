from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class StaticURLTests(TestCase):
    # Метод класса должен быть декорирован
    @classmethod
    def setUpClass(cls):
        # Вызываем родительский метод, чтобы не перезаписывать его полностью,
        # а расширить
        super().setUpClass()
        # Устанавливаем данные для тестирования
        # Создаём пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаём второй клиент, без авторизации
        cls.unauthorized_client = Client()

    def test_homepage(self):
        # Создаем экземпляр клиента
        # client = Client(). Клиент теперь есть в setUpClass()
        # Делаем запрос к главной странице и проверяем статус
        response = HttpResponse(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_force_login(self):
        self.client.force_login(self.user)
        response = HttpResponse(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        self.client.force_login(self.user)
        # Определим текущее количество записей в модели Post
        current_posts_count = Post.objects.count()
        # Создаём новую публикацию, отправляя данные POST-запросом
        # Разрешаем редирект после отправки данных
        response = self.client.post(reverse('new_post'),
                                    {'text': 'Это текст публикации'},
                                    follow=True)
        # Проверим, что после размещения поста клиент был успешно перенаправлен
        self.assertEqual(response.status_code, 200)
        # Убедимся, что в базе стало на одну публикацию больше, чем было
        self.assertEqual(Post.objects.count(),
                         current_posts_count + 1)

    def test_unauthorized_user_newpage(self):
        # Создаем экземпляр клиента
        # Авторизованного пользователя не создаём
        # client = Client(). Клиент теперь есть в setUpClass()
        # Запретим редирект, чтобы увидеть, какой статус вернёт страница /new/
        response = self.client.get(reverse('new_post'),
                                   follow=False)
        self.assertRedirects(response,
                             reverse('login') + '?next=' + reverse('new_post'),
                             status_code=302,
                             target_status_code=200)
