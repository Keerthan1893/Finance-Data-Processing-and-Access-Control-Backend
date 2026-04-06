# 📊 Finance Dashboard Backend

A secure, high-performance REST API for a role-based finance dashboard. Built with **Django REST Framework**, **SQLite**, **Redis**, and **Celery**.

---

## 🚀 Fast Track Setup (SQLite Only)

Get up and running in less than 2 minutes.

1.  **Clone & Environment**:
    ```bash
    git clone https://github.com/Keerthan1893/Finance-Data-Processing-and-Access-Control-Backend && cd finance_backend
    python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
2.  **Dependencies & Config**:
    ```bash
    pip install -r requirements.txt
    cp .env.example .env  # Add your SECRET_KEY and REDIS_URL here
    ```
3.  **Database & Admin**:
    ```bash
    python manage.py migrate
    python manage.py createsuperuser  # Create your initial Admin account
    ```
4.  **Run**:
    ```bash
    python manage.py runserver
    ```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | Django 4.2 + Django REST Framework (DRF) |
| **Database** | SQLite (Production-ready abstraction via Django ORM) |
| **Cache/Tasks** | Redis 7+ & Celery 5+ |
| **Auth** | JWT (SimpleJWT) with Token Rotation & Blacklisting |
| **Docs** | OpenAPI 3.0 via drf-spectacular (Swagger / Redoc) |

---

## 🔐 Role-Based Access Control (RBAC)

The system enforces strict data isolation based on three user roles:

| Feature / Action | 🔴 Admin | 🟡 Analyst | 🟢 Viewer |
|:--- |:---:|:---:|:---:|
| **Dashboard Highlights** | ✅ | ✅ | ✅ |
| **View/Search Records** | ✅ | ✅ | ❌ |
| **Create/Edit Records** | ✅ | ❌ | ❌ |
| **User Management** | ✅ | ❌ | ❌ |

> [!NOTE]
> **Viewer** is designed as an executive-level role for viewing high-level trends without seeing raw transaction details.

---

## 📂 Project Architecture

```
Client ──► REST API ── (JWT) ──► Redis (Cache / Blacklist)
             │
             ├── apps/users      → Auth, Roles & Profile
             ├── apps/records    → Financial Data & Soft-Delete logic
             └── apps/dashboard  → Analytics (Aggregated & Cached)
                           │
                      Celery Worker
                 (Pre-warms cache every 5min)
```

### 🧠 Core Design Decisions
- **Soft Deletion**: Records are never lost; the `DELETE` action marks them `is_deleted=True` for auditing.
- **Aggregated Analytics**: Dashboard summaries are computationally expensive and are cached in Redis (5-min TTL) to ensure sub-millisecond response times.
- **Strict Validation**: All financial inputs (amounts, dates, types) are validated via Serializers before persistence.

---

## 📖 API Documentation

Once running, access the full documentation here:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **Redoc**: `http://localhost:8000/api/redoc/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## 🧪 Testing

The codebase includes comprehensive integration tests for both Auth and Record CRUD.
```bash
python manage.py test
```
