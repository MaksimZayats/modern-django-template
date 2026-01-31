# Extended Question-to-Documentation Mappings

This reference provides comprehensive mappings from common user questions to the appropriate documentation files.

## Contents

- [Architecture & Design](#architecture--design)
  - [Service Layer Questions](#service-layer-questions)
  - [IoC & Dependency Injection Questions](#ioc--dependency-injection-questions)
  - [Controller Questions](#controller-questions)
  - [Factory Questions](#factory-questions)
- [Implementation Tasks](#implementation-tasks)
  - [Adding Features](#adding-features)
  - [Background Tasks](#background-tasks)
  - [Error Handling](#error-handling)
  - [Testing](#testing)
  - [Security](#security)
- [Setup & Configuration](#setup--configuration)
- [Learning Path Questions](#learning-path-questions)
- [Troubleshooting Questions](#troubleshooting-questions)

## Architecture & Design

### Service Layer Questions

| Question | Primary Doc | Answer Location |
|----------|-------------|-----------------|
| "Why can't I import models in controllers?" | `concepts/service-layer.md` | "The Golden Rule" section |
| "What's the difference between controller and service?" | `concepts/service-layer.md` | "Clear Boundaries" table |
| "Where should I put business logic?" | `concepts/service-layer.md` | "What Goes in a Service" |
| "How do I create domain exceptions?" | `concepts/service-layer.md` | "Domain Exceptions" section |
| "What can be imported in controllers?" | `concepts/service-layer.md` | "Acceptable Exceptions" table |

### IoC & Dependency Injection Questions

| Question | Primary Doc | Answer Location |
|----------|-------------|-----------------|
| "How does dependency injection work?" | `concepts/ioc-container.md` | Full document |
| "What is diwire?" | `concepts/ioc-container.md` | Introduction |
| "How do I register a service?" | `concepts/ioc-container.md` | Registration examples |
| "What's the difference between singleton and transient?" | `concepts/ioc-container.md` | Scope section |
| "How do I resolve dependencies?" | `concepts/ioc-container.md` | Resolution examples |

### Controller Questions

| Question | Primary Doc | Answer Location |
|----------|-------------|-----------------|
| "What's the difference between Controller and AsyncController?" | `concepts/controller-pattern.md` | Controller types section |
| "How does exception handling work?" | `concepts/controller-pattern.md` | `handle_exception` section |
| "How do I register routes?" | `concepts/controller-pattern.md` | `register()` examples |
| "Why are methods auto-wrapped?" | `concepts/controller-pattern.md` | Auto-wrapping section |

### Factory Questions

| Question | Primary Doc | Answer Location |
|----------|-------------|-----------------|
| "What is FastAPIFactory?" | `concepts/factory-pattern.md` | HTTP API section |
| "How do I customize the API?" | `concepts/factory-pattern.md` | Customization section |
| "Why use factories instead of direct instantiation?" | `concepts/factory-pattern.md` | Benefits section |

## Implementation Tasks

### Adding Features

| Task | Primary Doc | Key Steps |
|------|-------------|-----------|
| "Add a new CRUD endpoint" | `how-to/add-new-domain.md` | 12-step checklist |
| "Create a new service" | `how-to/add-new-domain.md` | Step 5 |
| "Add a new controller" | `how-to/add-new-domain.md` | Steps 7-10 |
| "Register in IoC" | `how-to/add-new-domain.md` | Steps 6, 8, 9 |

### Background Tasks

| Task | Primary Doc | Key Information |
|------|-------------|-----------------|
| "Create a Celery task" | `how-to/add-celery-task.md` | Full checklist |
| "Register a task" | `how-to/add-celery-task.md` | Registry section |
| "Schedule a task" | `how-to/add-celery-task.md` | Beat configuration |
| "Test a task" | `tutorial/06-testing.md` | Celery tests section |

### Error Handling

| Task | Primary Doc | Key Pattern |
|------|-------------|-------------|
| "Handle domain exceptions" | `how-to/custom-exception-handling.md` | Pattern examples |
| "Convert exceptions to HTTP errors" | `how-to/custom-exception-handling.md` | Controller section |
| "Create custom exceptions" | `how-to/custom-exception-handling.md` | Exception hierarchy |

### Testing

| Task | Primary Doc | Key Pattern |
|------|-------------|-------------|
| "Mock a service" | `how-to/override-ioc-in-tests.md` | Basic pattern |
| "Create test fixtures" | `tutorial/06-testing.md` | Factory section |
| "Test HTTP endpoints" | `tutorial/06-testing.md` | HTTP tests |
| "Test Celery tasks" | `tutorial/06-testing.md` | Celery tests |

### Security

| Task | Primary Doc | Key Information |
|------|-------------|-----------------|
| "Add authentication" | `how-to/secure-endpoints.md` | JWTAuth section |
| "Add rate limiting" | `how-to/secure-endpoints.md` | Throttle section |
| "Protect endpoints" | `how-to/secure-endpoints.md` | Full guide |

## Setup & Configuration

### Environment Setup

| Question | Primary Doc | Key Section |
|----------|-------------|-------------|
| "How do I start the project?" | `getting-started/quick-start.md` | Full guide |
| "What environment variables do I need?" | `reference/environment-variables.md` | Full table |
| "What's the minimum configuration?" | `reference/environment-variables.md` | Required section |

### Docker & Infrastructure

| Question | Primary Doc | Key Section |
|----------|-------------|-------------|
| "What Docker services are needed?" | `reference/docker-services.md` | Services list |
| "How do I configure PostgreSQL?" | `reference/docker-services.md` | PostgreSQL section |
| "How do I configure Redis?" | `reference/docker-services.md` | Redis section |

### Development Tools

| Question | Primary Doc | Key Section |
|----------|-------------|-------------|
| "What make commands are available?" | `reference/makefile.md` | Commands table |
| "How do I run tests?" | `reference/makefile.md` | Testing section |
| "How do I format code?" | `reference/makefile.md` | Formatting section |

## Learning Path Questions

### For New Developers

| Question | Recommended Path |
|----------|------------------|
| "Where do I start?" | `getting-started/quick-start.md` -> `getting-started/project-structure.md` |
| "How do I learn this codebase?" | `tutorial/index.md` (follow all 6 steps) |
| "Show me a complete example" | `tutorial/01-model-and-service.md` through `tutorial/06-testing.md` |

### For Experienced Developers

| Question | Recommended Doc |
|----------|-----------------|
| "I just need to add a feature" | `how-to/add-new-domain.md` |
| "Explain the architecture" | `concepts/service-layer.md` then `concepts/ioc-container.md` |
| "How do I run in production?" | `reference/environment-variables.md` |

## Troubleshooting Questions

### Common Errors

| Error/Issue | Check First | Then Check |
|-------------|-------------|------------|
| "ImportError in controller" | `concepts/service-layer.md` (Golden Rule) | CLAUDE.md |
| "Service not resolved" | `concepts/ioc-container.md` (registration) | `tutorial/02-ioc-registration.md` |
| "Test isolation issues" | `how-to/override-ioc-in-tests.md` | `tutorial/06-testing.md` |
| "Exception not handled" | `how-to/custom-exception-handling.md` | `concepts/controller-pattern.md` |

### Configuration Issues

| Issue | Check |
|-------|-------|
| "Environment variable not working" | `reference/environment-variables.md` (prefix) |
| "Docker service not starting" | `reference/docker-services.md` |
| "Make command failing" | `reference/makefile.md` |
