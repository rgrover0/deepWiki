# OwnerController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller

## Summary
The OwnerController class is a controller responsible for handling owner-related operations in the application. It plays a crucial role in the application architecture, acting as an intermediary between the user interface and the data access layer. This class contains key methods such as findOwner, initCreationForm, and processCreationForm, which enable owner data retrieval, creation, and updating. The owners field, an instance of OwnerRepository, is a significant dependency that facilitates data access. Overall, the OwnerController manages owner data and provides necessary functionality to support the application's features.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `setAllowedFields` | `void` | @InitBinder |
| `findOwner` | `Owner` | @ModelAttribute("owner") |
| `initCreationForm` | `String` | @GetMapping("/owners/new") |
| `processCreationForm` | `String` | @PostMapping("/owners/new") |
| `initFindForm` | `String` | @GetMapping("/owners/find") |
| `processFindForm` | `String` | @GetMapping("/owners") |
| `addPaginationModel` | `String` | - |
| `findPaginatedForOwnersLastName` | `Page<Owner>` | - |
| `initUpdateOwnerForm` | `String` | @GetMapping("/owners/{ownerId}/edit") |
| `processUpdateOwnerForm` | `String` | @PostMapping("/owners/{ownerId}/edit") |
| `showOwner` | `ModelAndView` | @GetMapping("/owners/{ownerId}") |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `VIEWS_OWNER_CREATE_OR_UPDATE_FORM` | `String` | - |
| `owners` | `OwnerRepository` | - |
