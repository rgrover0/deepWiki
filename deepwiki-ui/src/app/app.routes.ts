import { Routes } from '@angular/router';
import { AppShellComponent } from './layout/app-shell/app-shell.component';

export const routes: Routes = [
  {
    path: '',
    component: AppShellComponent,
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/projects/projects.component').then(m => m.ProjectsComponent),
      },
      {
        path: 'project/:id',
        loadComponent: () =>
          import('./features/project-detail/project-detail.component').then(m => m.ProjectDetailComponent),
      },
      {
        path: 'search',
        loadComponent: () =>
          import('./features/search/search.component').then(m => m.SearchComponent),
      },
    ],
  },
  {
    // Full-screen dark mode — no AppShell header/footer
    path: 'graph',
    loadComponent: () =>
      import('./features/graph/graph.component').then(m => m.GraphComponent),
  },
  { path: '**', redirectTo: '' },
];
