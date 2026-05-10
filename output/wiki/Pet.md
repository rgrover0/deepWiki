# Pet

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "pets")

## Summary
The Pet class is an entity responsible for representing a pet in the application, encapsulating its characteristics and behaviors. It plays a crucial role in the application architecture, serving as a central component in the data model. This class provides key methods such as addVisit and getVisits, which allow for managing a pet's visit history, as well as setType and getType for handling the pet's type. The class also includes important fields like visits, type, and birthDate, which are essential for storing a pet's relevant information. Overall, this entity is a fundamental part of the application's data structure.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `addVisit` | `void` | - |
| `getVisits` | `Collection<Visit>` | - |
| `setType` | `void` | - |
| `getType` | `PetType` | - |
| `getBirthDate` | `LocalDate` | - |
| `setBirthDate` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `visits` | `Set<Visit>` | @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER), @JoinColumn(name = "pet_id"), @OrderBy("date ASC") |
| `type` | `PetType` | @ManyToOne, @JoinColumn(name = "type_id") |
| `birthDate` | `LocalDate` | @Column, @DateTimeFormat(pattern = "yyyy-MM-dd") |
