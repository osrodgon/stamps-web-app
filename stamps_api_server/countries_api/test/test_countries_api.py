import os
import pytest
from rest_framework import status

from countries_api.api.serializers.country_response_serializer import CountryResponseSerializer
from common.test.api_client import api_client
from common.test.countries_api_test_data import (
    countries_table,
    country_post_payload_ok,
    country_put_payload_ok,
)
from countries_api.models import Country


@pytest.mark.django_db
class TestCountriesAPI:
    """
    Test suite for the Countries API endpoints.
    """

    # region Helper Methods
    def _assert_successful_response(self, response, expected_message, expected_status_code):
        """Asserts the structure of a successful API response."""
        assert response.status_code == expected_status_code
        assert response.data['success'] is True
        assert response.data['message'] == expected_message
        assert response.data['errors'] is None
        assert response.data['data'] is not None

    def _assert_error_response(self, response, expected_status_code, expected_error_field=None, expected_error_code=None, expected_error_message=None):
        """Asserts the structure of a failed API response."""
        assert response.status_code == expected_status_code
        assert response.data['success'] is False
        assert response.data['message'] == "Request failed"
        assert response.data['data'] is None
        assert response.data['errors'] is not None

        if expected_error_field:
            assert response.data['errors'][0]['field'] == expected_error_field
        if expected_error_code:
            assert response.data['errors'][0]['code'] == expected_error_code
        if expected_error_message:
            assert expected_error_message in response.data['errors'][0]['message']
    # endregion

    def test_list_countries(self, api_client, countries_table):
        response = api_client.get(self.__get_url())
        
        original = CountryResponseSerializer(countries_table, many=True)
        
        assert len(response.json()['data']) == len(countries_table)
        assert response.json()['data'] == original.data
        assert response.json()['success'] == True
        assert response.json()['message'] == "Retrieved successfully"
        assert response.json()['errors'] == None
        assert response.status_code == status.HTTP_200_OK

    def test_create_country_success(self, api_client, list_create_url, country_post_payload_ok):
        response = api_client.post(list_create_url, country_post_payload_ok, format='json')
        self._assert_successful_response(response, "Created successfully", status.HTTP_201_CREATED)
        assert response.data['data']['name'] == country_post_payload_ok['name']
        assert Country.objects.count() == 1
        assert Country.objects.filter(name=country_post_payload_ok['name']).exists()

    def test_create_country_invalid_payload_blank(self, api_client, list_create_url):
        response = api_client.post(list_create_url, {'name': ''}, format='json')
        self._assert_error_response(response, status.HTTP_400_BAD_REQUEST, expected_error_field='name', expected_error_code='blank')
        assert Country.objects.count() == 0

    def test_create_country_invalid_payload_missing(self, api_client, list_create_url):
        response = api_client.post(list_create_url, {}, format='json')
        self._assert_error_response(response, status.HTTP_400_BAD_REQUEST, expected_error_field='name', expected_error_code='required')
        assert Country.objects.count() == 0

    def test_create_country_duplicate_name(self, api_client, countries_table, list_create_url):
        response = api_client.post(list_create_url, {'name': countries_table[0].name}, format='json')
        self._assert_error_response(response, status.HTTP_400_BAD_REQUEST, expected_error_field='name', expected_error_code='unique')
        assert Country.objects.count() == 2

    def test_retrieve_country_success(self, api_client, countries_table, detail_url):
        country_1 = countries_table[0]
        url = detail_url(country_1.pk)
        response = api_client.get(url)
        self._assert_successful_response(response, "Retrieved successfully", status.HTTP_200_OK)
        assert response.data['data']['id'] == country_1.pk
        assert response.data['data']['name'] == country_1.name

    def test_retrieve_country_not_found(self, api_client, detail_url):
        url = detail_url(999)
        response = api_client.get(url)
        self._assert_error_response(response, status.HTTP_404_NOT_FOUND, expected_error_message='not found')

    def test_update_country_success(self, api_client, countries_table, detail_url, country_put_payload_ok):
        country_1 = countries_table[0]
        url = detail_url(country_1.pk)
        response = api_client.put(url, country_put_payload_ok, format='json')
        self._assert_successful_response(response, "Updated successfully", status.HTTP_200_OK)
        assert response.data['data']['name'] == country_put_payload_ok['name']
        country_1.refresh_from_db()
        assert country_1.name == country_put_payload_ok['name']

    def test_update_country_not_found(self, api_client, detail_url, country_put_payload_ok):
        url = detail_url(999)
        response = api_client.put(url, country_put_payload_ok, format='json')
        self._assert_error_response(response, status.HTTP_404_NOT_FOUND, expected_error_message='not found')

    def test_update_country_invalid_payload(self, api_client, countries_table, detail_url):
        country_1 = countries_table[0]
        original_name = country_1.name
        url = detail_url(country_1.pk)
        response = api_client.put(url, {'name': ''}, format='json')
        self._assert_error_response(response, status.HTTP_400_BAD_REQUEST, expected_error_field='name', expected_error_code='blank')
        country_1.refresh_from_db()
        assert country_1.name == original_name

    def test_delete_country_success(self, api_client, countries_table, detail_url):
        country_1 = countries_table[0]
        url = detail_url(country_1.pk)
        response = api_client.delete(url)
        self._assert_successful_response(response, "Deleted successfully", status.HTTP_200_OK)
        assert 'Successfully deleted' in response.data['data']['message']
        assert Country.objects.count() == 1
        with pytest.raises(Country.DoesNotExist):
            Country.objects.get(pk=country_1.pk)

    def test_delete_country_not_found(self, api_client, countries_table, detail_url):
        url = detail_url(999)
        response = api_client.delete(url)
        self._assert_error_response(response, status.HTTP_404_NOT_FOUND, expected_error_message='not found')
        assert Country.objects.count() == 2
        
    def __get_url(self):
        return "/" + str(os.getenv("COUNTRIES_URL_V1"))