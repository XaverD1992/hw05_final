from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Ivan')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    def setUp(self):
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
            image=self.uploaded
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий',
        )
        self.urls = {
            'index': [
                'posts:index',
                None,
                'posts/index.html'],
            'group_posts': [
                'posts:group_posts',
                {'slug': self.group.slug},
                'posts/group_list.html'],
            'profile': [
                'posts:profile',
                {'username': self.post.author},
                'posts/profile.html'],
            'post_detail': [
                'posts:post_detail',
                {'post_id': self.post.id},
                'posts/post_detail.html'],
            'post_edit': [
                'posts:post_edit',
                {'post_id': self.post.id},
                'posts/create_post.html'],
            'post_create': [
                'posts:post_create',
                None,
                'posts/create_post.html']
        }
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def common_tests_for_fields_of_some_pages(self, response_context,
                                              is_page=True):
        if is_page:
            self.assertIsInstance(response_context.get('page_obj'), Page)
            post = response_context.get('page_obj')[0]
        else:
            post = response_context.get('post')
        self.assertIsInstance(post, Post)
        post_text_0 = post.text
        post_group_0 = post.group
        post_author_0 = post.author
        post_image_0 = post.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_image_0, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for page_name, kwargs, template in self.urls.values():
            with self.subTest(page_name):
                response = self.authorized_client.get(reverse(page_name,
                                                              kwargs=kwargs))
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.common_tests_for_fields_of_some_pages(response.context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.common_tests_for_fields_of_some_pages(response.context)
        self.assertEqual(response.context.get('group'), self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.common_tests_for_fields_of_some_pages(response.context)
        self.assertEqual(response.context.get('author'), self.post.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.common_tests_for_fields_of_some_pages(response.context,
                                                   is_page=False)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context.get('form')
                self.assertIsInstance(form, PostForm)
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        self.post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group)
        pages = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
        ]
        for adress in pages:
            with self.subTest(adress):
                response = self.authorized_client.get(adress)
                context = response.context.get('page_obj')
                self.assertIn(self.post, context)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем, чтобы созданный Пост с группой
           не попап в чужую группу."""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        posts_count = Post.objects.filter(group=self.group).count()
        Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user,
            group=group2)
        self.group = Post.objects.filter(group=self.group).count()
        self.assertEqual(self.group, posts_count, 'поста нет в другой группе')

    def test_comment_correct_context(self):
        """Авторизованный пользователь может создать комментарий и он появится
           на странице поста."""
        comments_count = Comment.objects.count()
        form_data_1 = {'text': 'Тестовый коммент'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data_1,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(text=form_data_1['text']).
                        exists())

    def test_check_cache(self):
        """Проверка кеша."""
        post = Post.objects.create(text='Тестовый текст 3',
                                        author=self.user,
                                        group=self.group)
        response = self.guest_client.get(reverse('posts:index'))
        post.delete()
        response_2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_3.content)

    def test_follow_page(self):
        """Авторизованный пользователь может подписываться на других
           пользователей и удалять их из подписок. Новая запись пользователя
           появляется в ленте тех, кто на него подписан и не появляется в
           ленте тех, кто не подписан."""
        self.user_2 = User.objects.create(username='Oleg')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context.get("page_obj")), 0)
        Follow.objects.get_or_create(user=self.user_2, author=self.post.author)
        response_2 = self.authorized_client_2.get(reverse
                                                  ('posts:follow_index'))
        self.assertEqual(len(response_2.context.get('page_obj')), 1)
        self.assertIn(self.post, response_2.context.get('page_obj'))

        self.user_3 = User.objects.create(username='Igor')
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)
        response_3 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response_3.context.get('page_obj'))

        Follow.objects.all().delete()
        response_4 = self.authorized_client_2.get(reverse
                                                  ('posts:follow_index'))
        self.assertEqual(len(response_4.context.get('page_obj')), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group',
                                         description='Тестовое описание')
        cls.REMAINDER = 3
        posts: list = []
        for i in range(settings.NUMBER_OF_POSTS_PER_PAGE + cls.REMAINDER):
            posts.append(Post(text=f'Тестовый текст {i}',
                              group=cls.group,
                              author=cls.user))
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj')),
                         settings.NUMBER_OF_POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), self.REMAINDER)
