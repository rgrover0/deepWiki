# Person

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The Person class serves as a foundation for entities with personal details, bearing the responsibility of encapsulating and managing first and last names. Within the application architecture, it plays a crucial role as a base class, leveraging the @MappedSuperclass annotation to provide a common set of attributes for inheriting entities. Key methods, such as setLastName and getLastName, as well as setFirstName and getFirstName, facilitate the manipulation and retrieval of personal details. The class relies on two important fields: lastName and firstName, both of type String, which store the respective personal details. This design enables a standardized and efficient management of personal information across the application.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `setLastName` | `void` | - |
| `getLastName` | `String` | - |
| `setFirstName` | `void` | - |
| `getFirstName` | `String` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `lastName` | `String` | @Column, @NotBlank |
| `firstName` | `String` | @Column, @NotBlank |
