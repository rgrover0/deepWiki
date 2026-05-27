import { Component, input } from '@angular/core';
import { Project } from '../../../../core/models';

@Component({
  selector: 'dw-modules-section',
  standalone: true,
  template: `
    <div class="grid gap-4 md:grid-cols-2">
      @for (mod of project().modules; track mod.id) {
        <div class="rounded-[0.625rem] border p-5">
          <h3 class="font-semibold mb-1">{{ mod.name }}</h3>
          <p class="text-sm text-muted-foreground mb-3">{{ mod.description }}</p>
          <ul class="text-sm space-y-1">
            @for (f of mod.features; track f) {
              <li class="flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-primary inline-block"></span>{{ f }}
              </li>
            }
          </ul>
        </div>
      }
      @if (project().modules.length === 0) {
        <p class="text-muted-foreground text-sm col-span-2">No modules found for this project.</p>
      }
    </div>
  `,
})
export class ModulesSectionComponent {
  project = input.required<Project>();
}
