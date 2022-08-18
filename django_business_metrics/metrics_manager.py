from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable, Callable, Dict

from prometheus_client.registry import Collector
from prometheus_client.metrics_core import GaugeMetricFamily
from django.http import HttpRequest, HttpResponse

import prometheus_client


@dataclass
class _BusinessMetricGauge:
    """Full business metric definition. Meant for internal use."""
    name: str
    documentation: str
    callable: Callable[[], float]


def _get_gauge_metric(metric: _BusinessMetricGauge) -> GaugeMetricFamily:
    return GaugeMetricFamily(
        name=metric.name,
        documentation=metric.documentation,
        value=metric.callable())


class _BusinessMetricsCollector(Collector):
    _metrics: Dict[str, _BusinessMetricGauge]
    thread_pool_size: int

    def __init__(self, max_threads=5):
        self._metrics = {}
        self.thread_pool_size = max_threads

    def add_gauge(self, metric: _BusinessMetricGauge):
        self._metrics[metric.name] = metric

    def collect(self) -> Iterable[GaugeMetricFamily]:
        with ThreadPoolExecutor(max_workers=self.thread_pool_size) as pool:
            return pool.map(_get_gauge_metric, self._metrics.values())


class BusinessMetricsManager:
    _collector: _BusinessMetricsCollector

    def __init__(self):
        self._collector = _BusinessMetricsCollector()

    def add(self, name=None, documentation=""):
        def add_decorator(func: Callable[[], float]):
            metric = _BusinessMetricGauge(
                name=name or func.__name__,
                documentation=documentation,
                callable=func
            )
            self._collector.add_gauge(metric)
            return func
        return add_decorator

    def view(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(
            prometheus_client.generate_latest(self._collector),
            content_type=prometheus_client.CONTENT_TYPE_LATEST
        )


BUSINESS_METRICS_MANAGER = BusinessMetricsManager()

