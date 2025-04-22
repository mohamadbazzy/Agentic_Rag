<div align="center">
  <h1>🎓 Academic Advisor</h1>
  <p>An intelligent agent-based system to assist students with academic planning and course selection at AUB's MSFEA</p>
  
  [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](docker-compose.yml)
  [![Python](https://img.shields.io/badge/Python-3.8+-yellow?logo=python)](requirements.txt)
</div>

---

## 📑 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Services](#services)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## 🔍 Overview

Academic Advisor is a comprehensive platform designed to streamline the academic planning process for students at the Maroun Semaan Faculty of Engineering and Architecture (MSFEA) at the American University of Beirut (AUB). Using a multi-agent architecture, the system helps students navigate course selection, degree requirements, and academic regulations while providing personalized guidance tailored to each student's academic journey.

The system integrates with university data sources to provide up-to-date information on course offerings, prerequisites, and scheduling, enabling students to make informed decisions about their academic path.

## ✨ Key Features

- **Department-Specific Advising** - Specialized guidance for different MSFEA departments (ECE, MECH, CEE, etc.)
- **Schedule Helper** - Assistance with class schedules and course timetables
- **WhatsApp Integration** - Access advising services through WhatsApp
- **Central Supervisor** - Intelligent routing to appropriate department agents
- **Context-Aware Responses** - Leveraging vector search to provide accurate information
- **Persistent Conversation** - Session-based memory for continuing discussions

## 🏗️ System Architecture

Academic Advisor uses a microservices architecture with multiple specialized agents communicating through a central backend:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │◄───►│   Backend   │◄───►│ Vector DB   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
┌──────▼─────┐    ┌───────▼──────┐    ┌──────▼─────┐
│ Supervisor │    │  Department  │    │   Scraper  │
│   Agent    │    │    Agents    │    │   Service  │
└──────┬─────┘    └───────┬──────┘    └──────┬─────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                    ┌─────▼─────┐
                    │  WhatsApp │
                    │  Service  │
                    └───────────┘
```

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- OpenAI API key

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/academic-advisor.git
   cd academic-advisor
   ```

2. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configuration
   ```

3. Build and start all services
   ```bash
   docker-compose up -d
   ```

4. Access the application
   ```
   Frontend: http://localhost:80
   Backend API: http://localhost:8000
   WhatsApp Service: http://localhost:8001
   ```

## 🚀 Usage

### For Students
1. **Department Advising**: Get guidance specific to your engineering department
   ```
   "What are the core courses for ECE?"
   "How can I apply for a MECH internship?"
   ```

2. **Schedule Assistance**: Get help with course scheduling
   ```
   "When is ECE 350 offered this semester?"
   "Are there any conflicts between MECH 310 and FEAA 200?"
   ```

3. **General MSFEA Information**: Access faculty-wide information
   ```
   "What's the deadline for adding courses this semester?"
   "How do I contact the Dean's office?"
   ```

### Via WhatsApp
Send messages to the configured WhatsApp number to interact with the advisor on-the-go.

## 🧩 Services

The system comprises several interconnected services:

| Service | Description |
|---------|-------------|
| **Frontend** | Simple HTML/CSS/JS web interface for student interaction |
| **Backend** | FastAPI service handling core logic and routing |
| **Supervisor** | Orchestration agent that validates queries and directs to specialized agents |
| **Departments** | Specialized agents for department-specific advising (ECE, MECH, CEE, etc.) |
| **Scraper** | Data collection service that gathers course information |
| **WhatsApp** | Integration service enabling access via WhatsApp messaging |

## 📚 API Documentation

The backend exposes several API endpoints:

### Main Endpoints
```
GET /
POST /api/query
POST /api/whatsapp/webhook
POST /api/reset/{session_id}
```

For complete API documentation, visit the `/docs` endpoint after starting the backend service.

## 💻 Development

### Project Structure
```
├── app/                # Main application code
│   ├── api/            # API endpoints
│   ├── core/           # Core functionality
│   ├── db/             # Vector store integration
│   ├── models/         # Data models
│   └── services/       # Department agents and services
├── data/               # Data storage
├── docker/             # Dockerfiles for services
├── docs/               # Documentation
├── frontend/           # Web interface
├── k8s/                # Kubernetes configuration
├── Scraper/            # Data scraping utilities
├── scripts/            # Utility scripts
└── tests/              # Automated tests
```

### Technology Stack
- **Backend**: FastAPI, LangChain, LangGraph
- **Vector DB**: Pinecone
- **LLM**: OpenAI GPT models
- **Frontend**: React
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**:Github actions , ArgoCD
- **Messaging**: Twilio for WhatsApp integration

## 🌐 Deployment

### Docker Deployment
The easiest way to deploy the full application stack is using Docker Compose:
```bash
docker-compose up -d
```

### Kubernetes Deployment
For production environments, Kubernetes deployment is supported using the configurations in the `k8s` directory.


#### Prerequisites
- Azure account with active subscription
- Azure CLI installed (`az`)
- kubectl installed
- Git repository containing the application code
- GitHub account (for CI/CD)


## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [LangChain](https://www.langchain.com/) - LLM framework
- [LangGraph](https://python.langchain.com/docs/langgraph) - Agent orchestration
- [Pinecone](https://www.pinecone.io/) - Vector database
- [OpenAI](https://openai.com/) - LLM provider
- [Docker](https://www.docker.com/) - Containerization
- [Kubernetes](https://kubernetes.io/) - Orchestration
- [Twilio](https://www.twilio.com/) - WhatsApp integration

---

<div align="center">
  <p>PLEASE GIVE US AN A+ </p>
</div> 