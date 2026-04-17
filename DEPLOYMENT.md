# Deployment Information

## Public URL
🚀 [Thay_bang_URL_Railway_cua_ban]

## Platform
Railway

## Test Commands

### Health Check
```bash
curl [Thay_bang_URL_Railway_cua_ban]/health
```
**Kết quả thực tế:**
```json
[Dán_kết_quả_vào_đây]
```

### API Test (with authentication)
```bash
curl -X POST [Thay_bang_URL_Railway_cua_ban]/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```
**Kết quả thực tế:**
```json
[Dán_kết_quả_vào_đây]
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
