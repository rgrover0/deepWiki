# Visit

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "visits")

## Summary
The Visit entity represents a single visit in the pet clinic application, responsible for storing and managing visit-related data. As part of the application's domain model, it plays a crucial role in the overall architecture, providing a structured representation of visits. This class includes key methods such as getDate and setDescription, which allow for retrieval and modification of visit details. The date and description fields are essential, storing the visit date as a LocalDate object and a brief description of the visit as a String, respectively. These fields and methods enable effective management of visit information within the application.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getDate` | `LocalDate` | - |
| `setDate` | `void` | - |
| `getDescription` | `String` | - |
| `setDescription` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `date` | `LocalDate` | @Column(name = "visit_date"), @DateTimeFormat(pattern = "yyyy-MM-dd") |
| `description` | `String` | @NotBlank |
