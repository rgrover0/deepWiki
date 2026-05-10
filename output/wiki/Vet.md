# Vet

**Type:** `ENTITY`
**Package:** `package org.springframework.samples.petclinic.vet;`
**Annotations:** @Entity, @Table(name = "vets")

## Summary
This entity represents a veterinarian in the application, responsible for managing their specialties. It plays a crucial role in the application architecture, serving as a data model for veterinarians. The class provides key methods such as addSpecialty, which allows adding a new specialty, and getSpecialties, which retrieves a list of assigned specialties. The specialties field, a set of Specialty objects, stores the veterinarian's areas of expertise. This entity is annotated with @Entity and @Table, indicating its mapping to a database table, and is part of the org.springframework.samples.petclinic.vet package.

## Methods
| Method | Returns | Annotations |
|--------|---------|-------------|
| `addSpecialty` | `void` | - |
| `getNrOfSpecialties` | `int` | - |
| `getSpecialties` | `List<Specialty>` | @XmlElement |
| `getSpecialtiesInternal` | `Set<Specialty>` | - |

## Fields
| Field | Type | Annotations |
|-------|------|-------------|
| `specialties` | `Set<Specialty>` | @ManyToMany(fetch = FetchType.EAGER), @JoinTable(name = "vet_specialties", joinColumns = @JoinColumn(name = "vet_id"),
			inverseJoinColumns = @JoinColumn(name = "specialty_id")) |
