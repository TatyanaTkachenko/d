from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='Slug',
            author=cls.author
        )

    def test_pages_availability(self):
        routes = [
            # (name, args, client, expected_status)
            ('notes:home', None, self.client, HTTPStatus.OK),
            ('users:signup', None, self.client, HTTPStatus.OK),
            ('users:login', None, self.client, HTTPStatus.OK),
            ('users:logout', None, self.client, HTTPStatus.OK),
            ('notes:list', None, self.author, HTTPStatus.OK),
            ('notes:add', None, self.author, HTTPStatus.OK),
            ('notes:success', None, self.author, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), self.author, HTTPStatus.OK),
            ('notes:edit', (self.note.slug,), self.author, HTTPStatus.OK),
            ('notes:delete', (self.note.slug,), self.author, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), self.other_user, HTTPStatus.NOT_FOUND),
            ('notes:edit', (self.note.slug,), self.other_user, HTTPStatus.NOT_FOUND),
            ('notes:delete', (self.note.slug,), self.other_user, HTTPStatus.NOT_FOUND),
        ]

        for name, args, user, expected_status in routes:
            if user != self.client:
                self.client.force_login(user)
            url = reverse(name, args=args)
            with self.subTest(name=name, user=user):
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_redirect_for_anon(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None)
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
