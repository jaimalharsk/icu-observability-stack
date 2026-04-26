import time
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("pi.monitor")
counter = meter.create_counter("pi.requests", description="Fake request counter")

print("Sending metrics every 5s. Ctrl+C to stop.")
i = 0
while True:
    counter.add(1, {"env": "pi", "region": "home"})
    print(f"Sent tick {i}")
    i += 1
    time.sleep(5)
