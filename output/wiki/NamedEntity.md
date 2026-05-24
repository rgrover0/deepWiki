# NamedEntity

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The NamedEntity class serves as a base class for entities that have a name, providing a common structure for inheritance. Within the application architecture, it plays a crucial role as a mapped superclass, allowing subclasses to inherit its properties. This class features key methods such as getName and setName, which enable retrieval and modification of the entity's name, as well as a toString method for string representation. The name field, a string type, is a vital component, storing the entity's name. As a mapped superclass, it facilitates a standardized approach to entity naming, streamlining data modeling and management.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getName` | `String` | - |
| `setName` | `void` | - |
| `toString` | `String` | @Override |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `name` | `String` | @Column, @NotBlank |
