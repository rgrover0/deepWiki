# VetController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.vet;`
**Annotations:** @Controller

## Summary
The VetController class is a controller responsible for handling vet-related operations in the application. As part of the application architecture, it plays a crucial role in managing vet data and interactions. This class utilizes the vetRepository field, which is an instance of VetRepository, to access and manipulate vet data. Key methods include showResourcesVetList and findPaginated, which facilitate retrieving and displaying vet information, while addPaginationModel and showVetList enable pagination and listing of vets. The VetController class relies on its dependencies to provide a seamless user experience, making it a vital component of the application's backend logic.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `showResourcesVetList` | `Vets` | @GetMapping({ "/vets" }), @ResponseBody |
| `findPaginated` | `Page<Vet>` | - |
| `addPaginationModel` | `String` | - |
| `showVetList` | `String` | @GetMapping("/vets.html") |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `vetRepository` | `VetRepository` | - |
