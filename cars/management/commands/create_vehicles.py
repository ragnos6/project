import random
from faker import Faker
from django.core.management.base import BaseCommand
from cars.models import Enterprise, Vehicle, Driver, VehicleDriver, Model


fake = Faker('ru-RU')


class Command(BaseCommand):
    help = "Creates vehicles for selected Enterprises"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "-id",
            nargs='+',
            type=int,
            dest="enterprise-id",
            help='ID предприятия/й, для которых генерируем автомобили',
        )
        parser.add_argument(
            '-c',
            type=int,
            dest="count",
            help='Количество автомобилей для каждого предприятия',
        )
    
    def handle(self, *args, **options):
        enterprise_id = options["enterprise-id"]
        vehicle_count = options["count"]
        
        if not enterprise_id:
            self.stderr.write("Необходимо указать ID предприятия enterprise-id")
            return
        
        if vehicle_count < 1:
            self.stderr.write("Количество автомобилей должно быть больше нуля")
            return
                    
        enterprises = Enterprise.objects.filter(id__in=enterprise_id)
        if not enterprises.exists():
            self.stderr.write("Предприятие с указанными ID не найдено")
            return
            
        models = list(Model.objects.all())
        
        for enterprise in enterprises:
            vehicles = []
            drivers = []
            vehicle_driver_entries = []
                        
            for index in range(vehicle_count):
            
                # Создание автомобиля
                vehicle = Vehicle(
                    cost=random.randint(500000, 3000000),
                    year_of_production=random.randint(1990, 2024),
                    mileage=random.randint(0, 200000),
                    color=random.choice([
                        "Белый", 
                        "Чёрный", 
                        "Серебристый", 
                        "Серый", 
                        "Синий", 
                        "Красный", 
                        "Коричневый", 
                        "Бежевый", 
                        "Зелёный", 
                        "Жёлтый", 
                        "Оранжевый", 
                        "Фиолетовый", 
                        "Золотистый", 
                        "Бордовый"
                    ]),
                    transmission=random.choice(['manual', 'automatic']),
                    fuel_type=random.choice(['gasoline', 'diesel', 'electric', 'hybrid']),
                    model=random.choice(models),
                    enterprise=enterprise,
                )
                vehicles.append(vehicle)
                
                # Создание водителя
                driver = Driver(
                    name=fake.name(),
                    age=random.randint(25, 60),
                    salary=random.randint(30000, 80000),
                    enterprise=enterprise,
                )
                drivers.append(driver)

            created_vehicles = Vehicle.objects.bulk_create(vehicles)
            created_drivers = Driver.objects.bulk_create(drivers)
            
            # Привязываем водителей к автомобилям
            for i, vehicle in enumerate(created_vehicles):
                driver = created_drivers[i % len(created_drivers)]  # Назначаем водителей по кругу
                vehicle_driver_entries.append(VehicleDriver(vehicle=vehicle, driver=driver))

                # Каждому 10-му автомобилю назначаем активного водителя
                if i % 10 == 0:
                    vehicle.active_driver = driver
                    vehicle.save()

            # Сохраняем связи VehicleDriver
            VehicleDriver.objects.bulk_create(vehicle_driver_entries)

        self.stdout.write(self.style.SUCCESS("Автомобили и водители успешно созданы"))

