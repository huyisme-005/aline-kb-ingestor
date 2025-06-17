# Aline KB Ingestor

A full‑stack tool to ingest technical content (blogs, guides, PDFs) into a JSON knowledgebase for AI comment generation.

---

## Table of Contents

1. [Prerequisites](#prerequisites)  
2. [Getting Started](#getting-started)  
3. [Environment Variables](#environment-variables)  
4. [Development](#development)  
5. [Testing](#testing)  
6. [Code Style](#code-style)  
7. [Project Structure](#project-structure)  
8. [Extending](#extending)  
9. [Deployment](#deployment)  

---

## Prerequisites

- **Docker & Docker Compose** (v2+)  
- **Node.js** v18+ & **npm**  
- **Python** 3.11+ (if running backend locally)  
- **Redis** (if not using Docker Compose)  

---

## Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-org/aline-kb-ingestor.git
   cd aline-kb-ingestor

2. **Configure environment**
 Copy .env.example → .env (root) and .env.local.example → .env.local (frontend), then edit values.


Launch all services

docker-compose up --build

3.

Backend API → http://localhost:8000


Frontend UI → http://localhost:3000


Redis → redis://localhost:6379


4. **Use the UI**


Enter a Team ID


Provide either a Blog/Guide URL or upload a PDF / paste a Drive link


Click Ingest and monitor the JSON output

Frontend frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000


Development
Backend only
cd backend
pip install -r ../requirements.txt
uvicorn api.main:app --reload --port 8000
celery -A api.tasks worker --loglevel=info


Frontend only


cd frontend
npm install
npm run dev



Testing
Python tests (uses pytest, vcrpy)

pytest --cov=backend


Frontend sanity

cd frontend
npm run lint   # if configured



Code Style
Python: black, isort, flake8


TypeScript/React: follow Next.js defaults; add eslint if desired



Project Structure

aline-kb-ingestor/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md
│
├── backend/
│   ├── models.py
│   ├── base_scraper.py
│   ├── celeryconfig.py
│   ├── utils/
│   ├── importers/
│   ├── scrapers/
│   ├── api/
│   └── tests/
│
└── frontend/
    ├── .env.local.example
    ├── package.json
    ├── tsconfig.json
    ├── next.config.js
    ├── public/
    ├── styles/
    └── src/


Extending
Add a new scraper: subclass backend/base_scraper.py


Wire into API: update backend/api/main.py to detect your new source URL


Test: add VCR‑backed tests under backend/tests/



Deployment
Docker Compose for dev


AWS ECS/Fargate, Heroku, or Render for production


Ensure your REDIS_URL and API_URL are set in your deployment environment


Happy ingesting! 🎉

