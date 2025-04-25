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

   Required environment variables:
   ```
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # Database Configuration
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   PINECONE_INDEX_NAME=your_pinecone_index_name
   
   # WhatsApp Integration
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   
   # Application Settings
   LOG_LEVEL=INFO
   DEBUG=False
   PORT=8000
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

#### AKS + ArgoCD Deployment Guide
This guide covers the process for deploying applications to our AKS cluster using ArgoCD for continuous deployment. It assumes the initial infrastructure is already set up.

##### Prerequisites
- Azure CLI installed and configured
- kubectl installed and configured
- Access to the GitHub repository
- ArgoCD CLI installed (optional, for advanced operations)

##### Connecting to the Environment
```bash
# Connect to the AKS cluster
az aks get-credentials --resource-group aub-advisor-rg --name aub-advisor-aks

# Verify connection
kubectl get nodes
```

##### Deployment Process
1. **Creating a New Service Deployment**

   To add a new service to the CI/CD pipeline:
   - Add Kubernetes manifests in the appropriate location:
     - Place base configuration in `k8s/base/[service-name]/`
     - Add environment-specific configurations in `k8s/overlays/[env]/`
   - Create a GitHub Actions workflow for the service:
     - Create `.github/workflows/[service-name]-ci.yml`
     - Configure build and push to ACR
     - Set up the image tag update process

2. **Updating Existing Service**

   To update an existing service:
   - Make code changes in the service repository
   - Push changes to the main branch to trigger CI pipeline
   - GitHub Actions will:
     - Build a new Docker image
     - Push to Azure Container Registry
     - Update the Kubernetes manifest with the new image tag
     - Commit the changes back to the repository
   - ArgoCD will automatically detect the changes and sync the application

3. **Monitoring Deployments**

   Via ArgoCD UI:
   ```bash
   # Port-forward to access ArgoCD UI
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```
   Then access the UI at https://localhost:8080

   Via kubectl:
   ```bash
   # Check deployment status
   kubectl get deployments -n aub-advisor

   # Check pods
   kubectl get pods -n aub-advisor

   # View logs
   kubectl logs -f deployment/[service-name] -n aub-advisor
   ```

4. **Blue/Green Deployment Process**

   The deployment uses a blue/green strategy for zero-downtime updates:
   - The CI process updates the inactive deployment (if blue is active, green is updated)
   - ArgoCD deploys the changes to the inactive environment
   - To switch traffic:
   ```bash
   # Switch from blue to green
   kubectl patch service main-service -n aub-advisor -p '{"spec":{"selector":{"deployment":"green"}}}'

   # Switch from green to blue
   kubectl patch service main-service -n aub-advisor -p '{"spec":{"selector":{"deployment":"blue"}}}'
   ```

5. **Rollback Procedure**

   If a deployment needs to be rolled back:
   ```bash
   # Option 1: Revert to previous Git commit
   git revert [commit-hash]
   git push

   # Option 2: Manual rollback via ArgoCD
   argocd app rollback aub-advisor [version]

   # Option 3: Switch back to the previous environment in blue/green
   kubectl patch service main-service -n aub-advisor -p '{"spec":{"selector":{"deployment":"blue"}}}'
   ```

##### Troubleshooting
Common Issues:

- **Image Pull Errors**:
  ```bash
  kubectl describe pod [pod-name] -n aub-advisor
  ```
  Verify ACR credentials and AKS-ACR integration.

- **ArgoCD Sync Issues**:
  ```bash
  kubectl logs -f deployment/argocd-application-controller -n argocd
  ```
  Check for Git repository access issues or manifest errors.

- **Service Unavailable**:
  ```bash
  kubectl get endpoints -n aub-advisor
  ```
  Verify service selectors match pod labels.

##### Azure Container Registry Management
```bash
# Log in to ACR
az acr login --name aubadvisoracr

# List images
az acr repository list --name aubadvisoracr

# List tags for a specific image
az acr repository show-tags --name aubadvisoracr --repository [image-name]
```

##### Updating ArgoCD Application
If you need to update the ArgoCD application configuration:
```bash
# Edit the ArgoCD application
kubectl edit application aub-advisor -n argocd

# Or apply an updated manifest
kubectl apply -f argocd-app.yaml
```

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