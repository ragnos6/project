from locust import HttpUser, task, between

class DjangoReadOnlyUser(HttpUser):
    wait_time = between(0, 0)  # без паузы — чтобы выжать максимум RPS

    def on_start(self):
        self.headers = {"Authorization": f"Token 43f9553733f75df08073d9acad8fdc34b6735497"}

    @task(1)
    def get_drivers(self):
        self.client.get("/cars/drivers/", headers=self.headers)


