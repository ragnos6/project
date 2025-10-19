from locust import HttpUser, task, between

class DjangoReadOnlyUser(HttpUser):
    wait_time = between(0, 0)  # без паузы — чтобы выжать максимум RPS

    def on_start(self):
        self.headers = {"Authorization": f"Token 43f9553733f75df08073d9acad8fdc34b6735497"}

    @task(2)
    def get_drivers(self):
        self.client.get("/api/drivers/", headers=self.headers)

    @task(1)
    def get_trips(self):
        self.client.get(
            "/api/vehicles/761/trips/?start=2024-11-01T00:00:00&end=2025-12-17T23:59:59",
            headers=self.headers
        )

