from celery import shared_task
import time

@shared_task
def test_redis_connection(): 
    
    return "success"