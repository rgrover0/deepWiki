import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BadgeComponent } from '../../../../shared/components/badge/badge.component';
import {
  CardComponent, CardHeaderComponent, CardTitleComponent,
  CardDescriptionComponent, CardContentComponent,
} from '../../../../shared/components/card/card.component';
import { Project } from '../../../../core/models';

@Component({
  selector: 'dw-project-card',
  standalone: true,
  imports: [
    RouterLink, BadgeComponent,
    CardComponent, CardHeaderComponent, CardTitleComponent,
    CardDescriptionComponent, CardContentComponent,
  ],
  template: `
    <a [routerLink]="['/project', project().id]" class="block group">
      <dw-card class="group-hover:shadow-md transition-shadow h-full">
        <dw-card-header>
          <div class="flex items-start justify-between">
            <dw-card-title>{{ project().name }}</dw-card-title>
            @if (project().status) {
              <dw-badge [variant]="project().status === 'active' ? 'default' : 'secondary'">
                {{ project().status }}
              </dw-badge>
            }
          </div>
          <dw-card-description>{{ project().description }}</dw-card-description>
        </dw-card-header>
        <dw-card-content>
          <div class="flex flex-wrap gap-1.5">
            @for (tech of project().techStack.slice(0, 4); track tech) {
              <span class="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{{ tech }}</span>
            }
            @if (project().techStack.length > 4) {
              <span class="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                +{{ project().techStack.length - 4 }}
              </span>
            }
          </div>
          <div class="mt-3 flex gap-4 text-xs text-muted-foreground">
            <span>{{ project().modules.length }} modules</span>
            <span>{{ project().apis.length }} endpoints</span>
          </div>
        </dw-card-content>
      </dw-card>
    </a>
  `,
})
export class ProjectCardComponent {
  project = input.required<Project>();
}
