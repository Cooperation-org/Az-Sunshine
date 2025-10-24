# Arizona Sunshine Transparency Backend

This is the **Django REST Framework (DRF)** backend for the **Arizona Sunshine Transparency Project** — a data transparency and visualization platform built with Django, PostgreSQL (or SQLite), and REST API endpoints.

---

## Features

- Django + Django REST Framework API  
- Endpoints for candidates, contributions, donors, expenditures, races, and committees  
- Easily extendable models and serializers  
- Ready for frontend integration (React / Next.js)

---

## Prerequisites

Before starting, make sure you have the following installed:

- **Python 3.10+**
- **pip**
- **virtualenv** (recommended)
- **Git**
- **PostgreSQL**

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/sunshine-transparency.git
   cd sunshine-transparency/backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run initial migrations:**
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

5. **Create a superuser (optional):**
   ```bash
   python3 manage.py createsuperuser
   ```

---

## Run the Server

```bash
python3 manage.py runserver 127.0.0.1:8000
```

Access the API at:  
    http://127.0.0.1:8000/api/

Admin panel (if enabled):  
    http://127.0.0.1:8000/admin/

---

## Common API Endpoints

| Endpoint | Description |
|-----------|--------------|
| `/api/candidates/` | List all candidates |
| `/api/contributions/` | List contributions |
| `/api/expenditures/` | List expenditures |
| `/api/expenditures/support_oppose_by_candidate/` | Aggregate Support vs Oppose totals by candidate |
| `/api/races/` | List election races |

---

## Useful Management Commands

| Command | Description |
|----------|--------------|
| `python3 manage.py shell` | Open Django shell |
| `python3 manage.py createsuperuser` | Create admin account |
| `python3 manage.py collectstatic` | Collect static files for production |

---

## License

This project is open-source under the [MIT License](LICENSE).


