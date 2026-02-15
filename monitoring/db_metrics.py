import time
from django.db import connections
from prometheus_client import Counter, Histogram

DB_QUERY_COUNT = Counter(
    "django_db_queries_total",
    "Total number of DB queries",
    ["alias", "vendor"],
)

DB_QUERY_DURATION = Histogram(
    "django_db_query_duration_seconds",
    "DB query duration in seconds",
    ["alias", "vendor"],
)

def _prometheus_db_wrapper(execute, sql, params, many, context):
    # context содержит connection; это штатно для execute_wrapper
    conn = context["connection"]
    alias = getattr(conn, "alias", "default")
    vendor = getattr(conn, "vendor", "unknown")

    DB_QUERY_COUNT.labels(alias=alias, vendor=vendor).inc()

    start = time.perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        DB_QUERY_DURATION.labels(alias=alias, vendor=vendor).observe(time.perf_counter() - start)

class PrometheusDBExecuteWrapperMiddleware:
    """
    Оборачивает выполнение SQL внутри scope одного HTTP-запроса.
    Работает с любым backend'ом (включая PostGIS), потому что использует
    стандартный механизм Django instrumentation.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        managers = []
        try:
            for conn in connections.all():
                managers.append(conn.execute_wrapper(_prometheus_db_wrapper))
            # Входим во все context manager'ы
            exits = []
            for m in managers:
                exits.append(m.__enter__())
            return self.get_response(request)
        finally:
            # Выходим в обратном порядке
            for m in reversed(managers):
                try:
                    m.__exit__(None, None, None)
                except Exception:
                    # не глушим исключения запроса
                    pass
