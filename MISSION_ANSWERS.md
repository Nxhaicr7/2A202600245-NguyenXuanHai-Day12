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
# Lệnh kiểm tra xác thực không thành công
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "Hello"}'
# Output mong muốn: 403 Forbidden hoặc 401 Unauthorized do thiếu API Key

# Lệnh kiểm tra xác thực thành công
curl -X POST http://localhost:8000/ask -H "X-API-Key: my-secret-key" -H "Content-Type: application/json" -d '{"question": "Hello"}'
# Output mong muốn: 200 OK
```

### Exercise 4.4: Cost guard implementation
Sử dụng class `CostGuard` lưu trạng thái (in-memory hoặc Redis trong production) với các cấu hình `daily_budget_usd`, `global_daily_budget_usd`. Guardrail này theo dõi lượng token in/out sau mỗi request. Nếu chi phí vượt mức ngân sách (global hoặc per-user), raise lỗi `HTTPException 503` hoặc `402`. Thêm logic cảnh báo (warning logging) khi chi phí đạt mức threshold như 80%.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Health/Readiness probes**: Thiết lập các endpoint `/health` (liveness) và `/ready` (kiểm tra các dependent service như Redis).
- **Graceful Shutdown**: Handle `SIGTERM` signal để đợi các requests hiện tại xử lý xong.
- **Stateless design**: Sử dụng Redis để quản lý session và lịch sử hội thoại thay vì in-memory.
- **Load balancing**: Các requests có thể được phục vụ bởi bất kỳ instance nào (vì stateful data đã được outsource sang Redis).
