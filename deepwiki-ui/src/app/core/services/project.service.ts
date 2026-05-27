import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Suite } from '../models';
import { MOCK_SUITES } from './mock-data';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private http   = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  getClasses(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/classes`);
  }

  getStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }

  getSuites(): Observable<Suite[]> {
    // Mock data until backend /suite endpoint is wired in Iteration 17 bootstrap
    // Phase 2: return this.http.get<Suite[]>(`${this.apiUrl}/suite`);
    return of(MOCK_SUITES);
  }

  getArchitecture(): Observable<{ diagram: string }> {
    return this.http.get<{ diagram: string }>(`${this.apiUrl}/architecture`);
  }
}
