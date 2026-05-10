# Visit

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "visits")

## Summary
The Visit entity represents a single visit in the pet clinic application, responsible for storing and managing visit-related data. As part of the application's data model, it plays a crucial role in the overall architecture, facilitating the interaction between owners, pets, and clinic staff. Key methods, such as setDescription and setDate, allow for the modification of visit details, while getDescription and getDate provide access to the visit's description and date, respectively. The description and date fields are essential in capturing the visit's purpose and scheduling, making them vital components of the application's functionality.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `setDescription` | `void` | - |
| `getDescription` | `String` | - |
| `setDate` | `void` | - |
| `getDate` | `LocalDate` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `description` | `String` | @NotBlank |
| `date` | `LocalDate` | @Column(name = "visit_date"), @DateTimeFormat(pattern = "yyyy-MM-dd") |
