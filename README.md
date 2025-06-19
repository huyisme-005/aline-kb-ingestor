# Aline KB Ingestor

A full-stack application for ingesting content from various sources (blogs, PDFs, Google Drive, Substack) into a knowledge base.

## 🚀 Quick Deploy to AWS (Free Tier)

### Prerequisites
- AWS Account
- AWS CLI configured
- Node.js 18+ and Python 3.9+

### 1. Deploy Backend to AWS Lambda

```bash
# Install Serverless Framework
npm run install:serverless

# Install serverless plugin
npm run install:plugin

# Deploy backend
npm run deploy:backend
```

Note the API Gateway URL from the deployment output.

### 2. Deploy Frontend to AWS Amplify

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click "New app" → "Host web app"
3. Connect your GitHub repository
4. Build settings will auto-detect from `amplify.yml`
5. Add environment variable:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: Your Lambda API Gateway URL (from step 1)
6. Deploy

### 3. Environment Variables

In Amplify Console → App settings → Environment variables:
```
NEXT_PUBLIC_API_URL=https://your-lambda-url.execute-api.us-east-1.amazonaws.com/dev
```

## 🛠️ Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
aline-kb-ingestor/
├── backend/           # FastAPI backend
│   ├── api/          # API endpoints
│   ├── scrapers/     # Web scrapers
│   └── importers/    # File importers
├── frontend/         # Next.js frontend
│   ├── src/
│   └── public/
├── serverless.yml    # AWS Lambda configuration
├── amplify.yml       # AWS Amplify configuration
└── package.json      # Root package.json
```

## 🔧 Supported Content Sources

- **Blogs**: interviewing.io, nilmamano.com
- **PDFs**: Direct file upload
- **Google Drive**: Files and folders
- **Substack**: Any Substack publication
- **Generic**: Any website URL

## 📊 Free Tier Limits

- **AWS Amplify**: 1,000 build minutes/month, 15GB storage
- **AWS Lambda**: 1M requests/month, 400K GB-seconds compute

## 🚀 Deployment Commands

```bash
# Deploy backend only
npm run deploy:backend

# Deploy frontend (via Amplify Console)
npm run deploy:frontend
```

## 📝 License

MIT License - see LICENSE file for details.

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


**Development**

1. Backend only

cd backend
pip install -r ../requirements.txt
uvicorn api.main:app --reload --port 8000
celery -A api.tasks worker --loglevel=info


2. Frontend only

cd frontend
npm install
npm run dev


3. Testing

Python tests (uses pytest, vcrpy)

pytest --cov=backend


4. Frontend sanity

cd frontend
npm run lint   # if configured



5. Code Style
Python: black, isort, flake8


TypeScript/React: follow Next.js defaults; add eslint if desired



6. Project Structure

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


7. Extending
Add a new scraper: subclass backend/base_scraper.py


Wire into API: update backend/api/main.py to detect your new source URL


Test: add VCR‑backed tests under backend/tests/



8. Deployment
Docker Compose for dev


AWS ECS/Fargate, Heroku, or Render for production


Ensure your REDIS_URL and API_URL are set in your deployment environment


Happy ingesting! 🎉

