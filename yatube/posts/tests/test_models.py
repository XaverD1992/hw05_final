from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. Абвгд',
        )

    def setUp(self):
        self.group = PostModelTest.group

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        vals = (
            (self.post.text[:15], str(self.post)),
            (self.group.title, str(self.group)),
        )
        for value, expected in vals:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, expected
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(self.post._meta.get_field(field).help_text,
                                 expected)
