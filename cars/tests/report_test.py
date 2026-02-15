from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta

from cars.models import (
    Enterprise, Driver, Model, Vehicle,
    VehicleDocumentation, VehicleDriver, Trip,
    Manager
)


class ReportApiIntegrationTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Пользователь и менеджер
        self.user = User.objects.create_user(
            username="manager",
            password="pass123"
        )
        self.client.login(username="manager", password="pass123")

        # Создание предприятия
        self.enterprise = Enterprise.objects.create(
            name="Enterprise A",
            city="Moscow",
            timezone="Europe/Moscow"
        )

        # Создание менеджера и привязка к предприятию
        self.manager = Manager.objects.create(user=self.user)
        self.manager.enterprises.add(self.enterprise)

        # Документация автомобиля
        self.documentation = VehicleDocumentation.objects.create(
            vin_number="12345678901234567",
            pts_number="PTS000111222",
            reg_number="A111BC77",
            registration_date="2020-01-01",
            owner_name="John Doe"
        )

        # Водитель
        self.driver = Driver.objects.create(
            name="Иванов Иван",
            age=35,
            salary=60000,
            enterprise=self.enterprise
        )

        # Модель автомобиля
        self.model = Model.objects.create(
            name="Toyota Camry",
            vehicle_type="passenger",
            power_capacity=181,
            fuel_capacity=60,
            seating_capacity=5,
            payload_capacity=400
        )

        # Создаём авто БЕЗ активного водителя (иначе валидация не даст привязать предприятие)
        self.vehicle = Vehicle.objects.create(
            cost=2000000,
            year_of_production=2023,
            mileage=5000,
            color="Black",
            transmission="automatic",
            fuel_type="gasoline",
            model=self.model,
            documentation=self.documentation,
            enterprise=self.enterprise,
            purchase_date=now()
        )

        # Привязка водителя
        VehicleDriver.objects.create(
            vehicle=self.vehicle,
            driver=self.driver
        )

        # Теперь корректно добавляем активного водителя
        self.vehicle.active_driver = self.driver
        self.vehicle.save()

        # Добавляем поездку внутри периода отчёта
        Trip.objects.create(
            vehicle=self.vehicle,
            start_time=now() - timedelta(days=1, hours=2),
            end_time=now() - timedelta(days=1, hours=1)
        )

        # URL
        self.url = reverse("cars:report_api")

    def test_report_api_generates_report(self):
        """
        Полная проверка реального HTTP-вызова report_api.
        """
        # Используем сегодняшнюю дату для тестирования
        today = now().date()
        start_date = today - timedelta(days=1)
        end_date = today + timedelta(days=1)

        # Формируем query string параметры как в примере
        response = self.client.get(
            self.url,
            {
                "report_type": "car_mileage",
                "vehicle_id": self.vehicle.id,
                "period": "day",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )

        
        # Если статус не 200, выводим ошибку для отладки
        if response.status_code != 200:
            print(f"Response content: {response.content}")
            try:
                print(f"JSON response: {response.json()}")
            except:
                pass

        self.assertEqual(response.status_code, 200)

        data = response.json()
        
        # Обновляем проверки под фактическую структуру ответа
        self.assertIn("data", data)
        self.assertIn("unit", data)
        
        # Проверяем, что данные - это список
        rows = data["data"]
        self.assertIsInstance(rows, list)
        
        # Проверяем структуру элементов списка
        if rows:
            self.assertIn("time", rows[0])
            self.assertIn("value", rows[0])
            
        # Проверяем, что unit - это строка
        self.assertIsInstance(data["unit"], str)
