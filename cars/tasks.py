from celery import shared_task

@shared_task
def save_driver_data(data):
    print(f"Saving driver data: {data}")
    return True
