import { Component, input } from '@angular/core';
import { Project } from '../../../../core/models';
import { ApiCardComponent } from './api-card/api-card.component';

@Component({
  selector: 'dw-api-catalog-section',
  standalone: true,
  imports: [ApiCardComponent],
  template: `
    <div class="space-y-3">
      <h2 class="text-lg font-semibold">
        Exposed Endpoints
        <span class="ml-2 text-sm font-normal text-muted-foreground">({{ project().apis.length }})</span>
      </h2>
      @for (api of project().apis; track api.id) {
        <dw-api-card [api]="api" />
      }
      @if (project().apis.length === 0) {
        <p class="text-muted-foreground text-sm">No API endpoints defined for this project.</p>
      }
    </div>
  `,
})
export class ApiCatalogSectionComponent {
  project = input.required<Project>();
}
