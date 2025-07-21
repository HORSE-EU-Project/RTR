# RTR Service - Refactored Structure

This document describes the new, refactored structure of the RTR (Reliable Trust Resilience) service.

## Project Structure

```
_HORSE_RTR/
├── .github/                 # GitHub workflows and configurations
├── ansible_playbooks/      # Ansible playbook templates for mitigations
├── config/                  # Centralized configuration files
│   ├── mongod.conf         # MongoDB configuration
│   └── mongo-init.js       # MongoDB initialization script
├── models/                  # LLM model files (GGUF format)
│   └── README.md           # Model download instructions
├── src/                     # Main application source code
│   └── rtr_service/
│       ├── __init__.py
│       ├── api/            # FastAPI routers for different endpoints
│       │   ├── __init__.py
│       │   └── translate.py # Logic for the /translate endpoint
│       ├── auth/           # Authentication logic
│       │   ├── __init__.py
│       │   ├── hashing.py  # Password hashing utilities
│       │   ├── jwt.py      # JWT token handling (was jwttoken.py)
│       │   └── oauth.py    # OAuth2 authentication
│       ├── core/           # Core logic (e.g., config loading)
│       │   ├── __init__.py
│       │   └── settings.py # Centralized settings management
│       ├── database/       # Database connection & models
│       │   ├── __init__.py
│       │   └── connection.py # MongoDB connection management
│       ├── llm/            # LLM client logic
│       │   ├── __init__.py
│       │   └── client.py   # LLM interface for natural language processing
│       ├── mitigation/     # Mitigation-specific logic
│       │   ├── __init__.py
│       │   ├── action.py   # Mitigation action models (was mitigation_action_class.py)
│       │   └── rules.py    # Playbook generation rules (was mitigation_regex_control.py)
│       └── main.py         # FastAPI app entry point (was IBI-RTR_api.py)
├── tests/                  # Tests mirror the 'src' structure
├── .env                    # Environment variables
├── .gitignore              # Git ignore rules
├── docker-compose.yml      # Docker composition (updated for new structure)
├── Dockerfile              # Docker build instructions (updated)
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## Key Changes Made

### 1. **Modularization**
- Separated authentication logic into `src/rtr_service/auth/`
- Isolated mitigation logic in `src/rtr_service/mitigation/`
- Created dedicated database connection management
- Added LLM client infrastructure for future AI integration

### 2. **Configuration Management**
- Centralized all configuration files in `config/`
- Created `src/rtr_service/core/settings.py` for unified settings management
- Environment-based configuration with sensible defaults

### 3. **API Structure**
- Main application in `src/rtr_service/main.py`
- API endpoints organized in `src/rtr_service/api/`
- Added `/translate` endpoint for future LLM integration

### 4. **Docker Integration**
- Updated `Dockerfile` to work with new structure
- Modified `docker-compose.yml` to mount specific directories
- Updated paths in both files to reference new locations

### 5. **File Mappings**
- `IBI-RTR_api.py` → `src/rtr_service/main.py`
- `mitigation_action_class.py` → `src/rtr_service/mitigation/action.py`
- `mitigation_regex_control.py` → `src/rtr_service/mitigation/rules.py`
- `jwttoken.py` → `src/rtr_service/auth/jwt.py`
- `oauth.py` → `src/rtr_service/auth/oauth.py`
- `hashing.py` → `src/rtr_service/auth/hashing.py`
- `mongod.conf` → `config/mongod.conf`
- `mongo-init.js` → `config/mongo-init.js`

## Running the Application

### Development Mode
```bash
uvicorn src.rtr_service.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Mode
```bash
docker-compose up --build
```

## New Features Ready for Implementation

### 1. **LLM Translation Endpoint**
- Endpoint: `POST /api/v1/translate`
- Purpose: Convert natural language to structured mitigation actions
- Location: `src/rtr_service/api/translate.py`
- Client: `src/rtr_service/llm/client.py`

### 2. **Model Management**
- Model storage in `models/` directory
- GGUF format support prepared
- Configuration through environment variables

### 3. **Enhanced Configuration**
- Single source of truth for all settings
- Environment-based configuration
- Type-safe settings management

## Migration Notes

### Import Changes
If you have external scripts that import from the old structure, update the imports:

**Old:**
```python
from mitigation_action_class import mitigation_action_model
from mitigation_regex_control import playbook_creator
from jwttoken import create_access_token
```

**New:**
```python
from src.rtr_service.mitigation.action import mitigation_action_model
from src.rtr_service.mitigation.rules import playbook_creator
from src.rtr_service.auth.jwt import create_access_token
```

### Environment Variables
No changes to environment variables are required. The new settings system maintains backward compatibility.

### API Endpoints
All existing API endpoints remain unchanged and fully functional.

## Benefits of New Structure

1. **Maintainability**: Clear separation of concerns
2. **Scalability**: Modular architecture supports growth
3. **Testability**: Each module can be tested independently
4. **Future-Ready**: LLM integration infrastructure prepared
5. **Standards Compliance**: Follows Python packaging best practices

## Next Steps

1. **Test the restructured application** to ensure all functionality works
2. **Implement LLM integration** using the prepared infrastructure
3. **Add comprehensive tests** following the new structure
4. **Update CI/CD pipelines** to use new entry points
5. **Download and configure LLM models** in the `models/` directory
