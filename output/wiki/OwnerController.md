# OwnerController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller

## Summary
The OwnerController class is responsible for handling owner-related operations, serving as a crucial component in the application's architecture. It plays a key role in managing owner data, acting as an intermediary between the user interface and the data access layer. This controller contains methods such as showOwner, processUpdateOwnerForm, and findOwner, which enable the retrieval, creation, and updating of owner information. The owners field, an instance of OwnerRepository, is a vital dependency, providing access to owner data, while the VIEWS_OWNER_CREATE_OR_UPDATE_FORM field stores a string representing the view for creating or updating owner forms. Overall, this class facilitates the interaction between the application's user interface and the underlying data storage, ensuring seamless owner data management.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `showOwner` | `ModelAndView` | @GetMapping("/owners/{ownerId}") |
| `processUpdateOwnerForm` | `String` | @PostMapping("/owners/{ownerId}/edit") |
| `initUpdateOwnerForm` | `String` | @GetMapping("/owners/{ownerId}/edit") |
| `findPaginatedForOwnersLastName` | `Page<Owner>` | - |
| `addPaginationModel` | `String` | - |
| `processFindForm` | `String` | @GetMapping("/owners") |
| `initFindForm` | `String` | @GetMapping("/owners/find") |
| `processCreationForm` | `String` | @PostMapping("/owners/new") |
| `initCreationForm` | `String` | @GetMapping("/owners/new") |
| `findOwner` | `Owner` | @ModelAttribute("owner") |
| `setAllowedFields` | `void` | @InitBinder |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `owners` | `OwnerRepository` | - |
| `VIEWS_OWNER_CREATE_OR_UPDATE_FORM` | `String` | - |
