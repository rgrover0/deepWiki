import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { Title } from '@angular/platform-browser';
import { ProjectService } from '../../core/services/project.service';
import { Project } from '../../core/models';
import { BadgeComponent } from '../../shared/components/badge/badge.component';
import { MethodColorPipe } from '../../shared/pipes/method-color.pipe';
import { WikiService } from '../../core/services/wiki.service';
import { Message } from '../../core/models';

@Component({
  selector: 'dw-project-detail',
  standalone: true,
  imports: [RouterLink, BadgeComponent, MethodColorPipe, DecimalPipe],
  template: `
    <div class="container mx-auto px-4 py-10">

      <!-- Back nav -->
      <a routerLink="/projects" class="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-6">
        &#8592; All Projects
      </a>

      <!-- Loading skeleton -->
      @if (loading()) {
        <div class="animate-pulse space-y-4">
          <div class="h-8 w-64 rounded bg-muted"></div>
          <div class="h-4 w-full rounded bg-muted"></div>
          <div class="flex gap-2">
            <div class="h-5 w-16 rounded bg-muted"></div>
            <div class="h-5 w-16 rounded bg-muted"></div>
          </div>
        </div>
      }

      @if (!loading() && project()) {
        <!-- Project header -->
        <div class="mb-8">
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-3xl font-bold">{{ project()!.name }}</h1>
            <dw-badge>{{ project()!.status ?? 'active' }}</dw-badge>
          </div>
          <p class="text-muted-foreground">{{ project()!.description }}</p>
          <div class="flex flex-wrap gap-2 mt-3">
            @for (tech of project()!.techStack; track tech) {
              <span class="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">{{ tech }}</span>
            }
          </div>
          <!-- Stats bar -->
          <div class="flex gap-6 mt-4 text-sm text-muted-foreground">
            <span><strong class="text-foreground">{{ project()!.modules.length }}</strong> modules</span>
            <span><strong class="text-foreground">{{ project()!.apis.length }}</strong> endpoints</span>
          </div>
        </div>

        <!-- Tabs -->
        <div class="border-b mb-6">
          <nav class="flex gap-1">
            @for (tab of tabs; track tab.id) {
              <button
                (click)="activeTab.set(tab.id)"
                [class]="tabClass(tab.id)">
                {{ tab.label }}
              </button>
            }
          </nav>
        </div>

        <!-- Tab content -->
        @switch (activeTab()) {

          @case ('modules') {
            <div class="grid gap-4 md:grid-cols-2">
              @for (mod of project()!.modules; track mod.id) {
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
            </div>
          }

          @case ('apis') {
            <div class="space-y-3">
              <h2 class="text-lg font-semibold">Exposed Endpoints
                <span class="ml-2 text-sm font-normal text-muted-foreground">({{ project()!.apis.length }})</span>
              </h2>
              @for (api of project()!.apis; track api.id) {
                <div class="flex items-center gap-3 rounded-[0.625rem] border p-3">
                  <span class="text-xs font-bold px-2 py-1 rounded min-w-[52px] text-center {{ api.method | methodColor }}">
                    {{ api.method }}
                  </span>
                  <code class="text-sm font-mono flex-1 truncate">{{ api.endpoint }}</code>
                  <span class="text-xs text-muted-foreground hidden sm:block">{{ api.description }}</span>
                </div>
              }
            </div>
          }

          @case ('ask') {
            <div class="max-w-2xl space-y-4">
              <div>
                <h2 class="text-lg font-semibold">Ask DeepWiki</h2>
                <p class="text-sm text-muted-foreground mt-1">
                  Ask anything about {{ project()!.name }} — answers grounded in the knowledge graph.
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
                @if (askLoading()) {
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
                  [disabled]="askLoading()"
                  class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
                  Ask
                </button>
              </div>
              @if (askError()) {
                <p class="text-destructive text-sm">{{ askError() }}</p>
              }
            </div>
          }

          @case ('plan') {
            <div class="max-w-2xl space-y-4">
              <div>
                <h2 class="text-lg font-semibold">Plan & Tests</h2>
                <p class="text-sm text-muted-foreground mt-1">Describe a requirement to generate an implementation plan.</p>
              </div>
              <div class="flex gap-2">
                <input #ri type="text" placeholder="Add phone validation to owner creation..."
                  (keyup.enter)="generatePlan(ri.value)"
                  class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                <button (click)="generatePlan(ri.value)"
                  [disabled]="planLoading()"
                  class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
                  Generate
                </button>
              </div>
              @if (planLoading()) {
                <div class="space-y-2 animate-pulse">
                  @for (_ of [1,2,3,4]; track $index) {
                    <div class="h-3 rounded bg-muted" [style.width]="$index % 2 === 0 ? '100%' : '80%'"></div>
                  }
                </div>
              }
              @if (planResult()) {
                <div class="rounded-[0.625rem] border p-4">
                  <pre class="whitespace-pre-wrap text-sm font-mono">{{ planResult() }}</pre>
                </div>
              }
            </div>
          }

          @case ('compare') {
            <div class="max-w-2xl space-y-4">
              <div>
                <h2 class="text-lg font-semibold">Live Token Comparison</h2>
                <p class="text-sm text-muted-foreground mt-1">
                  Compare DeepWiki token usage vs raw source retrieval on the same query.
                </p>
              </div>
              <div class="flex gap-2">
                <input #cq type="text" placeholder="How does owner creation work?"
                  (keyup.enter)="runComparison(cq.value)"
                  class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                <button (click)="runComparison(cq.value)"
                  [disabled]="compareLoading()"
                  class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium">
                  Compare
                </button>
              </div>
              @if (compareLoading()) {
                <div class="rounded-[0.625rem] border p-4 text-sm text-muted-foreground animate-pulse">Running comparison...</div>
              }
              @if (compareError()) {
                <div class="rounded-[0.625rem] border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                  {{ compareError() }}
                </div>
              }
              @if (compareData()) {
                <div class="grid grid-cols-2 gap-4">
                  <div class="rounded-[0.625rem] border p-4">
                    <h3 class="font-semibold text-sm mb-2">With DeepWiki</h3>
                    <p class="text-2xl font-bold text-green-600">{{ compareData()!.wiki.total_tokens ?? 0 | number }}</p>
                    <p class="text-xs text-muted-foreground">tokens</p>
                    @if (compareData()!.wiki.answer) {
                      <p class="text-xs text-muted-foreground mt-3 mb-1">Answer</p>
                      <p class="text-sm">{{ compareData()!.wiki.answer }}</p>
                    }
                  </div>
                  <div class="rounded-[0.625rem] border p-4">
                    <h3 class="font-semibold text-sm mb-2">Without (Raw)</h3>
                    <p class="text-2xl font-bold text-destructive">{{ compareData()!.raw.total_tokens ?? 0 | number }}</p>
                    <p class="text-xs text-muted-foreground">tokens</p>
                    @if (compareData()!.raw.answer) {
                      <p class="text-xs text-muted-foreground mt-3 mb-1">Answer</p>
                      <p class="text-sm">{{ compareData()!.raw.answer }}</p>
                    }
                  </div>
                  @if (compareData()!.wiki.total_tokens && compareData()!.raw.total_tokens) {
                    <div class="col-span-2 rounded-[0.625rem] border p-4 bg-green-50">
                      <p class="text-sm font-medium text-green-800">
                        {{ savings() }}% fewer tokens with DeepWiki
                      </p>
                    </div>
                  }
                </div>
              }
            </div>
          }
        }
      }

      @if (!loading() && !project()) {
        <div class="text-center py-20 text-muted-foreground">
          <p class="text-lg">Project not found.</p>
          <a routerLink="/projects" class="text-sm text-primary underline">Back to projects</a>
        </div>
      }
    </div>
  `,
})
export class ProjectDetailComponent implements OnInit {
  private route          = inject(ActivatedRoute);
  private projectService = inject(ProjectService);
  private wikiService    = inject(WikiService);
  private titleService   = inject(Title);

  project     = signal<Project | null>(null);
  loading     = signal(true);
  activeTab   = signal('modules');
  messages    = signal<Message[]>([]);
  askLoading  = signal(false);
  askError    = signal<string | null>(null);
  planLoading = signal(false);
  planResult  = signal<string | null>(null);
  compareResult = signal<any>(null);
  compareLoading = signal(false);
  compareError = signal<string | null>(null);

  compareData = computed(() => {
    const result = this.compareResult();
    if (!result) return null;

    // API can return either { deepwiki, raw } or { wiki, raw }, and "all" mode nests under groq/claude.
    const payload = (result.groq && !result.deepwiki && !result.wiki) ? result.groq : result;
    const wiki = payload.wiki ?? payload.deepwiki;
    const raw = payload.raw;
    if (!wiki || !raw) return null;

    return { wiki, raw };
  });

  tabs = [
    { id: 'modules', label: 'Modules'        },
    { id: 'apis',    label: 'API Catalog'     },
    { id: 'ask',     label: 'Ask DeepWiki'    },
    { id: 'plan',    label: 'Plan & Tests'    },
    { id: 'compare', label: 'Live Comparison' },
  ];

  suggestedQuestions = computed(() => {
    const p = this.project();
    if (!p) return [];
    return [
      `What are the main modules in ${p.name}?`,
      `How does ${p.name} handle data persistence?`,
      `Which classes handle REST endpoints in ${p.name}?`,
    ];
  });

  savings = computed(() => {
    const r = this.compareData();
    if (!r?.wiki?.total_tokens || !r?.raw?.total_tokens) return 0;
    return Math.round((1 - r.wiki.total_tokens / r.raw.total_tokens) * 100);
  });

  tabClass(id: string) {
    const base = 'px-4 py-2 text-sm font-medium -mb-px border-b-2 transition-colors';
    return this.activeTab() === id
      ? `${base} border-primary text-primary`
      : `${base} border-transparent text-muted-foreground hover:text-foreground`;
  }

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    this.projectService.getSuites().subscribe(suites => {
      for (const s of suites) {
        const p = s.projects.find(pr => pr.id === id);
        if (p) {
          this.project.set(p);
          this.titleService.setTitle(`DeepWiki — ${p.name}`);
          this.loading.set(false);
          return;
        }
      }
      this.loading.set(false);
    });
  }

  ask(question: string) {
    if (!question.trim() || this.askLoading()) return;
    this.messages.update(m => [...m, { role: 'user', content: question }]);
    this.askLoading.set(true);
    this.askError.set(null);

    this.wikiService.ask({
      question,
      repo_id: this.project()?.id ?? 'spring-petclinic',
    }).subscribe({
      next: res => {
        this.messages.update(m => [...m, { role: 'assistant', content: res.answer }]);
        this.askLoading.set(false);
      },
      error: () => {
        this.askError.set('API not reachable. Is the backend running on port 8000?');
        this.askLoading.set(false);
      },
    });
  }

  generatePlan(req: string) {
    if (!req.trim()) return;
    this.planLoading.set(true);
    this.planResult.set(null);
    this.wikiService.generatePlan(req, this.project()?.id ?? 'spring-petclinic').subscribe({
      next: res => { this.planResult.set(res.plan); this.planLoading.set(false); },
      error: () => this.planLoading.set(false),
    });
  }

  runComparison(query: string) {
    if (!query.trim()) return;
    this.compareResult.set(null);
    this.compareError.set(null);
    this.compareLoading.set(true);
    this.wikiService.compare(query).subscribe({
      next: res => {
        this.compareResult.set(res);
        this.compareLoading.set(false);
      },
      error: () => {
        this.compareError.set('Comparison API is not reachable. Check backend /compare endpoint.');
        this.compareLoading.set(false);
      },
    });
  }
}
