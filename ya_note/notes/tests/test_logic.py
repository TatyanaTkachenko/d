from http import HTTPStatus

from pytils.translit import slugify
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteOperations(TestCase):
    NOTE_TITLE = 'Заголовок'
    NOTE_TEXT = 'Текст'
    NEW_NOTE_TITLE = 'Новый заголовок'
    NOTE_SLUG = 'slug'
    NEW_NOTE_TEXT = 'Новый текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)

        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )

        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')

    def test_create_note_by_auth(self):
        form_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'new-slug',
        }
        notes_count_before = Note.objects.count()
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.success_url)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)

        new_note = Note.objects.get(slug='new-slug')
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.text, form_data['text'])
        self.assertEqual(new_note.author, self.author)

    def test_create_note_by_anon(self):
        notes_count_before = Note.objects.count()
        self.client.post(self.add_url, data={'title': 'Тест', 'text': 'Тест'})
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_before, notes_count_after)

    def test_empty_slug(self):
        form_data = {
            'title': 'Заголовок без слага',
            'text': 'Текст',
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertRedirects(response, self.success_url)

        new_note = Note.objects.get(title=form_data['title'])
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_delete_note_by_author(self):
        notes_count_before = Note.objects.count()
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before - 1)

    def test_delete_note_by_another_user(self):
        notes_count_before = Note.objects.count()
        response = self.other_user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_edit_note_by_author(self):
        new_data = {
            'title': self.NEW_NOTE_TITLE,
            'text': self.NEW_NOTE_TEXT,
            'slug': self.NOTE_SLUG,
        }
        response = self.author_client.post(self.edit_url, data=new_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, new_data['title'])
        self.assertEqual(self.note.text, new_data['text'])
        self.assertEqual(self.note.slug, new_data['slug'])

    def test_edit_note_by_another_user(self):
        new_data = {
            'title': self.NEW_NOTE_TITLE,
            'text': self.NEW_NOTE_TEXT,
            'slug': self.NOTE_SLUG,
        }
        response = self.other_user_client.post(self.edit_url, data=new_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_slug_unique(self):
        form_data = {
            'title': 'Заголовок с повторяющимся слагом',
            'text': 'Текст',
            'slug': self.NOTE_SLUG,
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.NOTE_SLUG + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)
