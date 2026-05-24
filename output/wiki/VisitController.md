# VisitController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller

## Summary
The VisitController class is a core component responsible for handling visit-related operations in the application. As a controller, it plays a crucial role in the application architecture, serving as an intermediary between the user interface and the business logic. This class provides key methods such as setAllowedFields, loadPetWithVisit, and processNewVisitForm, which enable the creation and management of new visits. The owners field, an instance of OwnerRepository, is a vital dependency that facilitates access to owner data. Overall, this controller ensures seamless visit management, leveraging its methods and dependencies to provide a robust user experience.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `setAllowedFields` | `void` | @InitBinder |
| `loadPetWithVisit` | `Visit` | @ModelAttribute("visit") |
| `initNewVisitForm` | `String` | @GetMapping("/owners/{ownerId}/pets/{petId}/visits/new") |
| `processNewVisitForm` | `String` | @PostMapping("/owners/{ownerId}/pets/{petId}/visits/new") |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `owners` | `OwnerRepository` | - |
