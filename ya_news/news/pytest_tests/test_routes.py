from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, client_fixture, expected_status, pk_required',
    [
        ('news:home', 'client', HTTPStatus.OK, False),
        ('users:login', 'client', HTTPStatus.OK, False),
        ('users:logout', 'client', HTTPStatus.OK, False),
        ('users:signup', 'client', HTTPStatus.OK, False),
        ('news:detail', 'client', HTTPStatus.OK, True),
        ('news:edit', 'other_user_client', HTTPStatus.NOT_FOUND, True),
        ('news:edit', 'author_client', HTTPStatus.OK, True),
        ('news:delete', 'other_user_client', HTTPStatus.NOT_FOUND, True),
        ('news:delete', 'author_client', HTTPStatus.OK, True),
    ]
)
def test_status_codes(request, name, client_fixture, expected_status,
                      pk_required, comment, news):
    client = request.getfixturevalue(client_fixture)
    kwargs = {'pk': news.pk if name
              == 'news:detail' else comment.pk} if pk_required else {}
    #строка 26 Нужно избавиться от ветвлений, 
    # удачно reverse вынести в фикстуры, 
    # тогда их можно будет использовать в параметрах.
    url = reverse(name, kwargs=kwargs)
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_redirect_for_anon(client, name, comment):
    login_url = reverse('users:login')
    url = reverse(name, kwargs={'pk': comment.pk})
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
