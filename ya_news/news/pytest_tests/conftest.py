from datetime import timedelta

import pytest
from django.conf import settings
from django.test.client import Client
from django.utils import timezone

from news.models import Comment, News


ONE_PIECE_OF_NEWS = 'Новость'


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def other_user_client(other_user):
    client = Client()
    client.force_login(other_user)
    return client


@pytest.fixture
def news():
    return News.objects.create(
        title='Заголовок',
        text='Текст новости',
        date=timezone.now(),
    )


@pytest.fixture
def comment(news, author):
    return Comment.objects.create(
        author=author,
        news=news,
        text='Текст комментария',
    )


@pytest.fixture
def list_of_news():
    today, news_list = timezone.now(), []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        test_news = News.objects.create(
            title=f'{ONE_PIECE_OF_NEWS} {index}',
            text='Текст новости',
        )
        test_news.date = today - timedelta(days=index)
        test_news.save()
        news_list.append(test_news)
    return news_list


@pytest.fixture
def list_of_comments(news, author):
    now = timezone.now()
    comment_list = []
    for index in range(2):
        test_comment = Comment.objects.create(
            author=author,
            news=news,
            text=f'Комментарий {index}',
        )
        test_comment.created = now + timedelta(days=index)
        test_comment.save()
        comment_list.append(test_comment)
    return comment_list
