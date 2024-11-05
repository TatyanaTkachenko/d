from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.note_author = Note.objects.create(
            author=cls.author,
            title='Заголовок',
            text='Текст',
            slug='Slug_author'
        )
        cls.urls = (
            ('notes:add', None),
            ('notes:edit', (cls.note_author.slug,)),
        )

    def test_note_in_object_list(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertIn(self.note_author, object_list)

    def test_availability_notes_for_different_users(self):
        other_user = User.objects.create(username='Другой пользователь')
        self.client.force_login(other_user)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        self.assertNotIn(self.note_author, object_list)

    def test_form_in_pages(self):
        self.client.force_login(self.author)
        for name, args in self.urls:
            with self.subTest(user=self.author, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                # Проверка, что форма присутствует и её тип соответствует ожидаемому
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
