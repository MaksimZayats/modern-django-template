---
name: docs-reader
description: Answers questions using project documentation in docs/en/.
version: 1.0.0
---

# Documentation Reader Skill

This skill helps you navigate and reference the comprehensive project documentation located in `docs/en/`. Always consult these docs before answering questions about the codebase.

## Documentation Framework: Diataxis

The documentation follows the [Diataxis framework](https://diataxis.fr/). Use this mapping to find the right content:

| User Intent | Doc Section | Location |
|-------------|-------------|----------|
| "I want to learn" | Tutorial | `docs/en/tutorial/` |
| "I want to do X" | How-To Guides | `docs/en/how-to/` |
| "I want to understand" | Concepts | `docs/en/concepts/` |
| "I need facts" | Reference | `docs/en/reference/` |

## Quick Reference: Documentation Map

### Getting Started (Onboarding)

| Question | File |
|----------|------|
| How do I set up the project? | `docs/en/getting-started/quick-start.md` |
| What's the project structure? | `docs/en/getting-started/project-structure.md` |
| How do I configure my dev environment? | `docs/en/getting-started/development-environment.md` |

### Tutorial (Step-by-Step Learning)

The tutorial builds a complete Todo List feature:

| Step | Topic | File |
|------|-------|------|
| 1 | Model & Service | `docs/en/tutorial/01-model-and-service.md` |
| 2 | IoC Registration | `docs/en/tutorial/02-ioc-registration.md` |
| 3 | HTTP API | `docs/en/tutorial/03-http-api.md` |
| 4 | Celery Tasks | `docs/en/tutorial/04-celery-tasks.md` |
| 5 | Observability | `docs/en/tutorial/05-observability.md` |
| 6 | Testing | `docs/en/tutorial/06-testing.md` |

### Concepts (Understanding Architecture)

| Topic | File | Key Content |
|-------|------|-------------|
| Service Layer | `docs/en/concepts/service-layer.md` | The Golden Rule, why services matter |
| IoC Container | `docs/en/concepts/ioc-container.md` | Dependency injection with diwire |
| Controller Pattern | `docs/en/concepts/controller-pattern.md` | HTTP, Celery controllers |
| Factory Pattern | `docs/en/concepts/factory-pattern.md` | FastAPIFactory, CeleryAppFactory |
| Pydantic Settings | `docs/en/concepts/pydantic-settings.md` | Environment-based configuration |

### How-To Guides (Task-Focused)

| Task | File |
|------|------|
| Add a new domain/feature | `docs/en/how-to/add-new-domain.md` |
| Add a Celery task | `docs/en/how-to/add-celery-task.md` |
| Handle exceptions | `docs/en/how-to/custom-exception-handling.md` |
| Override IoC in tests | `docs/en/how-to/override-ioc-in-tests.md` |
| Secure endpoints | `docs/en/how-to/secure-endpoints.md` |
| Configure observability | `docs/en/how-to/configure-observability.md` |

### Reference (Facts & Details)

| Topic | File |
|-------|------|
| Environment variables | `docs/en/reference/environment-variables.md` |
| Makefile commands | `docs/en/reference/makefile.md` |
| Docker services | `docs/en/reference/docker-services.md` |

## How to Use This Skill

### Step 1: Identify the Question Type

Match the user's question to a Diataxis category:

- **Tutorial questions**: "How do I learn...", "Walk me through...", "Show me step by step..."
- **How-To questions**: "How do I add...", "How can I configure...", "What's the process for..."
- **Concept questions**: "What is...", "Why does...", "How does... work", "Explain..."
- **Reference questions**: "What are the options for...", "List all...", "What environment variables..."

### Step 2: Read the Relevant Documentation

Use the Read tool to access the appropriate documentation file:

```
Read: docs/en/concepts/service-layer.md
```

### Step 3: Answer from Documentation

Quote or reference specific sections from the docs. Always provide file paths for further reading.

## Common Question Mappings

### Architecture Questions

| Question | Read |
|----------|------|
| "How does the service layer work?" | `docs/en/concepts/service-layer.md` |
| "Why can't controllers use models?" | `docs/en/concepts/service-layer.md` |
| "How does dependency injection work?" | `docs/en/concepts/ioc-container.md` |
| "What's the factory pattern?" | `docs/en/concepts/factory-pattern.md` |
| "How are controllers structured?" | `docs/en/concepts/controller-pattern.md` |

### Implementation Questions

| Question | Read |
|----------|------|
| "How do I add a new feature?" | `docs/en/how-to/add-new-domain.md` |
| "How do I create a Celery task?" | `docs/en/how-to/add-celery-task.md` |
| "How do I handle errors?" | `docs/en/how-to/custom-exception-handling.md` |
| "How do I mock services in tests?" | `docs/en/how-to/override-ioc-in-tests.md` |
| "How do I protect endpoints?" | `docs/en/how-to/secure-endpoints.md` |

### Setup Questions

| Question | Read |
|----------|------|
| "How do I set up the project?" | `docs/en/getting-started/quick-start.md` |
| "What commands are available?" | `docs/en/reference/makefile.md` |
| "What env vars do I need?" | `docs/en/reference/environment-variables.md` |
| "What Docker services exist?" | `docs/en/reference/docker-services.md` |

### Learning Questions

| Question | Read First |
|----------|------------|
| "Show me a complete example" | `docs/en/tutorial/index.md` (then follow all steps) |
| "How do I build a feature from scratch?" | `docs/en/tutorial/01-model-and-service.md` |
| "How do I write tests?" | `docs/en/tutorial/06-testing.md` |

## Key Architectural Rules

Always reference these when answering architecture questions:

### The Golden Rule

```
Controller -> Service -> Model

Controllers NEVER import models directly.
```

From `docs/en/concepts/service-layer.md`:
> This rule is non-negotiable. Every database operation must go through a service.

### IoC Registration Order

From `docs/en/concepts/ioc-container.md`:
```python
container = Container()
register_core(container)           # 1. Domain services first
register_infrastructure(container) # 2. Infrastructure (JWT, auth)
register_delivery(container)       # 3. Controllers and factories
```

### Controller Types

From `docs/en/concepts/controller-pattern.md`:
- `Controller` (sync) - HTTP API, Celery tasks

## Additional Documentation

Also check `CLAUDE.md` in the project root - it contains development guidelines and code quality requirements.

## Reference Files

For deeper documentation exploration, see:
- `references/doc-structure.md` - Complete file listing
- `references/question-mappings.md` - Extended Q&A mappings
