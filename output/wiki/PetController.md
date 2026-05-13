# PetController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller, @RequestMapping("/owners/{ownerId}")

## Summary
The PetController class is responsible for handling pet-related operations, serving as a crucial component in the application's architecture by bridging the gap between the user interface and the data access layer. As a controller, it plays a key role in managing the flow of data and requests. The class contains key methods such as updatePetDetails and processUpdateForm, which enable the modification of existing pet records, while initCreationForm and processCreationForm facilitate the creation of new pet entries. Important fields include the PetTypeRepository and OwnerRepository dependencies, which provide access to pet and owner data, respectively.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `updatePetDetails` | `void` | - |
| `processUpdateForm` | `String` | @PostMapping("/pets/{petId}/edit") |
| `initUpdateForm` | `String` | @GetMapping("/pets/{petId}/edit") |
| `processCreationForm` | `String` | @PostMapping("/pets/new") |
| `initCreationForm` | `String` | @GetMapping("/pets/new") |
| `initPetBinder` | `void` | @InitBinder("pet") |
| `initOwnerBinder` | `void` | @InitBinder("owner") |
| `findPet` | `Pet` | @ModelAttribute("pet") |
| `findOwner` | `Owner` | @ModelAttribute("owner") |
| `populatePetTypes` | `Collection<PetType>` | @ModelAttribute("types") |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `types` | `PetTypeRepository` | - |
| `owners` | `OwnerRepository` | - |
| `VIEWS_PETS_CREATE_OR_UPDATE_FORM` | `String` | - |
