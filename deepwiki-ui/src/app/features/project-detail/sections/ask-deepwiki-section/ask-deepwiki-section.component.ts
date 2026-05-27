import { Component, computed, inject, input, signal } from '@angular/core';
import { WikiService } from '../../../../core/services/wiki.service';
import { Project, Message } from '../../../../core/models';

@Component({
  selector: 'dw-ask-deepwiki-section',
  standalone: true,
  template: `
    <div class="max-w-2xl space-y-4">
      <div>
        <h2 class="text-lg font-semibold">Ask DeepWiki</h2>
        <p class="text-sm text-muted-foreground mt-1">
          Ask anything about {{ project().name }} — answers grounded in the knowledge graph.
        </p>
      </div>

      <!-- Suggested questions -->
      <div class="flex flex-wrap gap-2">
        @for (q of suggestedQuestions(); track q) {
          <button (click)="ask(q)"
            class="text-xs px-3 py-1.5 rounded-full border hover:bg-accent transition-colors">
            {{ q }}
          </button>
        }
      </div>

      <!-- Messages -->
      <div class="space-y-3 min-h-[120px]">
        @for (msg of messages(); track $index) {
          <div [class]="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div [class]="msg.role === 'user'
              ? 'max-w-md bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2 text-sm'
              : 'max-w-md bg-muted rounded-2xl rounded-tl-sm px-4 py-2 text-sm'">
              {{ msg.content }}
            </div>
          </div>
        }
        @if (loading()) {
          <div class="flex justify-start">
            <div class="bg-muted rounded-2xl rounded-tl-sm px-4 py-2 text-sm text-muted-foreground animate-pulse">
              Thinking...
            </div>
          </div>
        }
      </div>

      <!-- Input -->
      <div class="flex gap-2">
        <input #qi type="text" placeholder="Ask about this project..."
          (keyup.enter)="ask(qi.value); qi.value=''"
          class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
        <button (click)="ask(qi.value); qi.value=''"
          [disabled]="loading()"
          class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
          Ask
        </button>
      </div>
      @if (error()) {
        <p class="text-destructive text-sm">{{ error() }}</p>
      }
    </div>
  `,
})
export class AskDeepwikiSectionComponent {
  project = input.required<Project>();

  private wikiService = inject(WikiService);

  messages = signal<Message[]>([]);
  loading  = signal(false);
  error    = signal<string | null>(null);

  suggestedQuestions = computed(() => {
    const p = this.project();
    return [
      `What are the main modules in ${p.name}?`,
      `How does ${p.name} handle data persistence?`,
      `Which classes handle REST endpoints in ${p.name}?`,
    ];
  });

  ask(question: string) {
    if (!question.trim() || this.loading()) return;
    this.messages.update(m => [...m, { role: 'user', content: question }]);
    this.loading.set(true);
    this.error.set(null);

    this.wikiService.ask({
      question,
      repo_id: this.project().id,
    }).subscribe({
      next: res => {
        this.messages.update(m => [...m, { role: 'assistant', content: res.answer }]);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('API not reachable. Is the backend running on port 8000?');
        this.loading.set(false);
      },
    });
  }
}
