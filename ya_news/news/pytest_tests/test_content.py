import pytest

from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_on_home_page(client, list_of_news):
    response = client.get(reverse('news:home'))
    news_count = response.context['object_list'].count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_sorted(client, list_of_news):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_sorted(client, news, list_of_comments):
    response = client.get(reverse('news:detail', args=(news.id,)))
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_date_created = [comment.created for comment in all_comments]
    sorted_date = sorted(all_date_created)
    assert all_date_created == sorted_date


@pytest.mark.django_db
def test_detail_form_for_anon(client, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_detail_form_for_auth(other_user_client, news):
    url = reverse('news:detail', args=(news.id,))
    response = other_user_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
