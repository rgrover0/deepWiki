import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval, switchMap, takeWhile, share } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface PipelineStep {
  label: string;
  status: 'pending' | 'running' | 'done' | 'skipped' | 'error' | 'cancelled';
  detail: string;
}

export interface JobStatus {
  repo_id: string;
  status: 'running' | 'done' | 'error';
  progress: number;
  current_step: string;
  steps: PipelineStep[];
  stats: { code_units?: number; contracts?: number };
  error?: string;
  logs?: string[];
}

export interface OnboardRequest {
  name: string;
  suite_id: string;
  repo_url?: string;
  confluence_link?: string;
  description?: string;
  story?: string;
  tech_stack?: string[];
  architecture_diagram?: string;
  status?: string;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http   = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  onboardRepo(body: OnboardRequest): Observable<{ repo_id: string; status: string }> {
    return this.http.post<{ repo_id: string; status: string }>(
      `${this.apiUrl}/admin/onboard-repo`, body
    );
  }

  getStatus(repoId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.apiUrl}/admin/status/${repoId}`);
  }

  pollStatus(repoId: string): Observable<JobStatus> {
    return interval(2000).pipe(
      switchMap(() => this.getStatus(repoId)),
      takeWhile(s => s.status === 'running', true),
      share(),
    );
  }

  reindex(repoId: string): Observable<{ repo_id: string; status: string }> {
    return this.http.post<{ repo_id: string; status: string }>(
      `${this.apiUrl}/admin/reindex/${repoId}`, {}
    );
  }
}
