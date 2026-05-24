# BaseEntity

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The BaseEntity class serves as a foundation for other entities in the application, providing a common set of attributes and methods. It plays a crucial role in the application architecture by defining a base structure for entities, allowing for inheritance and code reuse. This class features key methods such as getId and setId, which enable access and modification of the entity's identifier, as well as isNew, which checks if the entity is newly created. The id field, of type Integer, stores the unique identifier of the entity. As a @MappedSuperclass, it provides a basis for mapping entities to the database, simplifying the persistence process.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getId` | `Integer` | - |
| `setId` | `void` | - |
| `isNew` | `boolean` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `id` | `Integer` | @Id, @GeneratedValue(strategy = GenerationType.IDENTITY) |
