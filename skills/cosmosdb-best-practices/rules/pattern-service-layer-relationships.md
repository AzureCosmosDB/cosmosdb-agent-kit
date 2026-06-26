---
title: Use a service layer to hydrate document references before rendering
impact: HIGH
impactDescription: bridges document storage with frameworks expecting object graphs, prevents empty/null relationship data
tags: pattern, service-layer, relationships, hydration, template, controller
---

## Use a service layer to hydrate document references before rendering

When using ID-based references between Cosmos DB documents (see `model-relationship-references`), create a service layer that populates transient relationship properties before returning entities to controllers, templates, or API responses. Never return repository results directly to the presentation layer without hydrating relationships.

**Incorrect (controller accesses repository directly — empty relationships):**

```java
@Controller
public class VetController {

    @Autowired
    private VetRepository vetRepository;

    @GetMapping("/vets")
```

**Correct (service layer hydrates relationships):**


```java
@Service
public class VetService {

    private final VetRepository vetRepository;
    private final SpecialtyRepository specialtyRepository;

    public VetService(VetRepository vetRepository,
```

```java
@Controller
public class VetController {

    @Autowired
    private VetService vetService;  // ✅ Service, not repository

    @GetMapping("/vets")
```
