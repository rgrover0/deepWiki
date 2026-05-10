# Owner

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.owner;`
**Annotations:** @Entity, @Table(name = "owners")

## Summary
The Owner class is an entity responsible for representing an owner's information in the application. It plays a crucial role in the application architecture by encapsulating data and behavior related to owners, serving as a central component in managing owner-pet relationships. Key methods, such as addPet and getPets, enable the management of pets associated with an owner, while getFullAddress and setTelephone allow for the manipulation of owner contact information. The class relies on fields like pets, telephone, city, and address to store relevant owner data, facilitating a comprehensive representation of owners within the application.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `hasPets` | `boolean` | - |
| `getFullAddress` | `String` | - |
| `addVisit` | `void` | - |
| `toString` | `String` | @Override |
| `getPet` | `Pet` | - |
| `addPet` | `void` | - |
| `getPets` | `List<Pet>` | - |
| `setTelephone` | `void` | - |
| `getTelephone` | `String` | - |
| `setCity` | `void` | - |
| `getCity` | `String` | - |
| `setAddress` | `void` | - |
| `getAddress` | `String` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `pets` | `List<Pet>` | @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER), @JoinColumn(name = "owner_id"), @OrderBy("name") |
| `telephone` | `String` | @Column, @NotBlank, @Pattern(regexp = "\\d{10}", message = "{telephone.invalid}") |
| `city` | `String` | @Column, @NotBlank |
| `address` | `String` | @Column, @NotBlank |
