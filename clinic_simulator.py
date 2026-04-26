import time
import argparse
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import grpc

def make_provider():
    try:
        exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=2000)
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        print("[OK] Connected to OTel Collector at localhost:4317")
        return metrics.get_meter("clinic.floor1")
    except Exception as e:
        print(f"[ERROR] Failed to connect to OTel Collector: {e}")
        exit(1)

def push(gauge, value, labels):
    try:
        gauge.set(value, labels)
        print(f"  [SENT] {labels} -> {value}")
    except Exception as e:
        print(f"  [ERROR] Failed to send metric: {e}")

meter = make_provider()

oxygen_psi     = meter.create_gauge("clinic_oxygen_psi")
life_support_w = meter.create_gauge("clinic_life_support_watts")
battery_pct    = meter.create_gauge("clinic_battery_pct")
heartbeat      = meter.create_gauge("clinic_device_heartbeat")

BEDS = [f"bed_{i}" for i in range(1, 6)]

def normal():
    print("[SCENARIO] Normal state — all beds nominal")
    while True:
        for bed in BEDS:
            labels = {"bed": bed, "floor": "1"}
            push(oxygen_psi,     55,  labels)
            push(life_support_w, 210, labels)
            push(battery_pct,    95,  labels)
            push(heartbeat,      1,   labels)
        print("  [TICK] All beds OK\n")
        time.sleep(2)

def oxygen_leak(bed="bed_1"):
    print(f"[SCENARIO] Oxygen leak on {bed}")
    psi = 55
    while psi > 5:
        push(oxygen_psi, psi, {"bed": bed, "floor": "1"})
        if psi < 30:
            print(f"  [ALERT] Oxygen PSI critical: {psi}")
        psi -= 3
        time.sleep(2)
    print(f"[CRITICAL] {bed} oxygen depleted!")

def power_failure(bed="bed_2"):
    print(f"[SCENARIO] Power failure on {bed}")
    watts = 210
    batt = 95
    while watts > 0 or batt > 0:
        push(life_support_w, max(watts, 0), {"bed": bed, "floor": "1"})
        push(battery_pct,    max(batt, 0),  {"bed": bed, "floor": "1"})
        if watts <= 0:
            print(f"  [ALERT] Mains power lost — running on battery: {max(batt,0)}%")
        if batt < 20:
            print(f"  [CRITICAL] Battery low: {max(batt,0)}%")
        watts -= 30
        batt -= 8
        time.sleep(2)
    print(f"[CRITICAL] {bed} total power loss!")

def device_offline(bed="bed_3"):
    print(f"[SCENARIO] Device offline on {bed}")
    push(heartbeat, 0, {"bed": bed, "floor": "1"})
    print(f"  [CRITICAL] {bed} heartbeat lost — device unresponsive")
    time.sleep(30)

parser = argparse.ArgumentParser()
parser.add_argument("scenario", choices=["normal", "oxygen_leak", "power_failure", "device_offline"])
parser.add_argument("--bed", default=None)
args = parser.parse_args()

if args.scenario == "normal":
    normal()
elif args.scenario == "oxygen_leak":
    oxygen_leak(args.bed or "bed_1")
elif args.scenario == "power_failure":
    power_failure(args.bed or "bed_2")
elif args.scenario == "device_offline":
    device_offline(args.bed or "bed_3")
