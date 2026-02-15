from locust import HttpUser, task, between
import random

class DjangoAsyncWriter(HttpUser):
    wait_time = between(0, 0)

    @task
    def post_fake_data(self):
        data = {"value": random.randint(0, 1000)}
        self.client.post("/cars/test_async/", json=data)
