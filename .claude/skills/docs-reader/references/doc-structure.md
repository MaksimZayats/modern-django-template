# Complete Documentation Structure

This reference provides a complete listing of all documentation files and their purposes.

## Contents

- [Documentation Directory Tree](#documentation-directory-tree)
- [File Purposes by Section](#file-purposes-by-section)
- [Cross-References Between Documents](#cross-references-between-documents)
- [Finding Information by Keyword](#finding-information-by-keyword)

## Documentation Directory Tree

```
docs/en/
├── index.md                           # Landing page, architecture overview
├── getting-started/
│   ├── index.md                       # Getting started overview
│   ├── quick-start.md                 # 5-minute setup guide
│   ├── project-structure.md           # Directory layout explanation
│   └── development-environment.md     # Dev tools configuration
├── tutorial/
│   ├── index.md                       # Tutorial overview (Todo List feature)
│   ├── 01-model-and-service.md        # Create Todo model and TodoService
│   ├── 02-ioc-registration.md         # Register in IoC container
│   ├── 03-http-api.md                 # Build TodoController for HTTP API
│   ├── 04-celery-tasks.md             # Add cleanup background task
│   ├── 05-observability.md            # Configure Logfire tracing
│   └── 06-testing.md                  # Write integration tests
├── concepts/
│   ├── index.md                       # Concepts overview
│   ├── service-layer.md               # The Golden Rule, why services matter
│   ├── ioc-container.md               # diwire DI, registration patterns
│   ├── controller-pattern.md          # Controller and AsyncController
│   ├── factory-pattern.md             # FastAPIFactory, CeleryAppFactory
│   └── pydantic-settings.md           # BaseSettings, environment mapping
├── how-to/
│   ├── index.md                       # How-to guides overview
│   ├── add-new-domain.md              # 12-step checklist for new features
│   ├── add-celery-task.md             # Creating background tasks
│   ├── custom-exception-handling.md   # Domain exceptions, controller handling
│   ├── override-ioc-in-tests.md       # Mock services via container
│   ├── secure-endpoints.md            # JWTAuth, rate limiting
│   └── configure-observability.md     # Logfire/OpenTelemetry setup
└── reference/
    ├── index.md                       # Reference overview
    ├── environment-variables.md       # All env vars with prefixes
    ├── makefile.md                    # Available make commands
    └── docker-services.md             # PostgreSQL, Redis, MinIO config
```

## File Purposes by Section

### Getting Started

| File | Purpose | When to Reference |
|------|---------|-------------------|
| `quick-start.md` | Fastest path to running the project | New developers, setup issues |
| `project-structure.md` | Explains directory layout | Understanding codebase organization |
| `development-environment.md` | Dev tool configuration | Setting up IDE, linters, etc. |

### Tutorial

| File | What It Teaches | Prerequisites |
|------|-----------------|---------------|
| `01-model-and-service.md` | Django models, service pattern | None |
| `02-ioc-registration.md` | diwire container, dependency injection | Step 1 |
| `03-http-api.md` | FastAPI controllers, schemas | Steps 1-2 |
| `04-celery-tasks.md` | Task controllers, registry | Steps 1-3 |
| `05-observability.md` | Logfire integration, tracing | Steps 1-4 |
| `06-testing.md` | Test factories, IoC overrides | Steps 1-5 |

### Concepts

| File | Key Ideas | Related How-To |
|------|-----------|----------------|
| `service-layer.md` | Golden Rule, domain exceptions | `add-new-domain.md` |
| `ioc-container.md` | Registration patterns, scopes | `override-ioc-in-tests.md` |
| `controller-pattern.md` | Controller types, exception handling | `custom-exception-handling.md` |
| `factory-pattern.md` | Factory usage, customization | - |
| `pydantic-settings.md` | Environment configuration | - |

### How-To Guides

| File | Task | Time Estimate |
|------|------|---------------|
| `add-new-domain.md` | Add complete feature | Follow all 12 steps |
| `add-celery-task.md` | Create background task | Follow checklist |
| `custom-exception-handling.md` | Handle errors gracefully | Follow pattern |
| `override-ioc-in-tests.md` | Mock dependencies | Apply to tests |
| `secure-endpoints.md` | Add authentication | Apply to controllers |
| `configure-observability.md` | Enable tracing | Configure once |

### Reference

| File | Content Type | Use Case |
|------|--------------|----------|
| `environment-variables.md` | All env vars with defaults | Configuration debugging |
| `makefile.md` | All make commands | Development tasks |
| `docker-services.md` | Container configurations | Infrastructure setup |

## Cross-References Between Documents

### Service Layer Connections

```
service-layer.md (concept)
    ├── Referenced by: add-new-domain.md (step 5)
    ├── Referenced by: 01-model-and-service.md (tutorial)
    └── Referenced by: ioc-container.md (registration)
```

### IoC Container Connections

```
ioc-container.md (concept)
    ├── Referenced by: 02-ioc-registration.md (tutorial)
    ├── Referenced by: override-ioc-in-tests.md (how-to)
    └── Referenced by: add-new-domain.md (steps 6, 8)
```

### Controller Pattern Connections

```
controller-pattern.md (concept)
    ├── Referenced by: 03-http-api.md (tutorial)
    ├── Referenced by: add-new-domain.md (step 7)
    └── Referenced by: custom-exception-handling.md (how-to)
```

## Finding Information by Keyword

| Keyword | Primary Doc | Secondary Doc |
|---------|-------------|---------------|
| service | `concepts/service-layer.md` | `tutorial/01-model-and-service.md` |
| model | `tutorial/01-model-and-service.md` | `how-to/add-new-domain.md` |
| controller | `concepts/controller-pattern.md` | `tutorial/03-http-api.md` |
| IoC | `concepts/ioc-container.md` | `tutorial/02-ioc-registration.md` |
| container | `concepts/ioc-container.md` | `how-to/override-ioc-in-tests.md` |
| test | `tutorial/06-testing.md` | `how-to/override-ioc-in-tests.md` |
| mock | `how-to/override-ioc-in-tests.md` | `tutorial/06-testing.md` |
| celery | `tutorial/04-celery-tasks.md` | `how-to/add-celery-task.md` |
| task | `how-to/add-celery-task.md` | `tutorial/04-celery-tasks.md` |
| exception | `how-to/custom-exception-handling.md` | `concepts/service-layer.md` |
| auth | `how-to/secure-endpoints.md` | - |
| JWT | `how-to/secure-endpoints.md` | - |
| factory | `concepts/factory-pattern.md` | - |
| settings | `concepts/pydantic-settings.md` | `reference/environment-variables.md` |
| env | `reference/environment-variables.md` | - |
| docker | `reference/docker-services.md` | `getting-started/quick-start.md` |
| make | `reference/makefile.md` | - |
| tracing | `tutorial/05-observability.md` | `how-to/configure-observability.md` |
| logfire | `how-to/configure-observability.md` | `tutorial/05-observability.md` |
