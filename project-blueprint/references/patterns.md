# Architectural pattern signatures

Cheatsheet for labeling the architecture **after** slice discovery is complete. The pattern label is a summary of what was found, not a recipe to apply.

For each pattern below: **folder signals**, **code-level signals**, **anti-signals** (refute the hypothesis), and confidence notes.

If the project mixes patterns, label it "**Pragmatic mix**" and describe what it is — don't force a single label.

---

## DDD — Domain-Driven Design

**Folder signals**
- `domain/`, `domains/`, or per-context folders like `ordering/`, `billing/`, each with internal structure
- Sub-folders inside a context: `entities/`, `value-objects/`, `aggregates/`, `repositories/`, `services/` (domain services), `events/`
- `bounded-contexts/` or `contexts/` at top level

**Code-level signals**
- Entity classes with `id` and explicit invariants in constructors
- Value objects: small immutable types with equality by value
- Repository **interfaces** in `domain/`, implementations elsewhere
- Domain events emitted on state changes
- Class/method names mirror business terms (`PlaceOrder`, not `CreateRecord`)

**Anti-signals**
- All "entities" are anemic data bags with public setters → not real DDD
- Repositories return ORM models directly → Layered/CRUD wearing DDD vocabulary

**Confidence note**: many projects use DDD *vocabulary* without DDD *enforcement*. Look for invariants and value objects before claiming high confidence.

---

## Hexagonal — Ports & Adapters

**Folder signals**
- `ports/` + `adapters/` (explicit form)
- `domain/` + `application/` + `infrastructure/` (common implicit form)
- Adapters split into `primary/`/`driving/` and `secondary/`/`driven/`

**Code-level signals**
- Interfaces (ports) in `domain/` or `application/`, implementations in `infrastructure/`
- Use cases orchestrate domain logic and depend only on ports
- DI wires adapters at the edge (`main.*`, composition root)

**Verification grep**
```bash
# Domain should NOT import infrastructure
grep -rn "from.*infrastructure\|import.*infrastructure" src/domain/
```
Zero results = good. Non-zero = either broken or not really Hexagonal.

**Anti-signals**
- Domain imports ORM, HTTP, or framework types
- "Ports" that aren't interfaces

---

## Clean Architecture

**Folder signals**
- `entities/` + `use_cases/` (or `usecases/`, `interactors/`) + `interface_adapters/` + `frameworks/`
- Concentric naming: `enterprise/`, `application/`, `interface/`, `external/`

**Code-level signals**
- Use case classes with single `execute()` / `handle()` method
- Input/output DTOs per use case (`...Request`, `...Response`)
- Presenter pattern: use case returns to presenter that formats for delivery

**Anti-signals**
- Use cases call infrastructure directly
- No DTOs; use cases return ORM models

**Note**: Hexagonal and Clean overlap heavily. Use the team's stated terminology if available.

---

## MVC — Model-View-Controller

**Folder signals**
- `models/` + `views/` + `controllers/`
- Sometimes `helpers/`, `mailers/`, `decorators/` (Rails-style)

**Code-level signals**
- Controllers handle HTTP, return rendered views
- Models are ORM classes (ActiveRecord, Eloquent, Django models)
- Views are templates (ERB, Blade, Jinja, Thymeleaf, JSX)

**Anti-signals**
- No view layer → it's a JSON API; closer to Layered

**Frameworks that lean MVC**: Rails, Laravel, Django (with templates), ASP.NET MVC, Spring MVC.

---

## Layered (3-tier)

**Folder signals**
- `controllers/` + `services/` + `repositories/` (no `domain/` separation)
- Sometimes `web/` + `business/` + `data/`

**Code-level signals**
- Services contain logic; entities are passive
- Repositories wrap the ORM
- Top-down: controllers → services → repositories

**This is the most common pattern** in mainstream backend code (Spring Boot, NestJS, FastAPI tutorials). Don't oversell it as DDD or Hexagonal unless the structural separation is real.

---

## CQRS — Command Query Responsibility Segregation

**Folder signals**
- `commands/` + `queries/` separate paths
- `command-handlers/` + `query-handlers/`
- Often paired with event sourcing: `events/`, `event-store/`, `projections/`

**Code-level signals**
- Command objects (`PlaceOrderCommand`) with one handler each
- Query objects returning DTOs, not entities
- Separate read DB or read models if event-sourced

**Frameworks**: MediatR (.NET), nestjs/cqrs, axon (Java).

---

## Event-driven / Pub-sub

**Folder signals**
- `events/`, `handlers/`, `subscribers/`, `listeners/`, `consumers/`, `producers/`
- Queue/broker config: `kafka/`, `rabbitmq/`, `sqs/`, `pubsub/`

**Code-level signals**
- Event bus or message broker setup at entry point
- Handlers subscribe to event types, not URLs
- Often combined with another pattern (DDD + events, CQRS + events)

---

## Feature-sliced / Vertical slicing

**Folder signals**
- Top-level `features/`, each with its own `api/`, `model/`, `ui/`, `lib/`
- Or `modules/` where each is a self-contained vertical slice

**Code-level signals**
- All code for one feature in one folder, regardless of technical layer
- Cross-feature dependencies are explicit and limited

**Anti-signals**
- Features import each other's internals freely → horizontal pretending to be vertical

---

## Modular monolith

**Folder signals**
- Top-level `modules/` or `packages/`, each a mini-application
- Each module has its own internal layering
- A clear "public API" per module (facade file)

**Code-level signals**
- Module boundaries enforced (sometimes via build system: Java modules, NestJS modules, Go internal)
- Inter-module calls through facade

---

## Microservices

**Folder signals**
- Top-level `services/`, each its own deployable
- Each has its own manifest and Dockerfile
- Often top-level `shared/` or `proto/` for contracts

**Code-level signals**
- Inter-service via HTTP, gRPC, or queues
- Independent deploys; each owns its data

**Anti-signals**
- All "services" share one database → distributed monolith
- All "services" deploy together → also distributed monolith

---

## Onion Architecture

Almost identical to Hexagonal/Clean. Folder hints:
- `core/` or `domain/` innermost
- `application/`, then `infrastructure/`
- Strict rule: dependencies point inward

If the team says "Onion", use that label. Otherwise call it Hexagonal.

---

## Pragmatic mixes (the honest answer)

Most real codebases mix patterns. Common combinations:
- **Layered + DDD entities** — services/repositories outside, rich domain models inside
- **Hexagonal + CQRS** — separate command and query application services, both depending on domain ports
- **Modular monolith + DDD per module** — each module is a bounded context

Don't force a single label. *"Layered overall with DDD-style entities in `domain/order/` only"* is more honest and useful than picking one label and hiding contradictions.
