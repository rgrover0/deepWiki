# PetTypeFormatter

**Type:** `COMPONENT`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Component

## Summary
This component is responsible for formatting pet types, playing a crucial role in the application's data processing layer. As a key part of the application architecture, it enables seamless conversion between internal and external representations of pet types. The `parse` and `print` methods are essential, allowing for the conversion of `PetType` objects to strings and vice versa. The `types` field, which is an instance of `PetTypeRepository`, provides access to the repository of pet types, facilitating these conversions. This component's functionality is annotated with `@Component`, indicating its status as a Spring-managed bean, and is located in the `org.springframework.samples.petclinic.owner` package.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `parse` | `PetType` | @Override |
| `print` | `String` | @Override |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `types` | `PetTypeRepository` | - |
