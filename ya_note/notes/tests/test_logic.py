from pytils.translit import slugify
from http import HTTPStatus

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
#строка 53 Недопустимо сравнивать с литералом
#Нет гарантии, что выбрали правильно, перед сохранением
#  в БД вью функция может искажать данные
# Вариант 1. Создать условия, при которых ДО 
# отправки формы в БД гарантированно пусто, нет ни одной заметки
# Вариант 2. Узнать какие в БД есть заметки ДО отправки формы, 
# выбрать из БД все заметки ПОСЛЕ отправки формы, из <все заметки>
#  вычесть <заметки ДО>, если в результате осталась одна заметка, 
# это то что мы ищем.
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
    # строка 81 аналогично строке 53 замечание
        expected_slug = slugify(form_data['title'])
    #строка 83 Если заголовок будет длиннее 100 символов, тест провалится. 
    # Обрати внимание как формируется слаг в модели.
        self.assertEqual(new_note.slug, expected_slug)

    def test_delete_note_by_author(self):
        notes_count_before = Note.objects.count()   # строка 89 Избыточно
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())
        notes_count_after = Note.objects.count()  # строка 93 Избыточно        
        self.assertEqual(notes_count_after, notes_count_before - 1)  # строка 94 Избыточно
    
    def test_delete_note_by_another_user(self):
        notes_count_before = Note.objects.count()   # строка 97 Избыточно
        response = self.other_user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())
        notes_count_after = Note.objects.count()   # строка 101 Избыточно
        self.assertEqual(notes_count_after, notes_count_before)  # строка 102 Избыточно

    def test_edit_note_by_author(self):
        new_data = {
            'title': self.NEW_NOTE_TITLE,
            'text': self.NEW_NOTE_TEXT,
            'slug': self.NOTE_SLUG,
        }
        response = self.author_client.post(self.edit_url, data=new_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        #  строка 112 Нужно ещё проверить, что автор заметки не изменился,
        #  т.е. остался таким же каким и был до редактирования
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
        #  строка 128 Нужно ещё проверить, что автор заметки не изменился,
        #  т.е. остался таким же каким и был до редактирования
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        # строка 130 Нужно явно проверить, что заголовок не изменился. 
        # Удачно отказаться от refresh_from_db в 128 строке 
        # и использовать get, так у нас будет две версии заметки, 
        # версия ДО и версия ПОСЛЕ, можно явно сравнивать их атрибуты.
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
