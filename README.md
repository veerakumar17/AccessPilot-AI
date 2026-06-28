# AccessPilot AI

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)
![React](https://img.shields.io/badge/React-19.2-cyan.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-6.0-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

**AI-Powered Web Accessibility Audit Platform**

AccessPilot AI is a full-stack web application that automates web accessibility auditing using AI and browser automation. It crawls websites, runs WCAG compliance scans, and generates detailed reports with AI-powered explanations and remediation suggestions.

---

## 📋 Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running with Docker](#running-with-docker)
- [Running without Docker](#running-without-docker)
- [API Overview](#api-overview)
- [AI Pipeline](#ai-pipeline)
- [Accessibility Workflow](#accessibility-workflow)
- [PDF Reports](#pdf-reports)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## ✨ Features

### Core Functionality
- **Automated Web Crawling** - BFS crawler that discovers and scans up to 50 pages per audit
- **WCAG 2.1 Compliance Scanning** - axe-core 4.9.1 integration for comprehensive accessibility testing
- **AI-Powered Explanations** - LLM-generated plain English explanations for each violation
- **Smart Fix Generation** - AI-suggested code fixes with implementation steps
- **Disability Simulations** - Simulates how violations affect users with different disabilities
- **PDF Report Export** - Professional, branded PDF reports with executive summaries
- **Multi-Provider AI Support** - OpenAI, Groq, Gemini, or local Ollama

### Technical Features
- **Real-time Updates** - Polling-based status updates during audit execution
- **JWT Authentication** - Secure user registration and login
- **Async Architecture** - Fully async FastAPI backend with SQLAlchemy
- **Background Tasks** - Non-blocking audit pipeline execution
- **Responsive UI** - Modern React frontend with Tailwind CSS
- **Type Safety** - Full TypeScript coverage on frontend

---

## 📸 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/1200x600/0a1628/4fc3f7?text=Dashboard+-+Project+Overview+%26+Stats)

### Projects Management
![Projects](https://via.placeholder.com/1200x600/0a1628/4fc3f7?text=Projects+-+Create+%26+Manage+Websites)

### Audit History
![Audit History](https://via.placeholder.com/1200x600/0a1628/4fc3f7?text=Audit+History+-+Track+All+Scans)

### Audit Details
![Audit Details](https://via.placeholder.com/1200x600/0a1628/4fc3f7?text=Audit+Details+-+Violations+%26+AI+Insights)

### PDF Report
![PDF Report](https://via.placeholder.com/1200x600/0a1628/4fc3f7?text=PDF+Report+-+Professional+Export)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Dashboard│  │ Projects │  │   Audit  │  │  Reports │  │
│  │  Page    │  │  Page    │  │  History │  │   Page   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       ↓              ↓              ↓              ↓        │
│  ┌──────────────────────────────────────────────────────┐  │
││           React Query + Axios + TypeScript            │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/REST API
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ Auth Router  │  │ Project API  │  │   Audit API   │   │
│  └──────────────┘  └──────────────┘  └───────────────┘   │
│       ↓                 ↓                  ↓               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Services Layer                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │   Auth     │  │  Crawler   │  │     AI       │  │  │
│  │  │  Service   │  │  Service   │  │   Engine     │  │  │
│  │  └────────────┘  └────────────┘  └──────────────┘  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │  Scanner   │  │ Reporter   │  │   PDF        │  │  │
│  │  │  Service   │  │  Service   │  │  Service     │  │  │
│  │  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LLM Provider Layer                       │  │
│  │                    ┌──────────┐                       │  │
│  │                    │   Groq   │                       │  │
│  │                    └──────────┘                       │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           PostgreSQL + SQLAlchemy ORM                 │  │
│  │   Users, Projects, Audits, Pages, Violations, Reports │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.111+ (Python 3.12)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose) + bcrypt (passlib)
- **AI/LLM**: Groq (Llama 3.3 70B)
- **Browser Automation**: Playwright + axe-core
- **PDF Generation**: ReportLab
- **Logging**: Structlog (JSON logging)

### Frontend
- **Framework**: React 19.2 + TypeScript 6.0
- **Routing**: React Router 7
- **State Management**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS 4.3 + PostCSS
- **Icons**: Lucide React
- **Build Tool**: Vite 8.0

### DevOps
- **Containerization**: Docker + Docker Compose
- **Process Manager**: Uvicorn (ASGI server)

---

## 📁 Folder Structure

```
AccessPilot-AI/
├── app/                          # Backend application
│   ├── api/v1/                   # API routes
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── projects.py          # Project management
│   │   ├── audits.py            # Audit orchestration
│   │   └── reports.py           # Report generation
│   ├── core/                     # Core utilities
│   │   ├── security.py          # JWT, password hashing
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── logging.py           # Logging configuration
│   ├── db/                       # Database layer
│   │   ├── session.py           # SQLAlchemy engine
│   │   └── base.py              # Declarative base
│   ├── engines/                  # External integrations
│   │   ├── playwright_engine.py # Browser automation
│   │   ├── axe_engine.py        # Accessibility scanner
│   │   └── llm/                 # LLM providers
│   │       ├── base.py          # Abstract LLM client
│   │       ├── factory.py       # Provider factory
│   │       ├── models.py        # Response dataclasses
│   │       └── groq_provider.py
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── audit.py
│   │   ├── page.py
│   │   ├── violation.py
│   │   └── report.py
│   ├── repositories/             # Data access layer
│   │   ├── user_repo.py
│   │   ├── project_repo.py
│   │   ├── audit_repo.py
│   │   ├── page_repo.py
│   │   └── report_repo.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── auth.py
│   │   ├── project.py
│   │   ├── audit.py
│   │   └── report.py
│   ├── services/                 # Business logic
│   │   ├── auth_service.py
│   │   ├── project_service.py
│   │   ├── audit_service.py
│   │   ├── audit_pipeline.py    # 8-step pipeline
│   │   ├── crawler_service.py
│   │   ├── scanner_service.py
│   │   ├── scan_persistence_service.py
│   │   ├── ai_engine_service.py
│   │   ├── ai_explanation_service.py
│   │   ├── fix_generator_service.py
│   │   ├── simulator_service.py
│   │   ├── reporter_service.py
│   │   └── pdf_service.py
│   ├── config.py                 # Settings management
│   ├── dependencies.py           # FastAPI dependencies
│   └── main.py                   # FastAPI app factory
├── frontend/                     # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/           # Navbar, Sidebar, AppLayout
│   │   │   └── ui/               # Reusable UI components
│   │   ├── pages/                # Route pages
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ProjectsPage.tsx
│   │   │   ├── AuditHistoryPage.tsx
│   │   │   ├── AuditDetailsPage.tsx
│   │   │   └── ReportsPage.tsx
│   │   ├── services/             # API clients
│   │   ├── hooks/                # Custom React Query hooks
│   │   ├── context/              # React contexts
│   │   ├── types/                # TypeScript interfaces
│   │   └── data/                 # Mock data
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
├── alembic/                      # Database migrations
│   └── versions/
├── scripts/                      # Utility scripts
│   ├── validate_backend.py
│   └── check_axe_rules.py
├── tests/                        # Test suite
│   ├── unit/
│   └── integration/
├── .env.example                  # Environment template
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL 16** (or use Docker)
- **Git**

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/veerakumar17/AccessPilot-AI.git
   cd AccessPilot-AI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/api/docs`
   - Health check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

### Application
```env
APP_NAME=AccessPilot AI
APP_ENV=development
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-secret-key-here
```

### Database
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/accesspilot
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### JWT
```env
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### LLM Provider: Groq
```env
# AccessPilot AI uses Groq for AI-powered accessibility analysis
# Get your free API key at: https://console.groq.com/keys
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
```

### Crawler
```env
CRAWLER_MAX_PAGES=20
CRAWLER_TIMEOUT_SECONDS=30
CRAWLER_HEADLESS=true
```

### CORS
```env
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Frontend (create `frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🐳 Running with Docker

### Quick Start

1. **Clone and navigate**
   ```bash
   git clone https://github.com/veerakumar17/AccessPilot-AI.git
   cd AccessPilot-AI
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/api/docs`
   - PostgreSQL: `localhost:5432`

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Run database migrations
docker-compose exec api alembic upgrade head
```

---

## 💻 Running without Docker

### Backend Only

```bash
# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (PostgreSQL must be running)
createdb accesspilot

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Overview

### Authentication Endpoints
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `GET /api/v1/auth/me` - Get current user info

### Project Endpoints
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects` - List all projects
- `GET /api/v1/projects/{id}` - Get project details
- `DELETE /api/v1/projects/{id}` - Delete project

### Audit Endpoints
- `POST /api/v1/audits` - Start new audit (returns 202 Accepted)
- `GET /api/v1/audits` - List all audits
- `GET /api/v1/audits/{id}` - Get audit status
- `GET /api/v1/audits/{id}/summary` - Get audit summary with report
- `GET /api/v1/audits/{id}/pages` - Get crawled pages
- `GET /api/v1/audits/{id}/violations` - Get accessibility violations

### Report Endpoints
- `GET /api/v1/reports/{audit_id}` - Get generated report
- `GET /api/v1/reports/{audit_id}/pdf` - Download PDF report

### Health Check
- `GET /health` - API health status

---

## 🔄 AI Pipeline

The audit pipeline consists of **8 sequential steps**:

```
Step 1: Mark Audit as RUNNING
    ↓
Step 2: Crawl Website (BFS crawler, max 50 pages)
    ↓
Step 3: Save Pages to Database
    ↓
Step 4: Run axe-core Accessibility Scan
    ↓
Step 5: Save Violations to Database
    ↓
Step 6: AI Enrichment (3 sub-steps)
    ├─ 6a: Generate AI Explanations (one per unique rule_id)
    ├─ 6b: Generate AI Fixes (code examples + steps)
    └─ 6c: Generate Disability Simulations
    ↓
Step 7: Build Report (calculate score, generate summary)
    ↓
Step 8: Mark Audit as COMPLETED
```

### AI Enrichment Details

**Optimization**: Instead of generating AI content for every violation, the system:
1. Groups violations by `rule_id` (e.g., all "image-alt" violations)
2. Generates ONE explanation/fix/simulation per unique rule
3. Batch-updates all violations in that group

**Result**: 66 violations → ~10-15 LLM calls (90% reduction)

### AI Provider: Groq

AccessPilot AI uses **Groq** as its AI provider for generating accessibility explanations, fix suggestions, and disability simulations.

**Why Groq?**
- **Free tier available** - No credit card required
- **Very fast inference** - Optimized for low latency
- **High quality** - Powered by Llama 3.3 70B model
- **Easy setup** - Get API key in minutes at https://console.groq.com/keys

**Model:** `llama-3.3-70b-versatile`

---

## ♿ Accessibility Workflow

### 1. Create Project
- Enter website URL and project details
- Project serves as the base for audits

### 2. Start Audit
- Select project and optionally override target URL
- Audit runs in background (non-blocking)
- Poll for status updates every 5 seconds

### 3. Review Results
- **Accessibility Score**: 0-100% (A-F grade)
- **Severity Breakdown**: Critical, Serious, Moderate, Minor
- **Pages Scanned**: Total pages crawled
- **Violations List**: Detailed list with:
  - WCAG criterion
  - HTML snippet
  - CSS selector
  - AI explanation (plain English)
  - AI-suggested fix (code + steps)
  - Disability impact simulation

### 4. Export Report
- Download professional PDF report
- Includes executive summary, stats, and all violations
- Branded with AccessPilot AI styling

---

## 📄 PDF Reports

The PDF report includes:

- **Cover Page**: Project name, target URL, audit date, status
- **Executive Summary**: 
  - Accessibility score (0-100%)
  - Grade (A-F)
  - Stats grid (pages, violations, severity counts)
  - AI-generated summary text
- **Violations Section**:
  - Each violation with rule ID, severity badge, WCAG criterion
  - HTML snippet with syntax highlighting
  - AI Explanation (plain English, business impact, recommendation)
  - AI Fix (problem, recommended fix, code example, implementation steps)
  - General User Impact
  - Accessibility Impact by User Group (blind, low vision, motor, cognitive)

---

## 🚀 Future Improvements

### Planned Features
- [ ] **Multi-language Support** - i18n for global accessibility
- [ ] **Historical Trends** - Track accessibility improvements over time
- [ ] **Team Collaboration** - Share audits and reports with team members
- [ ] **Scheduled Audits** - Automated recurring scans (daily/weekly/monthly)
- [ ] **Custom Rules** - Define organization-specific accessibility rules
- [ ] **CI/CD Integration** - GitHub Actions, GitLab CI plugins
- [ ] **Browser Extension** - One-click audits from any webpage
- [ ] **Mobile App** - React Native app for on-the-go audits
- [ ] **Advanced Analytics** - Heatmaps, violation clustering, trend analysis
- [ ] **Accessibility Score API** - Public API for third-party integrations
- [ ] **WAVE Integration** - Combine multiple scanning engines
- [ ] **User Testing** - Integrate with assistive technology testing platforms

### Technical Improvements
- [ ] **WebSocket Support** - Real-time audit progress updates
- [ ] **Redis Caching** - Cache LLM responses and scan results
- [ ] **Celery/ARQ** - Replace BackgroundTasks with robust task queue
- [ ] **Kubernetes Deployment** - Helm charts for production
- [ ] **Observability** - OpenTelemetry, Prometheus metrics, Grafana dashboards
- [ ] **Load Testing** - Locust/JMeter tests for scalability validation

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript strict mode
- Write tests for new features
- Update documentation for API changes
- Ensure all checks pass before submitting PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Veera Kumar**
- GitHub: [@veerakumar17](https://github.com/veerakumar17)
- LinkedIn: [Veera Kumar](https://linkedin.com/in/veerakumar17)

---

## 🙏 Acknowledgments

- [axe-core](https://github.com/dequelabs/axe-core) - Accessibility testing engine
- [Playwright](https://playwright.dev/) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- Groq - AI provider for accessibility analysis

---

## 📞 Support

For support, email veerakumar17@example.com or open an issue on GitHub.

---

## 🎯 Use Cases

- **Enterprise**: Audit internal web applications for WCAG compliance
- **Agencies**: Generate accessibility reports for clients
- **Developers**: Test websites during development
- **Hackathons**: Rapid accessibility auditing prototype
- **Education**: Learn about web accessibility and AI

---

## 🌟 Star History

If you find this project useful, please consider giving it a star!

---

**Built with ❤️ for a more accessible web**