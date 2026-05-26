import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Pet {
  id: number;
  name: string;
  birthDate: string;
  type: { id: number; name: string };
}

export interface Owner {
  id: number;
  firstName: string;
  lastName: string;
  address: string;
  city: string;
  telephone: string;
  pets: Pet[];
}

@Injectable({ providedIn: 'root' })
export class PetService {
  private readonly BASE = '/api';

  constructor(private http: HttpClient) {}

  getPets(): Observable<Pet[]> {
    return this.http.get<Pet[]>(`${this.BASE}/pets`);
  }

  getPetById(id: number): Observable<Pet> {
    return this.http.get<Pet>(`${this.BASE}/pets/${id}`);
  }

  createPet(pet: Pet): Observable<Pet> {
    return this.http.post<Pet>(`${this.BASE}/pets`, pet);
  }

  updatePet(id: number, pet: Pet): Observable<Pet> {
    return this.http.put<Pet>(`${this.BASE}/pets/${id}`, pet);
  }

  deletePet(id: number): Observable<void> {
    return this.http.delete<void>(`${this.BASE}/pets/${id}`);
  }

  getOwners(): Observable<Owner[]> {
    return this.http.get<Owner[]>(`${this.BASE}/owners`);
  }

  getOwnerById(id: number): Observable<Owner> {
    return this.http.get<Owner>(`${this.BASE}/owners/${id}`);
  }

  searchOwners(lastName: string): Observable<Owner[]> {
    return this.http.get<Owner[]>(`${this.BASE}/owners?lastName=` + lastName);
  }

  createOwner(owner: Owner): Observable<Owner> {
    return this.http.post<Owner>(`${this.BASE}/owners`, owner);
  }
}
