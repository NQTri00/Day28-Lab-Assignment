# Hướng Dẫn Nộp Bài - Lab #28: Full Platform Integration Sprint

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

   **Trả lời:** Kiến trúc được thiết kế theo nguyên tắc "async-first và decouple mọi thứ". Trade-off chính là giữa **latency và reliability**: thay vì gọi trực tiếp từ API Gateway đến vLLM (thấp latency nhưng tightly-coupled), chúng tôi dùng Kafka làm message broker để buffer các request, chấp nhận latency cao hơn đổi lại độ bền dữ liệu cao hơn (messages không bị mất nếu vLLM tạm thời sập). Về maintainability, mỗi service chạy trong container riêng với cấu hình độc lập trong `docker-compose.yml`, giúp dễ dàng update từng component mà không ảnh hưởng toàn hệ thống. Performance được đảm bảo qua vector search với Qdrant (giảm context đưa vào LLM), và monitoring real-time với Prometheus + Grafana để phát hiện bottleneck ngay.

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

   **Trả lời:** Kết nối giữa local và Kaggle được thực hiện qua ngrok tunnel với URL được lưu trong file `.env`. Khi Kaggle ngắt kết nối hoặc URL thay đổi, API Gateway sẽ bắt `httpx.ConnectError` hoặc `httpx.HTTPStatusError` và trả về HTTP 503 với message rõ ràng thay vì crash với 500. Cơ chế fallback được implement trong `api-gateway/main.py`: toàn bộ LLM call được bọc trong `try/except`, đảm bảo hệ thống vẫn phục vụ các endpoint khác (health check, metrics, Qdrant search) khi vLLM offline. Khi cần restore, chỉ cần cập nhật URL mới trong `.env` và chạy `docker compose restart api-gateway` — không cần restart toàn bộ stack.

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

   **Trả lời:** Kafka đóng vai trò "backbone" của toàn bộ data flow. Thay vì `script_01` → `script_03` → `script_05` gọi nhau trực tiếp (tightly coupled), mỗi script chỉ biết về Kafka topic `data.raw`. **Producer** (`01_ingest_to_kafka.py`) chỉ cần publish message và không quan tâm ai consume. **Prefect flow** consume độc lập, transform sang Delta Lake, và bản thân Prefect có scheduler riêng nên không bị block bởi producer. **Embedding service** (`05_embed_to_qdrant.py`) cũng đọc từ Delta Lake độc lập. Lợi ích thực tế: khi Kaggle vLLM bị restart, toàn bộ data đã được lưu an toàn trong Kafka (replay được), Delta Lake, và Qdrant — không mất một record nào.

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

   **Trả lời:** Observability được implement theo 3 tầng. **Metrics**: API Gateway expose `/metrics` endpoint qua `prometheus-fastapi-instrumentator`, tự động track HTTP request count, latency histogram (P50/P95/P99), và error rate. Prometheus scrape endpoint này mỗi 15 giây (cấu hình trong `monitoring/prometheus.yml`). Grafana kết nối Prometheus để visualize dashboard. **Logs**: Mỗi service trong Docker đều stream logs ra stdout, có thể xem real-time bằng `docker compose logs -f`. Các script Python dùng `print()` với prefix rõ ràng (e.g., "Integration 1 OK", "Saved N records"). **Traces**: LangSmith được tích hợp qua `LANGCHAIN_API_KEY` để trace các LLM call, track input/output tokens, latency, và lỗi. Production readiness check script (`production_readiness_check.py`) kiểm tra tự động toàn bộ stack và cho ra score 10/10.

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

   **Trả lời:** Có graceful degradation ở nhiều tầng. **Nếu Qdrant crash**: API Gateway bắt exception trong vector search block và set `context = []`, sau đó vẫn tiếp tục gọi LLM với empty context — user nhận được answer tuy nhiên không có retrieval augmentation. **Nếu Kafka crash**: `01_ingest_to_kafka.py` sẽ throw lỗi rõ ràng, nhưng các service đã chạy (Qdrant, Redis, API Gateway) vẫn hoạt động bình thường phục vụ query từ data đã index. **Nếu Redis crash**: Feature store sẽ unavailable nhưng vector search và LLM inference vẫn hoạt động. **Nếu vLLM/Kaggle crash**: API Gateway trả về 503 thay vì 500, health endpoint vẫn trả về 200 OK, và toàn bộ observability stack (Prometheus, Grafana) vẫn chạy. Cơ chế rollback: `docker compose restart <service>` để khởi động lại service bị lỗi mà không ảnh hưởng service khác.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
