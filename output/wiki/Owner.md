# Owner

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "owners")

## Summary
The Owner entity represents an individual who owns pets in the application, responsible for encapsulating their details and relationships with pets. It plays a crucial role in the application architecture by providing a data model for storing owner information. Key methods include getters and setters for address, city, and telephone, as well as methods for managing pets, such as adding a pet or retrieving a list of pets. The class has fields for address, city, telephone, and a list of pets, which are essential for maintaining owner data. This entity is a fundamental component of the application's data model, enabling the storage and retrieval of owner information.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getAddress` | `String` | - |
| `setAddress` | `void` | - |
| `getCity` | `String` | - |
| `setCity` | `void` | - |
| `getTelephone` | `String` | - |
| `setTelephone` | `void` | - |
| `getPets` | `List<Pet>` | - |
| `addPet` | `void` | - |
| `getPet` | `Pet` | - |
| `toString` | `String` | @Override |
| `addVisit` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `address` | `String` | @Column, @NotBlank |
| `city` | `String` | @Column, @NotBlank |
| `telephone` | `String` | @Column, @NotBlank, @Pattern(regexp = "\\d{10}", message = "{telephone.invalid}") |
| `pets` | `List<Pet>` | @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER), @JoinColumn(name = "owner_id"), @OrderBy("name") |
