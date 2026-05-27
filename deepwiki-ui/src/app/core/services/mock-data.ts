import { Suite } from '../models';

export const MOCK_SUITES: Suite[] = [
  {
    id: 'pet-management-platform',
    name: 'Pet Management Platform',
    description: 'Spring Boot backend for managing pets, owners, vets and clinic visits',
    color: '#2878CC',
    projects: [
      {
        id: 'spring-petclinic',
        name: 'Spring PetClinic',
        suite: 'pet-management-platform',
        techStack: ['Java 17', 'Spring Boot 3', 'JPA', 'Thymeleaf', 'MySQL'],
        description: 'Reference Spring Boot application implementing a veterinary clinic management system.',
        story: 'The canonical Spring Boot showcase app — used to demonstrate best practices for building production-grade Spring applications.',
        status: 'active',
        lastDeploy: '2026-05-01',
        modules: [
          {
            id: 'owner-management',
            name: 'Owner Management',
            description: 'CRUD operations for pet owners',
            features: ['Create owner', 'Search owners by last name', 'Edit owner details', 'View owner pets'],
            classCount: 4,
            type: 'feature',
          },
          {
            id: 'pet-management',
            name: 'Pet Management',
            description: 'Pet registration and type management',
            features: ['Add pet to owner', 'Edit pet details', 'Pet type formatting', 'Pet validation'],
            classCount: 4,
            type: 'feature',
          },
          {
            id: 'visit-tracking',
            name: 'Visit Tracking',
            description: 'Vet visit scheduling and history',
            features: ['Schedule visit', 'View visit history', 'Visit form validation'],
            classCount: 2,
            type: 'feature',
          },
          {
            id: 'vet-directory',
            name: 'Vet Directory',
            description: 'Veterinarian profiles and specialties',
            features: ['List vets', 'Vet specialties', 'Paginated vet view'],
            classCount: 4,
            type: 'core',
          },
          {
            id: 'infrastructure',
            name: 'Infrastructure',
            description: 'Caching, configuration, and cross-cutting concerns',
            features: ['Infinispan cache config', 'Web MVC configuration', 'Runtime hints'],
            classCount: 3,
            type: 'core',
          },
        ],
        relations: [],
        apis: [
          { id: 'get-owners',    name: 'List Owners',    type: 'exposed', method: 'GET',    endpoint: '/owners',            description: 'Search owners by last name', authRequired: false },
          { id: 'post-owners',   name: 'Create Owner',   type: 'exposed', method: 'POST',   endpoint: '/owners/new',         description: 'Create a new owner', authRequired: false },
          { id: 'get-pets',      name: 'Get Pets',       type: 'exposed', method: 'GET',    endpoint: '/owners/{id}/pets',   description: 'List pets for owner', authRequired: false },
          { id: 'post-pets',     name: 'Add Pet',        type: 'exposed', method: 'POST',   endpoint: '/owners/{id}/pets/new', description: 'Add a pet to owner', authRequired: false },
          { id: 'get-vets',      name: 'List Vets',      type: 'exposed', method: 'GET',    endpoint: '/vets',               description: 'List all vets', authRequired: false },
          { id: 'get-vets-json', name: 'Vets JSON',      type: 'exposed', method: 'GET',    endpoint: '/vets.json',          description: 'Vets as JSON', authRequired: false },
          { id: 'post-visits',   name: 'Add Visit',      type: 'exposed', method: 'POST',   endpoint: '/owners/{id}/pets/{petId}/visits/new', description: 'Schedule a vet visit', authRequired: false },
        ],
      },
    ],
  },
];
