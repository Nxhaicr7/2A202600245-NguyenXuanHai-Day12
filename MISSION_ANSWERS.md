# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. API key bị hardcode trực tiếp trong code.
2. Không quản lý config bằng biến môi trường (biến cục bộ).
3. Sử dụng `print` thay vì proper structured logging, gây rò rỉ secret key ra log.
4. Không có health check endpoint, khiến platform không thể restart container khi ứng dụng bị crash.
5. Port, host bị fix cứng (`localhost:8000`) và bật chế độ `reload=True` (chỉ dùng cho debug).

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | Hardcoded | Biến môi trường (`.env`) | Dễ dàng quản lý và bảo mật, tuân thủ 12-factor. |
| Logging | `print` | Structured JSON logging | Không rò rỉ secret, dễ dàng tích hợp với các tool như Datadog/Loki. |
| Host | `localhost` | `0.0.0.0` | Có thể nhận request từ bên ngoài container. |
| Lifecycle | Không có | Graceful shutdown & startup | Không bị ngắt kết nối đột ngột của các request đang xử lý. |
| Health Check | Không có | Có endpoints `/health` & `/ready` | Load balancer và orchestrator biết trạng thái thực tế của agent. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: Develop dùng `python:3.11` (full, ~1GB), Production dùng `python:3.11-slim` (nhẹ hơn rất nhiều).
2. Working directory: `/app`

### Exercise 2.3: Image size comparison
- Develop: ~1150 MB
- Production: ~160 MB
- Difference: ~86%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: [Chờ cung cấp - Cần sự hỗ trợ của bạn]
- Screenshot: [Chờ cung cấp - Cần sự hỗ trợ của bạn]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
```bash
# Lệnh kiểm tra xác thực không thành công (thiếu API Key)
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Hello"}'
# Output: {"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}

# Lệnh kiểm tra xác thực thành công (có API Key)
curl -X POST http://localhost:8000/ask -H "X-API-Key: dev-key-change-me-in-production" -H "Content-Type: application/json" -d '{"user_id": "test", "question": "Hỏi về dịch vụ gửi tiết kiệm"}'
# Output: {"question":"Hỏi về dịch vụ gửi tiết kiệm","answer":"...","model":"mock_llm",...}
```

### Exercise 4.4: Cost guard implementation
Sử dụng class `CostGuard` lưu trạng thái trong Redis (stateless). Class này theo dõi lượng token tiêu thụ dựa trên giá của model (vd: GPT-4o-mini). Nếu `total_cost_usd` vượt quá `daily_budget_usd` của user hoặc `global_daily_budget_usd` của hệ thống, agent sẽ chặn request và trả về lỗi `402 Payment Required` hoặc `503 Service Unavailable`.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Health/Readiness probes**: Đã implement `/health` (liveness) và `/ready` (readiness). Endpoint `/health` trả về trạng thái uptime và kết nối Redis.
- **Graceful Shutdown**: Sử dụng `signal.SIGTERM` handler để đảm bảo Agent hoàn thành các request đang xử lý trước khi đóng container.
- **Stateless design**: Toàn bộ session history, rate limit data và cost tracking đều được lưu trữ trong Redis thay vì bộ nhớ cục bộ (RAM).
- **Load balancing**: Cấu hình Docker Compose cho phép scale nhiều instances `agent` và Nginx (hoặc cloud LB) phân phối traffic đều giữa các instance.
