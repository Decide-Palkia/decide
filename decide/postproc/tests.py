from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods


class PostProcTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)

    def tearDown(self):
        self.client = None

    def test_identity(self):
        data = {
            'type': 'IDENTITY',
            'options': [
                { 'option': 'Option 1', 'number': 1, 'votes': 5 },
                { 'option': 'Option 2', 'number': 2, 'votes': 0 },
                { 'option': 'Option 3', 'number': 3, 'votes': 3 },
                { 'option': 'Option 4', 'number': 4, 'votes': 2 },
                { 'option': 'Option 5', 'number': 5, 'votes': 5 },
                { 'option': 'Option 6', 'number': 6, 'votes': 1 },
            ]
        }

        expected_result = [
            { 'option': 'Option 1', 'number': 1, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 5', 'number': 5, 'votes': 5, 'postproc': 5 },
            { 'option': 'Option 3', 'number': 3, 'votes': 3, 'postproc': 3 },
            { 'option': 'Option 4', 'number': 4, 'votes': 2, 'postproc': 2 },
            { 'option': 'Option 6', 'number': 6, 'votes': 1, 'postproc': 1 },
            { 'option': 'Option 2', 'number': 2, 'votes': 0, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhondt1(self):
        data = {
            'type': 'DHONDT',
            'seats': 12,
            'options': [
                { 'option': 'Partido 1', 'number': 1, 'votes': 50 },
                { 'option': 'Partido 2', 'number': 2, 'votes': 10 },
                { 'option': 'Partido 3', 'number': 3, 'votes': 34 },
                { 'option': 'Partido 4', 'number': 4, 'votes': 25 },
                { 'option': 'Partido 5', 'number': 5, 'votes': 56 },
                { 'option': 'Partido 6', 'number': 6, 'votes': 170 },
            ]
        }

        expected_result = [
            { 'option': 'Partido 6', 'number': 6, 'votes': 170, 'postproc': 6 },
            { 'option': 'Partido 5', 'number': 5, 'votes': 56, 'postproc': 2 },
            { 'option': 'Partido 1', 'number': 1, 'votes': 50, 'postproc': 2 },
            { 'option': 'Partido 3', 'number': 3, 'votes': 34, 'postproc': 1 },
            { 'option': 'Partido 4', 'number': 4, 'votes': 25, 'postproc': 1 },
            { 'option': 'Partido 2', 'number': 2, 'votes': 10, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)

    def test_dhondt2(self):
        data = {
            'type': 'DHONDT',
            'seats': 17,
            'options': [
                { 'option': 'Partido 1', 'number': 1, 'votes': 50 },
                { 'option': 'Partido 2', 'number': 2, 'votes': 10 },
                { 'option': 'Partido 3', 'number': 3, 'votes': 34 },
                { 'option': 'Partido 4', 'number': 4, 'votes': 25 },
                { 'option': 'Partido 5', 'number': 5, 'votes': 56 },
                { 'option': 'Partido 6', 'number': 6, 'votes': 1000000 },
            ]
        }

        expected_result = [
            { 'option': 'Partido 6', 'number': 6, 'votes': 1000000, 'postproc': 17 },
            { 'option': 'Partido 5', 'number': 5, 'votes': 56, 'postproc': 0 },
            { 'option': 'Partido 1', 'number': 1, 'votes': 50, 'postproc': 0 },
            { 'option': 'Partido 2', 'number': 2, 'votes': 10, 'postproc': 0 },
            { 'option': 'Partido 3', 'number': 3, 'votes': 34, 'postproc': 0 },
            { 'option': 'Partido 4', 'number': 4, 'votes': 25, 'postproc': 0 },
        ]

        response = self.client.post('/postproc/', data, format='json')
        self.assertEqual(response.status_code, 200)

        values = response.json()
        self.assertEqual(values, expected_result)
