# Vet

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.vet;`
**Annotations:** @Entity, @Table(name = "vets")

## Summary
The Vet entity is responsible for representing a veterinarian in the application, encapsulating their specialties and related data. As part of the application's domain model, it plays a crucial role in the overall architecture, interacting with other entities such as Specialty. Key methods include getSpecialtiesInternal and addSpecialty, which manage the veterinarian's specialties. The specialties field, a Set of Specialty objects, is a vital dependency, storing the veterinarian's areas of expertise. This entity is annotated with @Entity and @Table, indicating its mapping to a database table, and is located in the org.springframework.samples.petclinic.vet package.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `getSpecialtiesInternal` | `Set<Specialty>` | - |
| `getSpecialties` | `List<Specialty>` | @XmlElement |
| `getNrOfSpecialties` | `int` | - |
| `addSpecialty` | `void` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `specialties` | `Set<Specialty>` | @ManyToMany(fetch = FetchType.EAGER), @JoinTable(name = "vet_specialties", joinColumns = @JoinColumn(name = "vet_id"),
			inverseJoinColumns = @JoinColumn(name = "specialty_id")) |
