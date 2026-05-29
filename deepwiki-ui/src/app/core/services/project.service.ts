import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Suite, Project } from '../models';
import { MOCK_SUITES } from './mock-data';

const SUITE_COLORS = ['#2878CC', '#7C3AED', '#059669', '#DC2626', '#D97706', '#0891B2'];

interface ApiRepo  { id: string; name: string; language: string; }
interface ApiSuite { id: string; name: string; description: string; repos: ApiRepo[]; repo_count: number; }

export interface AllRepoRow {
  id: string; name: string; description: string; language: string;
  repository_url: string; confluence_link: string;
  status: string; tech_stack: string[];
  suite_id: string; suite_name: string;
  is_dummy: boolean;
}

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
    return this.http.get<{ suites: ApiSuite[] }>(`${this.apiUrl}/suite`).pipe(
      map(res => res.suites.map((s, i) => ({
        id:          s.id,
        name:        s.name,
        description: s.description,
        color:       SUITE_COLORS[i % SUITE_COLORS.length],
        projects:    s.repos.map(r => this._repoToProject(r, s.id)),
      }))),
      catchError(() => of(MOCK_SUITES)),
    );
  }

  createProject(body: {
    name: string; description: string; story: string; suite_id: string;
    tech_stack: string[]; repository_url: string; confluence_link: string;
    architecture_diagram: string; language: string; status: string;
  }): Observable<any> {
    return this.http.post(`${this.apiUrl}/project`, body);
  }

  updateProject(id: string, body: Partial<{
    name: string; description: string; story: string; suite_id: string;
    tech_stack: string[]; repository_url: string; confluence_link: string;
    architecture_diagram: string; language: string; status: string;
  }>): Observable<any> {
    return this.http.patch(`${this.apiUrl}/project/${id}`, body);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/project/${id}`);
  }

  createSuite(body: { name: string; description: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/project/suite`, body);
  }

  /** Returns ALL Repository nodes — including those without a suite link. */
  getAllRepos(): Observable<AllRepoRow[]> {
    return this.http.get<{ repos: AllRepoRow[] }>(`${this.apiUrl}/project/all`).pipe(
      map(res => res.repos),
      catchError(() => of([])),
    );
  }

  getArchitecture(): Observable<{ diagram: string }> {
    return this.http.get<{ diagram: string }>(`${this.apiUrl}/architecture`);
  }

  private _repoToProject(r: ApiRepo, suiteId: string): Project {
    return {
      id:          r.id,
      name:        r.name,
      suite:       suiteId,
      techStack:   r.language ? [r.language] : [],
      description: '',
      modules:     [],
      relations:   [],
      apis:        [],
      status:      'active',
    };
  }
}
