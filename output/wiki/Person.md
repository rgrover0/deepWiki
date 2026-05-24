# Person

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The Person class serves as a foundational entity in the application, responsible for encapsulating individual attributes. As a `@MappedSuperclass`, it plays a crucial role in the application architecture by providing a base mapping for subclasses. This class provides key methods such as `getFirstName` and `setFirstName`, which allow for the retrieval and modification of an individual's first name, while `getLastName` and `setLastName` serve a similar purpose for the last name. The `firstName` and `lastName` fields are essential in storing this information. Overall, this class provides a fundamental structure for representing individuals within the application.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getFirstName` | `String` | - |
| `setFirstName` | `void` | - |
| `getLastName` | `String` | - |
| `setLastName` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `firstName` | `String` | @Column, @NotBlank |
| `lastName` | `String` | @Column, @NotBlank |
