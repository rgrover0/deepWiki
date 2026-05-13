# BaseEntity

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The BaseEntity class serves as a foundation for other entities in the application, providing a common set of attributes and methods. It plays a crucial role in the application architecture by defining a base structure for entities, enabling inheritance and code reuse. This class features key methods such as isNew and getId, which determine if an entity is new and retrieve its identifier, respectively. The id field, an Integer type, is a vital component, storing the unique identifier for each entity. As a @MappedSuperclass, it provides a basis for entity mapping, simplifying database interactions for subclasses.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `isNew` | `boolean` | - |
| `setId` | `void` | - |
| `getId` | `Integer` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `id` | `Integer` | @Id, @GeneratedValue(strategy = GenerationType.IDENTITY) |
