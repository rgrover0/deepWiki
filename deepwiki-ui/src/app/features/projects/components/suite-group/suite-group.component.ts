import { Component, input } from '@angular/core';
import { BadgeComponent } from '../../../../shared/components/badge/badge.component';
import { ProjectCardComponent } from '../project-card/project-card.component';
import { Suite } from '../../../../core/models';

@Component({
  selector: 'dw-suite-group',
  standalone: true,
  imports: [BadgeComponent, ProjectCardComponent],
  template: `
    <section>
      <div class="flex items-center gap-3 mb-4">
        <div class="w-3 h-3 rounded-full" [style.background]="suite().color"></div>
        <h2 class="text-xl font-semibold">{{ suite().name }}</h2>
        <dw-badge variant="secondary">{{ suite().projects.length }}</dw-badge>
      </div>
      <p class="text-muted-foreground text-sm mb-4">{{ suite().description }}</p>
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        @for (project of suite().projects; track project.id) {
          <dw-project-card [project]="project" />
        }
      </div>
    </section>
  `,
})
export class SuiteGroupComponent {
  suite = input.required<Suite>();
}
