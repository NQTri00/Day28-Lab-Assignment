from fastapi import FastAPI, Request, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ.get("VLLM_URL", os.environ.get("VLLM_NGROK_URL", "http://localhost:8001"))
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()
    if "query" not in body:
        raise HTTPException(status_code=422, detail="Missing query")
    query = body["query"]
    start = time.time()

    # 1. Vector search
    async with httpx.AsyncClient() as client:
        try:
            search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
                "vector": body.get("embedding", [0.0] * 384),
                "limit": 3
            })
            context = search_resp.json().get("result", [])
        except Exception:
            context = []

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
                "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                "messages": [{"role": "user", "content": prompt}]
            }, headers={"ngrok-skip-browser-warning": "true"})
        llm_resp.raise_for_status()
        result = llm_resp.json()
        answer = result["choices"][0]["message"]["content"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {type(e).__name__}: {str(e)[:200]}"
        )

    latency = (time.time() - start) * 1000
    return {
        "answer": answer,
        "latency_ms": round(latency, 2),
        "model": result.get("model", "unknown")
    }

@app.get("/health")
def health():
    return {"status": "ok"}
