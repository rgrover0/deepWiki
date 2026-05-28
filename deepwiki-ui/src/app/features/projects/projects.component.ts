import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { ProjectService } from '../../core/services/project.service';
import { Suite } from '../../core/models';
import { BadgeComponent } from '../../shared/components/badge/badge.component';
import { SuiteGroupComponent } from './components/suite-group/suite-group.component';

@Component({
  selector: 'dw-projects',
  standalone: true,
  imports: [BadgeComponent, SuiteGroupComponent],
  template: `
    <div class="container mx-auto px-4 py-10 space-y-8">

      <!-- Hero -->
      <div class="space-y-2">
        <h1 class="text-4xl font-bold tracking-tight">Project Suite</h1>
        <p class="text-muted-foreground text-lg">
          @if (loading()) {
            Loading projects...
          } @else {
            {{ totalProjects() }} project{{ totalProjects() !== 1 ? 's' : '' }}
            across {{ suites().length }} application suite{{ suites().length !== 1 ? 's' : '' }}
          }
        </p>
      </div>

      <!-- Suite filter tabs -->
      @if (!loading() && suites().length > 1) {
        <div class="flex gap-2 flex-wrap border-b pb-3">
          <button
            (click)="activeSuite.set(null)"
            [class]="filterTabClass(activeSuite() === null)">
            All Suites
          </button>
          @for (suite of suites(); track suite.id) {
            <button
              (click)="activeSuite.set(suite.id)"
              [class]="filterTabClass(activeSuite() === suite.id)">
              <span class="w-2 h-2 rounded-full inline-block mr-1.5" [style.background]="suite.color"></span>
              {{ suite.name }}
            </button>
          }
        </div>
      }

      <!-- Loading skeleton -->
      @if (loading()) {
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          @for (_ of skeletons; track $index) {
            <div class="rounded-[0.625rem] border p-5 space-y-3 animate-pulse">
              <div class="h-5 w-2/3 rounded bg-muted"></div>
              <div class="h-3 w-full rounded bg-muted"></div>
              <div class="h-3 w-4/5 rounded bg-muted"></div>
              <div class="flex gap-2 mt-2">
                <div class="h-5 w-14 rounded bg-muted"></div>
                <div class="h-5 w-14 rounded bg-muted"></div>
              </div>
            </div>
          }
        </div>
      }

      <!-- Suite groups -->
      @if (!loading()) {
        @for (suite of visibleSuites(); track suite.id) {
          <dw-suite-group [suite]="suite" />
        }

        @if (visibleSuites().length === 0) {
          <div class="text-center py-20 text-muted-foreground">
            <p class="text-lg">No projects found.</p>
            <p class="text-sm mt-1">Start the API and run the ingestion pipeline.</p>
          </div>
        }
      }
    </div>
  `,
})
export class ProjectsComponent implements OnInit {
  private projectService = inject(ProjectService);
  private title          = inject(Title);

  suites      = signal<Suite[]>([]);
  activeSuite = signal<string | null>(null);
  loading     = signal(true);
  skeletons   = new Array(6);

  totalProjects = computed(() => this.suites().reduce((sum, s) => sum + s.projects.length, 0));

  visibleSuites = computed(() => {
    const active = this.activeSuite();
    return active ? this.suites().filter(s => s.id === active) : this.suites();
  });

  filterTabClass(active: boolean) {
    const base = 'px-4 py-1.5 rounded-full text-sm font-medium transition-colors';
    return active
      ? `${base} bg-primary text-primary-foreground`
      : `${base} text-muted-foreground hover:text-foreground hover:bg-muted`;
  }

  ngOnInit() {
    this.title.setTitle('DeepWiki — Projects');
    this.projectService.getSuites().subscribe(s => {
      this.suites.set(s);
      this.loading.set(false);
    });
  }
}
