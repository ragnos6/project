from django.utils import timezone
import zoneinfo
import time
import json
from datetime import datetime
import logging
from threading import local
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.session.get("django_timezone")
        if tzname:
            timezone.activate(zoneinfo.ZoneInfo(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
        

logger = logging.getLogger('requests')
_thread_locals = local()

class ApiLoggingMiddleware(MiddlewareMixin):
    def __call__(self, request):
        start_time = time.time()
        
        try:
            body = request.body.decode('utf-8')
        except Exception:
            body = '<unreadable>'
        
        params = dict(request.GET) if request.method == 'GET' else body
        
        response = self.get_response(request)
        
        total_time = time.time() - start_time
        sql_count = len(connection.queries)
        sql_time = sum(float(q.get('time', 0)) for q in connection.queries)
        
        timestamp = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        log_line = (
            f'{timestamp} {request.META.get("REMOTE_ADDR", "?")} '
            f'"{request.method} {request.path} HTTP/1.1" {response.status_code} '
            f'{total_time:.3f} {sql_count} {sql_time:.3f} '
            f'"{json.dumps(params)}"'
        )
        

        with open('/home/parallels/project/logs/requests.log', 'a') as f:
            f.write(log_line + '\n')
            
        return response
