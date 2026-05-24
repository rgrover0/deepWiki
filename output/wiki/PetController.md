# PetController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Controller, @RequestMapping("/owners/{ownerId}")

## Summary
The PetController class is responsible for handling owner and pet-related operations, serving as a crucial component in the application's architecture. It plays a key role in managing the interaction between owners and their pets, facilitating the creation and update of pet details. This controller utilizes key methods such as initCreationForm and processUpdateForm to handle pet creation and update processes. The class relies on important fields, including the OwnerRepository and PetTypeRepository, which provide access to owner and pet type data. Overall, it acts as a central point for pet management, leveraging its dependencies to provide a seamless user experience.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `populatePetTypes` | `Collection<PetType>` | @ModelAttribute("types") |
| `findOwner` | `Owner` | @ModelAttribute("owner") |
| `findPet` | `Pet` | @ModelAttribute("pet") |
| `initOwnerBinder` | `void` | @InitBinder("owner") |
| `initPetBinder` | `void` | @InitBinder("pet") |
| `initCreationForm` | `String` | @GetMapping("/pets/new") |
| `processCreationForm` | `String` | @PostMapping("/pets/new") |
| `initUpdateForm` | `String` | @GetMapping("/pets/{petId}/edit") |
| `processUpdateForm` | `String` | @PostMapping("/pets/{petId}/edit") |
| `updatePetDetails` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `VIEWS_PETS_CREATE_OR_UPDATE_FORM` | `String` | - |
| `owners` | `OwnerRepository` | - |
| `types` | `PetTypeRepository` | - |
