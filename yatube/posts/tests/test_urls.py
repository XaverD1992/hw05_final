from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post, User

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create(username='NoName')
        cls.user2 = User.objects.create(username='NoName2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост',
        )
        cls.templates_public = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user1}/',
            f'/posts/{cls.post.id}/',
        ]

        cls.templates_private = [
            f'/posts/{cls.post.id}/edit/',
            '/create/'
        ]

        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user1.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(PostURLTests.user1)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(PostURLTests.user2)

    def test_public_urls_exists_for_guests_at_desired_location(self):
        """Публичные страницы доступны для неавторизованного пользователя
           по ожидаемому адресу."""
        for adress in self.templates_public:
            with self.subTest(adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_all_urls_exists_for_auth_at_desired_location(self):
        """Все страницы доступны для авторизованного пользователя-автора
           тестового поста по ожидаемому адресу."""
        templates_all_pages = self.templates_public + self.templates_private
        for adress in templates_all_pages:
            with self.subTest(adress):
                response = self.authorized_client_1.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_urls_redirect_anonymous_on_auth_login(self):
        """Приватные страницы перенаправляют неавторизованного пользователя
           на страницу авторизации."""
        pages = {'/create/': '/auth/login/?next=/create/',
                 f'/posts/{self.post.id}/edit/':
                 f'/auth/login/?next=/posts/{self.post.id}/edit/'}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_edit_url_redirect_not_author_on_post_detail_url(self):
        """Страница редактирования поста перенаправляет авторизованного
            пользователя при попытке редактирования чужого поста"""
        post = Post.objects.create(
            author=self.user1,
            text='NewТестовый пост',
        )
        response = self.authorized_client_2.get(f'/posts/{post.id}/edit/')
        self.assertRedirects(
            response,
            f'/posts/{post.id}/'
        )

    def test_unexisting_page_at_desired_location(self):
        """Страница /unexisting_page/ должна выдать ошибку."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_1.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_404_returns_customized_template(self):
        """Cтраница 404 отдаёт кастомный шаблон"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
