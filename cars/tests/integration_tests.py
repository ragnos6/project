import io
import json
from unittest.mock import patch

from django.test import TestCase, RequestFactory, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, force_authenticate
from django.http import HttpResponse, FileResponse

# Импорты ваших view-объектов
from cars.views import (
    CustomAuthToken,
    export_data,
    import_data,
    report_api,
)


class AuthIntegrationTest(TestCase):
    def setUp(self):
        # Пользователь для теста аутентификации
        self.username = "manager"
        self.password = "strong-password-123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.factory = APIRequestFactory()

    def test_token_auth_success(self):
        view = CustomAuthToken.as_view()
        request = self.factory.post('/', {'username': self.username, 'password': self.password}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertTrue(isinstance(response.data['token'], str) and len(response.data['token']) > 0)

    def test_token_auth_wrong_credentials(self):
        view = CustomAuthToken.as_view()
        request = self.factory.post('/', {'username': self.username, 'password': 'wrong'}, format='json')
        response = view(request)
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.data)


class ImportExportIntegrationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('cars.views.ImportExportService.handle_export_response')
    @patch('cars.views.ImportExportService.export_data')
    def test_export_returns_file(self, mock_export_data, mock_handle_export):
        """
        Проверяем, что export_data view корректно возвращает attachment с именем файла,
        когда сервис handle_export_response отдаёт файловый объект.
        """
        # Заглушка: export_data возвращает датасеты (нам не важны их содержимое в тесте view)
        mock_export_data.return_value = ('ent_ds', 'veh_ds', 'trip_ds', 'zip')

        # Заглушка: handle_export_response возвращает файловый объект и имя
        fake_mem = io.BytesIO(b'fake-zip-content')
        mock_handle_export.return_value = (fake_mem, 'export_csv.zip')

        req = self.factory.get('/', {'enterprise_id': '1', 'start': '2020-01-01', 'end': '2020-01-31', 'file_format': 'zip'})

        response = export_data(req)

        # Ожидаем FileResponse с attachment
        self.assertEqual(response.status_code, 200)
        self.assertIn('Content-Disposition', response)
        self.assertIn('export_csv.zip', response['Content-Disposition'])

    @patch('cars.views.ImportExportService.import_json')
    def test_import_json_success(self, mock_import_json):
        """
        Проверяем, что import_data(view) вызывает ImportExportService.import_json
        при загрузке JSON-файла и возвращает успешный ответ.
        """
        factory = APIRequestFactory()

        content = b'{"Enterprise": [], "Vehicle": [], "Trip": []}'
        uploaded = SimpleUploadedFile("data.json", content, content_type="application/json")

        # создаём корректный multipart-запрос через DRF APIRequestFactory
        request = factory.post(
            '/',
            {'file_import': uploaded},
            format='multipart'
         )

        response = import_data(request)

        mock_import_json.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Импорт данных завершён", response.content.decode('utf-8'))


class ReportIntegrationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # создаём пользователя и аутентифицируемсь в тестах
        self.user = User.objects.create_user(username='report_user', password='pw12345')

    @patch('cars.views.ReportService.generate_report')
    def test_report_success(self, mock_generate):
        """
        Тестируем успешную генерацию отчёта через report_api (ожидаем 200).
        """
        mock_generate.return_value = {'report': {'rows': []}}

        request = self.factory.get('/', {'report_type': 'car_mileage', 'enterprise_id': '1', 'start_date': '2020-01-01', 'end_date': '2020-01-31'})
        # Привязываем пользователя к запросу, чтобы пройти аутентификацию DRF
        force_authenticate(request, user=self.user)

        response = report_api(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('report', response.data)

    @patch('cars.views.ReportService.generate_report')
    def test_report_error(self, mock_generate):
        """
        Тестируем сценарий, когда сервис возвращает {'error': ...} — ожидаем 400.
        """
        mock_generate.return_value = {'error': 'invalid params'}

        request = self.factory.get('/', {'report_type': 'unknown'})
        force_authenticate(request, user=self.user)

        response = report_api(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

