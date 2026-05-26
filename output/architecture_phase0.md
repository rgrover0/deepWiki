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
    BaseEntity : +getId() Integer
    BaseEntity : +setId() void
    BaseEntity : +isNew() boolean
    class NamedEntity["NamedEntity"]
    <<Class>> NamedEntity
    NamedEntity : +String name
    NamedEntity : +getName() String
    NamedEntity : +setName() void
    NamedEntity : +toString() String
    class Person["Person"]
    <<Class>> Person
    Person : +String firstName
    Person : +String lastName
    Person : +getFirstName() String
    Person : +setFirstName() void
    Person : +getLastName() String
    Person : +setLastName() void
    class Owner["Owner"]
    <<Entity>> Owner
    Owner : +String address
    Owner : +String city
    Owner : +String telephone
    Owner : +List pets
    Owner : +getAddress() String
    Owner : +setAddress() void
    Owner : +getCity() String
    Owner : +setCity() void
    class OwnerController["OwnerController"]
    <<Controller>> OwnerController
    OwnerController : +String VIEWS_OWNER_CREATE_OR_UPDATE_FORM
    OwnerController : +OwnerRepository owners
    OwnerController : +setAllowedFields() void
    OwnerController : +findOwner() Owner
    OwnerController : +initCreationForm() String
    OwnerController : +processCreationForm() String
    class Pet["Pet"]
    <<Entity>> Pet
    Pet : +LocalDate birthDate
    Pet : +PetType type
    Pet : +Set visits
    Pet : +setBirthDate() void
    Pet : +getBirthDate() LocalDate
    Pet : +getType() PetType
    Pet : +setType() void
    class PetController["PetController"]
    <<Controller>> PetController
    PetController : +String VIEWS_PETS_CREATE_OR_UPDATE_FORM
    PetController : +OwnerRepository owners
    PetController : +PetTypeRepository types
    PetController : +populatePetTypes() Collection
    PetController : +findOwner() Owner
    PetController : +findPet() Pet
    PetController : +initOwnerBinder() void
    class PetType["PetType"]
    <<Entity>> PetType
    class PetTypeFormatter["PetTypeFormatter"]
    <<Component>> PetTypeFormatter
    PetTypeFormatter : +PetTypeRepository types
    PetTypeFormatter : +print() String
    PetTypeFormatter : +parse() PetType
    class PetValidator["PetValidator"]
    <<Class>> PetValidator
    PetValidator : +String REQUIRED
    PetValidator : +validate() void
    PetValidator : +supports() boolean
    class Visit["Visit"]
    <<Entity>> Visit
    Visit : +LocalDate date
    Visit : +String description
    Visit : +getDate() LocalDate
    Visit : +setDate() void
    Visit : +getDescription() String
    Visit : +setDescription() void
    class VisitController["VisitController"]
    <<Controller>> VisitController
    VisitController : +OwnerRepository owners
    VisitController : +setAllowedFields() void
    VisitController : +loadPetWithVisit() Visit
    VisitController : +initNewVisitForm() String
    VisitController : +processNewVisitForm() String
    class CacheConfiguration["CacheConfiguration"]
    <<Config>> CacheConfiguration
    CacheConfiguration : +petclinicCacheConfigurationCustomizer() JCacheManagerCustomizer
    CacheConfiguration : +cacheConfiguration() javax_cache_configuration_Configuration
    class CrashController["CrashController"]
    <<Controller>> CrashController
    CrashController : +triggerException() String
    class WebConfiguration["WebConfiguration"]
    <<Config>> WebConfiguration
    WebConfiguration : +localeResolver() LocaleResolver
    WebConfiguration : +localeChangeInterceptor() LocaleChangeInterceptor
    WebConfiguration : +addInterceptors() void
    class WelcomeController["WelcomeController"]
    <<Controller>> WelcomeController
    WelcomeController : +welcome() String
    class Specialty["Specialty"]
    <<Entity>> Specialty
    class Vet["Vet"]
    <<Entity>> Vet
    Vet : +Set specialties
    Vet : +getSpecialtiesInternal() Set
    Vet : +getSpecialties() List
    Vet : +getNrOfSpecialties() int
    Vet : +addSpecialty() void
    class VetController["VetController"]
    <<Controller>> VetController
    VetController : +VetRepository vetRepository
    VetController : +showVetList() String
    VetController : +addPaginationModel() String
    VetController : +findPaginated() Page
    VetController : +showResourcesVetList() Vets
    class Vets["Vets"]
    <<Class>> Vets
    Vets : +List vets
    Vets : +getVetList() List
    Pet --> PetType