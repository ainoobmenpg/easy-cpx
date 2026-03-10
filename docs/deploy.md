# Deployment & Security Guide

> This guide covers production deployment best practices for Operational CPX.

---

## Environment Configuration

### Required Environment Variables

#### Backend

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/cpx` |
| `MINIMAX_API_KEY` | MiniMax API key for AI | `your-api-key` |
| `MINIMAX_BASE_URL` | AI API endpoint | `https://api.minimax.chat/v1` |
| `ENABLE_INTERNAL_ENDPOINTS` | Enable internal APIs | `false` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `https://your-domain.com` |

#### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.your-domain.com` |

### Security-Critical Settings

```bash
# .env.production (Backend)
DATABASE_URL=postgresql://user:secure-password@host:5432/cpx
MINIMAX_API_KEY=your-secure-api-key
MINIMAX_BASE_URL=https://api.minimax.chat/v1
ENABLE_INTERNAL_ENDPOINTS=false
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# .env.production (Frontend)
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

> **Warning**: Never commit `.env` files to version control. Use `.env.example` for templates.

---

## CORS Configuration

### Production CORS

The backend uses FastAPI's CORS middleware. Configure `CORS_ORIGINS` appropriately:

```python
# backend/main.py
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

#### Recommended Production Settings

```bash
# Allow only your production domains
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

#### Development Settings

```bash
# Allow local development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## Internal API Protection

### What are Internal Endpoints?

Internal endpoints expose sensitive data **without Fog of War**:
- `/api/internal/games/{game_id}/true-state`
- `/api/internal/games/{game_id}/units`

These endpoints reveal enemy positions and other classified information.

### Protection Strategy

1. **Always disable in production**:
   ```bash
   ENABLE_INTERNAL_ENDPOINTS=false
   ```

2. **Network isolation**: If internal access is needed, restrict via firewall/VPC:
   - Only allow admin machine IPs
   - Use VPN or bastion host
   - Never expose to public internet

3. **Alternative**: Use a separate internal API with authentication

---

## Authentication & RBAC

### Current Status

Authentication is planned but not yet implemented. See [CPX-AUTH](./issues/cpx-auth-jwt.md).

### Planned Implementation

```bash
# Future JWT settings
JWT_SECRET=your-secret-key
JWT_EXP_MIN=15
JWT_REFRESH_EXP_MIN=10080  # 7 days
```

### RBAC Roles

| Role | Access Level |
|------|--------------|
| `admin` | Full system access |
| `white` | Full game visibility (referee) |
| `blue` | Player side only |
| `red` | Enemy side (AI) |
| `observer` | Read-only spectator |

---

## Rate Limiting

### Recommended Configuration

For production, implement rate limiting at the application level or proxy:

#### Nginx Example

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
        }

        location /api/auth/login {
            limit_req zone=auth burst=5 nodelay;
        }
    }
}
```

#### Recommended Limits

| Endpoint Type | Rate |
|--------------|------|
| General API | 10 requests/second |
| Auth endpoints | 5 requests/minute |
| Turn commit | 1 request/second |

---

## Database Security

### PostgreSQL Configuration

1. **Use strong passwords**:
   ```sql
   ALTER USER cpx WITH PASSWORD 'secure-random-password';
   ```

2. **Restrict access**:
   ```sql
   REVOKE CONNECT ON DATABASE cpx FROM PUBLIC;
   GRANT CONNECT ON DATABASE cpx TO cpx_user;
   ```

3. **SSL/TLS**:
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/cpx?sslmode=require
   ```

### Backup Strategy

```bash
# Daily backup script
pg_dump -h localhost -U cpx_user cpx > backup_$(date +%Y%m%d).sql
```

---

## Logging & Monitoring

### Structured Logging

The system uses structured logging for audit trails:

```python
# Example log output
{
  "timestamp": "2026-03-10T12:00:00Z",
  "level": "INFO",
  "event": "turn_commit",
  "game_id": 1,
  "user": "player1",
  "action": "commit"
}
```

### Recommended Log Retention

| Log Type | Retention |
|----------|-----------|
| Access logs | 90 days |
| Application logs | 30 days |
| Audit logs | 1 year |
| Error logs | 90 days |

---

## Proxy Configuration

### Nginx Production Config

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Security Checklist

Before production deployment, verify:

- [ ] `ENABLE_INTERNAL_ENDPOINTS=false`
- [ ] `CORS_ORIGINS` restricted to production domains
- [ ] Strong database password
- [ ] SSL/TLS configured
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Logging configured
- [ ] Backup strategy in place
- [ ] No `.env` files in version control

---

## Docker Deployment

```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

---

## Troubleshooting

### Common Issues

1. **CORS errors**: Check `CORS_ORIGINS` includes your frontend domain
2. **Internal endpoint 401**: Ensure `ENABLE_INTERNAL_ENDPOINTS=false` in production
3. **Database connection**: Verify `DATABASE_URL` format and credentials
4. **API 500 errors**: Check logs for detailed error messages

### Health Check

```bash
# Backend health
curl https://api.your-domain.com/api/games/

# Frontend health
curl https://your-domain.com
```
