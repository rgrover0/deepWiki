# VetController

**Type:** `CONTROLLER`
**Package:** `package org.springframework.samples.petclinic.vet;`
**Annotations:** @Controller

## Summary
The VetController class is a controller responsible for handling vet-related operations in the application. It plays a crucial role in the application architecture, serving as an intermediary between the user interface and the data access layer. This class utilizes the vetRepository field, which is an instance of VetRepository, to interact with the data storage. Key methods, such as showVetList and findPaginated, enable the retrieval and display of vet information, while addPaginationModel facilitates pagination functionality. As a central component, it ensures seamless communication between the presentation layer and the data access layer, thereby facilitating efficient vet data management.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `showVetList` | `String` | @GetMapping("/vets.html") |
| `addPaginationModel` | `String` | - |
| `findPaginated` | `Page<Vet>` | - |
| `showResourcesVetList` | `Vets` | @GetMapping({ "/vets" }), @ResponseBody |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `vetRepository` | `VetRepository` | - |
