import requests, redis, subprocess

results = {}

def check(name, fn):
    try:
        fn()
        results[name] = "PASS"
        print(f"  [PASS] {name}")
    except Exception as e:
        results[name] = f"FAIL: {e}"
        print(f"  [FAIL] {name}: {e}")

print("\n=== RELIABILITY ===")
check("Health check endpoint", lambda:
    requests.get("http://localhost:8000/health").raise_for_status())
check("API Gateway responds", lambda:
    requests.get("http://localhost:8000/docs").raise_for_status())

print("\n=== OBSERVABILITY ===")
check("Prometheus up", lambda:
    requests.get("http://localhost:9090/-/healthy").raise_for_status())
check("Grafana up", lambda:
    requests.get("http://localhost:3000/api/health").raise_for_status())
check("Metrics endpoint exposed", lambda:
    requests.get("http://localhost:8000/metrics").raise_for_status())

print("\n=== SECURITY ===")
def assert_status(code, allowed):
    if code not in allowed:
        raise Exception(f"Status {code} not in {allowed}")

check("Unauthorized request rejected", lambda: (
    r := requests.get("http://localhost:8000/admin"),
    assert_status(r.status_code, [401, 403, 404])
))

print("\n=== VECTOR STORE ===")
check("Qdrant healthy", lambda:
    requests.get("http://localhost:6333/healthz").raise_for_status())
check("Collection exists", lambda: (
    r := requests.get("http://localhost:6333/collections/documents"),
    r.raise_for_status()
))

print("\n=== FEATURE STORE ===")
check("Redis reachable", lambda:
    redis.Redis(host="localhost", port=6379).ping())

print("\n=== KAFKA ===")
def check_kafka():
    result = subprocess.run(
        ["docker", "exec", "day28-lab-assignment-kafka-1", "kafka-topics", "--list",
         "--bootstrap-server", "localhost:9092"],
        capture_output=True, text=True
    )
    if "data.raw" not in result.stdout:
        raise Exception("data.raw topic not found")
check("Kafka topics exist", check_kafka)

# Tổng kết
passed = sum(1 for v in results.values() if v == "PASS")
total = len(results)
score = (passed / total) * 100
print(f"\n{'='*40}")
print(f"Production Readiness Score: {passed}/{total} = {score:.0f}%")
print(f"Target: >80% — Status: {'READY' if score >= 80 else 'NOT READY'}")
