from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_comment_by_anon(client, news):
    url = reverse('news:detail', args=(news.id,))
    count_comments_before = Comment.objects.count()
    client.post(url, data={'text': 'Новый текст комментария'})
    assert count_comments_before == Comment.objects.count()


@pytest.mark.django_db
def test_comment_by_auth_user(author, news, author_client):
    new_comment_text = {'text': 'Новый текст'}
    count_comments_before = Comment.objects.count()
    url = reverse('news:detail', kwargs={'pk': news.pk})
    author_client.post(url, data=new_comment_text)
    assert count_comments_before + 1 == Comment.objects.count()

    comment = Comment.objects.filter(news=news, author=author).latest('created')
    assert comment.text == new_comment_text['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_using_bad_words(other_user_client, news):
    url = reverse('news:detail', args=(news.id,))
    count_comments_before = Comment.objects.count()
    text_data = {'text': f'Текст, {BAD_WORDS[0]}, дальше текст'}
    response = other_user_client.post(url, data=text_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert count_comments_before == Comment.objects.count()


@pytest.mark.django_db
def test_edit_comment_by_author(author_client, comment, news):
    edit_comment = {'text': 'Новый текст комментария'}
    news_url = reverse('news:detail', kwargs={'pk': news.pk})
    comment_url = reverse('news:edit', kwargs={'pk': comment.pk})

    response = author_client.post(comment_url, data=edit_comment)
    assertRedirects(response, news_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == edit_comment['text']


@pytest.mark.django_db
def test_delete_comment_by_author(author_client, comment, news):
    count_comments_before = Comment.objects.count()
    news_url = reverse('news:detail', kwargs={'pk': news.pk})
    comment_url = reverse('news:delete', kwargs={'pk': comment.pk})

    response = author_client.delete(comment_url)
    assertRedirects(response, news_url + '#comments')
    assert count_comments_before - 1 == Comment.objects.count()


@pytest.mark.django_db
def test_edit_comment_by_another_user(admin_client, comment):
    original_text = comment.text
    new_comment = {'text': 'Новый текст'}
    comment_url = reverse('news:edit', kwargs={'pk': comment.pk})

    response = admin_client.post(comment_url, data=new_comment)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text


@pytest.mark.django_db
def test_delete_comment_by_another_user(admin_client, comment):
    count_comments_before = Comment.objects.count()
    comment_url = reverse('news:delete', kwargs={'pk': comment.pk})

    response = admin_client.delete(comment_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert count_comments_before == Comment.objects.count()
