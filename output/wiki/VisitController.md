# VisitController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller

## Summary
The VisitController class is a controller responsible for handling visit-related operations in the application. As part of the application architecture, it plays a crucial role in managing the interaction between the user interface and the data access layer. This class contains key methods such as processNewVisitForm and initNewVisitForm, which are used to process and initialize new visit forms, respectively. The loadPetWithVisit method is also significant, as it loads a pet with its associated visit. The owners field, which is an instance of OwnerRepository, is an important dependency that enables data access and manipulation. Overall, this controller ensures seamless visit management in the application.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `processNewVisitForm` | `String` | @PostMapping("/owners/{ownerId}/pets/{petId}/visits/new") |
| `initNewVisitForm` | `String` | @GetMapping("/owners/{ownerId}/pets/{petId}/visits/new") |
| `loadPetWithVisit` | `Visit` | @ModelAttribute("visit") |
| `setAllowedFields` | `void` | @InitBinder |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `owners` | `OwnerRepository` | - |
