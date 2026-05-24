# Pet

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "pets")

## Summary
The Pet class is an entity responsible for representing a pet in the application, encapsulating its properties and behavior. It plays a crucial role in the application architecture, serving as a data model for storing and managing pet information. This class provides key methods such as setBirthDate and addVisit, which allow for modification of a pet's birth date and addition of visits, respectively. The class also includes important fields like birthDate, type, and visits, which are essential for maintaining a pet's profile. As an entity, it is annotated with @Entity and @Table, indicating its mapping to a database table, and is part of the org.springframework.samples.petclinic.owner package.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `setBirthDate` | `void` | - |
| `getBirthDate` | `LocalDate` | - |
| `getType` | `PetType` | - |
| `setType` | `void` | - |
| `getVisits` | `Collection<Visit>` | - |
| `addVisit` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `birthDate` | `LocalDate` | @Column, @DateTimeFormat(pattern = "yyyy-MM-dd") |
| `type` | `PetType` | @ManyToOne, @JoinColumn(name = "type_id") |
| `visits` | `Set<Visit>` | @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER), @JoinColumn(name = "pet_id"), @OrderBy("date ASC") |
