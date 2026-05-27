import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AskRequest, AskResponse, SearchResult, FlowTrace, PlanResponse } from '../models';

@Injectable({ providedIn: 'root' })
export class WikiService {
  private http   = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  ask(req: AskRequest): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${this.apiUrl}/ask`, req);
  }

  search(query: string, topK = 5, unitType?: string): Observable<{ results: SearchResult[]; count: number }> {
    return this.http.post<{ results: SearchResult[]; count: number }>(
      `${this.apiUrl}/search`,
      { query, top_k: topK, unit_type: unitType ?? null }
    );
  }

  getFlow(
    entryPoint: string,
    beRepoId  = 'spring-petclinic',
    feRepoId  = 'angular-petclinic',
    maxHops   = 8,
  ): Observable<FlowTrace> {
    return this.http.post<FlowTrace>(`${this.apiUrl}/flow`, {
      entry_point: entryPoint,
      fe_repo_id:  feRepoId,
      be_repo_id:  beRepoId,
      max_hops:    maxHops,
    });
  }

  generatePlan(requirement: string, repoId: string): Observable<PlanResponse> {
    return this.http.post<PlanResponse>(`${this.apiUrl}/plan`, {
      requirement,
      repo_id: repoId,
    });
  }

  compare(query: string, topK = 5, mode = 'groq'): Observable<any> {
    return this.http.post(`${this.apiUrl}/compare`, { query, top_k: topK, mode });
  }

  getContracts(repoId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/contracts?repo_id=${repoId}`);
  }
}
