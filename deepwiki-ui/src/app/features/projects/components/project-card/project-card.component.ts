import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Project } from '../../../../core/models';

@Component({
  selector: 'dw-project-card',
  standalone: true,
  imports: [RouterLink, LucideAngularModule],
  template: `
    <a [routerLink]="['/project', project().id]" class="block group">
      <div class="h-full rounded-xl border bg-card p-6 hover:shadow-lg transition-all hover:border-primary/50 group-hover:shadow-md">
        <div class="mb-2">
          <div class="flex items-start justify-between">
            <lucide-icon name="layers" class="h-8 w-8 text-primary mb-2"></lucide-icon>
            <div class="flex items-center gap-1">
              @if (project().status) {
                <span class="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">
                  Docs
                </span>
              }
              <lucide-icon name="arrow-right"
                class="h-5 w-5 text-muted-foreground group-hover:text-accent transition-colors">
              </lucide-icon>
            </div>
          </div>
          <h3 class="font-semibold group-hover:text-primary transition-colors">{{ project().name }}</h3>
          <p class="text-sm text-muted-foreground mt-1">{{ project().description }}</p>
        </div>

        <div class="space-y-3 mt-4">
          <div>
            <p class="text-xs text-muted-foreground mb-2">Tech Stack</p>
            <div class="flex flex-wrap gap-1">
              @for (tech of project().techStack.slice(0, 3); track tech) {
                <span class="text-xs px-2 py-0.5 rounded border text-muted-foreground">{{ tech }}</span>
              }
              @if (project().techStack.length > 3) {
                <span class="text-xs px-2 py-0.5 rounded border text-muted-foreground">
                  +{{ project().techStack.length - 3 }}
                </span>
              }
            </div>
          </div>
          <div>
            <p class="text-xs text-muted-foreground mb-1">Modules</p>
            <p class="text-sm">{{ project().modules.length }} modules</p>
          </div>
        </div>
      </div>
    </a>
  `,
})
export class ProjectCardComponent {
  project = input.required<Project>();
}
