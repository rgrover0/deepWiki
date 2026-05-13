# NamedEntity

**Type:** `CLASS`
**Package:** `package org.springframework.samples.petclinic.model;`
**Annotations:** @MappedSuperclass

## Summary
The NamedEntity class serves as a base entity, providing a foundation for other classes to inherit its properties and behavior. Within the application architecture, it plays a crucial role in defining a common structure for entities that have a name. This class features key methods, including toString and setName, which enable the conversion to a string representation and modification of the name, respectively, while the getName method allows for name retrieval. The name field, a string type, is a vital component, storing the entity's name. As a @MappedSuperclass, it provides a mapped inheritance strategy for its subclasses.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `toString` | `String` | @Override |
| `setName` | `void` | - |
| `getName` | `String` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `name` | `String` | @Column, @NotBlank |
