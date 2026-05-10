# Architecture Diagram

classDiagram
    class PetClinicApplication["PetClinicApplication"]
    <<Class>> PetClinicApplication
    PetClinicApplication : +main() void
    class PetClinicRuntimeHints["PetClinicRuntimeHints"]
    <<Class>> PetClinicRuntimeHints
    PetClinicRuntimeHints : +registerHints() void
    class BaseEntity["BaseEntity"]
    <<Class>> BaseEntity
    BaseEntity : +Integer id
    BaseEntity : +isNew() boolean
    BaseEntity : +setId() void
    BaseEntity : +getId() Integer
    class NamedEntity["NamedEntity"]
    <<Class>> NamedEntity
    NamedEntity : +String name
    NamedEntity : +toString() String
    NamedEntity : +setName() void
    NamedEntity : +getName() String
    class Person["Person"]
    <<Class>> Person
    Person : +String lastName
    Person : +String firstName
    Person : +setLastName() void
    Person : +getLastName() String
    Person : +setFirstName() void
    Person : +getFirstName() String
    class Owner["Owner"]
    <<Entity>> Owner
    Owner : +List pets
    Owner : +String telephone
    Owner : +String city
    Owner : +String address
    Owner : +addVisit() void
    Owner : +toString() String
    Owner : +getPet() Pet
    Owner : +addPet() void
    class OwnerController["OwnerController"]
    <<Controller>> OwnerController
    OwnerController : +OwnerRepository owners
    OwnerController : +String VIEWS_OWNER_CREATE_OR_UPDATE_FORM
    OwnerController : +showOwner() ModelAndView
    OwnerController : +processUpdateOwnerForm() String
    OwnerController : +initUpdateOwnerForm() String
    OwnerController : +findPaginatedForOwnersLastName() Page
    class Pet["Pet"]
    <<Entity>> Pet
    Pet : +Set visits
    Pet : +PetType type
    Pet : +LocalDate birthDate
    Pet : +addVisit() void
    Pet : +getVisits() Collection
    Pet : +setType() void
    Pet : +getType() PetType
    class PetController["PetController"]
    <<Controller>> PetController
    PetController : +PetTypeRepository types
    PetController : +OwnerRepository owners
    PetController : +String VIEWS_PETS_CREATE_OR_UPDATE_FORM
    PetController : +updatePetDetails() void
    PetController : +processUpdateForm() String
    PetController : +initUpdateForm() String
    PetController : +processCreationForm() String
    class PetType["PetType"]
    <<Entity>> PetType
    class PetTypeFormatter["PetTypeFormatter"]
    <<Component>> PetTypeFormatter
    PetTypeFormatter : +PetTypeRepository types
    PetTypeFormatter : +parse() PetType
    PetTypeFormatter : +print() String
    class PetValidator["PetValidator"]
    <<Class>> PetValidator
    PetValidator : +String REQUIRED
    PetValidator : +supports() boolean
    PetValidator : +validate() void
    class Visit["Visit"]
    <<Entity>> Visit
    Visit : +String description
    Visit : +LocalDate date
    Visit : +setDescription() void
    Visit : +getDescription() String
    Visit : +setDate() void
    Visit : +getDate() LocalDate
    class VisitController["VisitController"]
    <<Controller>> VisitController
    VisitController : +OwnerRepository owners
    VisitController : +processNewVisitForm() String
    VisitController : +initNewVisitForm() String
    VisitController : +loadPetWithVisit() Visit
    VisitController : +setAllowedFields() void
    class CacheConfiguration["CacheConfiguration"]
    <<Config>> CacheConfiguration
    CacheConfiguration : +cacheConfiguration() javax_cache_configuration_Configuration
    CacheConfiguration : +petclinicCacheConfigurationCustomizer() JCacheManagerCustomizer
    class CrashController["CrashController"]
    <<Controller>> CrashController
    CrashController : +triggerException() String
    class WebConfiguration["WebConfiguration"]
    <<Config>> WebConfiguration
    WebConfiguration : +addInterceptors() void
    WebConfiguration : +localeChangeInterceptor() LocaleChangeInterceptor
    WebConfiguration : +localeResolver() LocaleResolver
    class WelcomeController["WelcomeController"]
    <<Controller>> WelcomeController
    WelcomeController : +welcome() String
    class Specialty["Specialty"]
    <<Entity>> Specialty
    class Vet["Vet"]
    <<Entity>> Vet
    Vet : +Set specialties
    Vet : +addSpecialty() void
    Vet : +getNrOfSpecialties() int
    Vet : +getSpecialties() List
    Vet : +getSpecialtiesInternal() Set
    class VetController["VetController"]
    <<Controller>> VetController
    VetController : +VetRepository vetRepository
    VetController : +showResourcesVetList() Vets
    VetController : +findPaginated() Page
    VetController : +addPaginationModel() String
    VetController : +showVetList() String
    class Vets["Vets"]
    <<Class>> Vets
    Vets : +List vets
    Vets : +getVetList() List
    Pet --> PetType