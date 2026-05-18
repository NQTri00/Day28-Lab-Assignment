import requests
import os

def check_prometheus():
    try:
        resp = requests.get("http://localhost:9090/api/v1/query",
                            params={"query": 'http_requests_total{job="api-gateway"}'})
        data = resp.json()
        assert data["status"] == "success"
        print("Integration 9 OK: Prometheus metrics flowing")
    except Exception as e:
        print(f"Failed to check Prometheus: {e}")

def check_langsmith():
    try:
        from langsmith import Client
        api_key = os.environ.get("LANGCHAIN_API_KEY")
        if not api_key or api_key == "your_langsmith_key":
            print("Skipping LangSmith check (LANGCHAIN_API_KEY not set)")
            return
        client = Client(api_key=api_key)
        runs = list(client.list_runs(project_name="lab28-platform", limit=1))
        if len(runs) > 0:
            print("Integration 10 OK: LangSmith traces visible")
        else:
            print("No traces found in LangSmith yet")
    except Exception as e:
        print(f"Failed to check Langsmith: {e}")

if __name__ == "__main__":
    check_prometheus()
    check_langsmith()
