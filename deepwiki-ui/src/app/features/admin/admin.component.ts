import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { Project, Suite } from '../../core/models';
import { LucideAngularModule } from 'lucide-angular';
import { ProjectService } from '../../core/services/project.service';
import { AdminService, JobStatus, PipelineStep } from '../../core/services/admin.service';
import { AllRepoRow } from '../../core/services/project.service';
import { MOCK_SUITES } from '../../core/services/mock-data';
import { environment } from '../../../environments/environment';

interface ProjectForm {
  name: string;
  suite: string;
  newSuite: string;
  newSuiteDesc: string;
  techStack: string[];
  description: string;
  story: string;
  repositoryUrl: string;
  confluenceLink: string;
  architectureDiagram: string;
  diagramMode: 'upload' | 'url';
  diagramUrl: string;
  status: string;
}

interface Toast { type: 'success' | 'error'; message: string; }

const EMPTY_FORM = (): ProjectForm => ({
  name: '', suite: '', newSuite: '', newSuiteDesc: '', techStack: [],
  description: '', story: '', repositoryUrl: '', confluenceLink: '',
  architectureDiagram: '', diagramMode: 'upload', diagramUrl: '', status: 'active',
});

@Component({
  selector: 'dw-admin',
  standalone: true,
  imports: [LucideAngularModule],
  styles: [`
    .tab-trigger { @apply py-2 text-sm font-medium rounded-md transition-colors; }
    .tab-trigger.active { @apply bg-background text-foreground shadow-sm; }
    .tab-trigger:not(.active) { @apply text-muted-foreground hover:text-foreground; }
    .field-label { @apply block text-sm font-medium mb-1.5; }
    .field-input {
      @apply w-full h-10 rounded-lg border bg-muted/40 px-3 text-sm
             placeholder:text-muted-foreground focus:outline-none focus:ring-2
             focus:ring-primary focus:bg-background transition-colors;
    }
    .field-textarea {
      @apply w-full rounded-lg border bg-muted/40 px-3 py-2 text-sm
             placeholder:text-muted-foreground focus:outline-none focus:ring-2
             focus:ring-primary focus:bg-background transition-colors resize-none;
    }
    .section-title { @apply font-semibold text-base flex items-center gap-2 mb-4; }
    .btn-primary {
      @apply flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground
             text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
    }
    .btn-build {
      @apply flex items-center gap-2 h-11 px-6 rounded-lg text-sm font-semibold
             transition-colors disabled:opacity-50 disabled:cursor-not-allowed
             bg-penske-yellow text-gray-900 hover:bg-yellow-400;
    }
    .btn-outline {
      @apply flex items-center gap-2 h-10 px-4 rounded-lg border bg-background
             text-sm font-medium hover:bg-muted transition-colors disabled:opacity-50;
    }
    .btn-icon {
      @apply h-10 w-10 rounded-lg border bg-background flex items-center
             justify-center hover:bg-muted transition-colors flex-shrink-0;
    }
    .step-num {
      @apply h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center
             flex-shrink-0 text-xs font-bold text-primary;
    }
    .step-check {
      @apply h-6 w-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0;
    }
  `],
  template: `

    <!-- ══════════════ PASSWORD GATE ══════════════ -->
    @if (!authenticated()) {
      <div class="fixed inset-0 bg-background/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-card rounded-2xl border shadow-2xl p-8 max-w-sm w-full space-y-6">
          <div class="text-center space-y-2">
            <div class="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <lucide-icon name="lock" class="h-7 w-7 text-primary"></lucide-icon>
            </div>
            <h2 class="text-xl font-bold">Admin Access</h2>
            <p class="text-sm text-muted-foreground">Enter the admin password to continue</p>
          </div>

          <div class="space-y-3">
            <input
              #pwInput
              type="password"
              placeholder="Admin password"
              (keyup.enter)="checkPassword(pwInput.value)"
              [class]="'field-input ' + (authError() ? 'border-destructive ring-1 ring-destructive' : '')"
            />
            @if (authError()) {
              <p class="text-xs text-destructive">Incorrect password. Please try again.</p>
            }
            <button (click)="checkPassword(pwInput.value)" class="btn-primary w-full justify-center">
              <lucide-icon name="unlock" class="h-4 w-4"></lucide-icon>
              Unlock Admin Panel
            </button>
          </div>
        </div>
      </div>
    }

    <div class="space-y-6">

      <!-- Page header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-4xl font-bold tracking-tight flex items-center gap-3">
            <lucide-icon name="settings" class="h-8 w-8 text-primary"></lucide-icon>
            Admin Panel
          </h1>
          <p class="text-muted-foreground text-lg mt-2">
            Manage projects, repositories, and documentation
          </p>
        </div>
        <button (click)="authenticated.set(false)"
          class="h-9 px-3 rounded-lg border text-xs font-medium hover:bg-muted transition-colors
                 flex items-center gap-1.5 text-muted-foreground">
          <lucide-icon name="lock" class="h-3.5 w-3.5"></lucide-icon>
          Lock
        </button>
      </div>

      <!-- Toast -->
      @if (toast()) {
        <div [class]="toast()!.type === 'success'
          ? 'flex items-center gap-3 px-4 py-3 rounded-lg bg-green-50 border border-green-200 text-green-800 text-sm'
          : 'flex items-center gap-3 px-4 py-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm'">
          <lucide-icon [name]="toast()!.type === 'success' ? 'check-circle-2' : 'alert-circle'"
            class="h-4 w-4 flex-shrink-0"></lucide-icon>
          {{ toast()!.message }}
        </div>
      }

      <!-- Segmented tab bar -->
      <div class="grid grid-cols-3 gap-1 rounded-lg border bg-muted p-1">
        <button (click)="tab.set('add-project')"
          [class]="'tab-trigger ' + (tab() === 'add-project' ? 'active' : '')">
          Add Project
        </button>
        <button (click)="tab.set('manage-projects')"
          [class]="'tab-trigger ' + (tab() === 'manage-projects' ? 'active' : '')">
          Manage Projects
        </button>
        <button (click)="tab.set('settings')"
          [class]="'tab-trigger ' + (tab() === 'settings' ? 'active' : '')">
          Settings
        </button>
      </div>

      <!-- ══════════════ ADD PROJECT ══════════════ -->
      @if (tab() === 'add-project') {
        <div class="grid gap-6 md:grid-cols-3">

          <!-- Main form card -->
          <div class="md:col-span-2 rounded-xl border bg-card p-6 space-y-6">

            <div>
              <h2 class="font-semibold text-lg flex items-center gap-2">
                <lucide-icon name="plus" class="h-5 w-5"></lucide-icon>
                Add New Project / Repository
              </h2>
              <p class="text-sm text-muted-foreground mt-1">
                Fill in project details and click <strong>Build Now</strong> to ingest the codebase into DeepWiki
              </p>
            </div>

            <hr class="border-border" />

            <!-- §1 Basic Info -->
            <div>
              <h3 class="section-title">
                <lucide-icon name="file-text" class="h-4 w-4 text-primary"></lucide-icon>
                Basic Information
              </h3>

              <div class="grid gap-4 md:grid-cols-2 mb-4">
                <div>
                  <label class="field-label">Project Name *</label>
                  <input type="text" [value]="form.name" (input)="form.name = val($event)"
                    placeholder="e.g., Authentication Service" class="field-input" />
                </div>
                <div>
                  <label class="field-label">Application Suite *</label>
                  @if (!newSuiteMode()) {
                    <div class="flex gap-2">
                      <div class="relative flex-1">
                        <select [value]="form.suite" (change)="form.suite = val($event)"
                          class="field-input appearance-none pr-8 cursor-pointer">
                          <option value="">Select a suite</option>
                          @for (s of suites(); track s.id) {
                            <option [value]="s.id">{{ s.name }}</option>
                          }
                        </select>
                        <lucide-icon name="chevron-down"
                          class="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none">
                        </lucide-icon>
                      </div>
                      <button (click)="newSuiteMode.set(true)" class="btn-icon" title="Create new suite">
                        <lucide-icon name="plus" class="h-4 w-4"></lucide-icon>
                      </button>
                    </div>
                  } @else {
                    <div class="space-y-2">
                      <input type="text" [value]="form.newSuite" (input)="form.newSuite = val($event)"
                        placeholder="New suite name" class="field-input" />
                      <div class="flex gap-2">
                        <input type="text" [value]="form.newSuiteDesc" (input)="form.newSuiteDesc = val($event)"
                          placeholder="Suite description (optional)" class="field-input flex-1" />
                        <button (click)="newSuiteMode.set(false)"
                          class="h-10 px-3 rounded-lg border text-sm hover:bg-muted transition-colors flex-shrink-0">
                          Cancel
                        </button>
                      </div>
                    </div>
                  }
                </div>
              </div>

              <div class="mb-4">
                <label class="field-label">Status</label>
                <div class="relative w-48">
                  <select [value]="form.status" (change)="form.status = val($event)"
                    class="field-input appearance-none pr-8 cursor-pointer">
                    <option value="active">Active</option>
                    <option value="beta">Beta</option>
                    <option value="deprecated">Deprecated</option>
                  </select>
                  <lucide-icon name="chevron-down"
                    class="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none">
                  </lucide-icon>
                </div>
              </div>

              <div class="mb-4">
                <label class="field-label">Description *</label>
                <textarea [value]="form.description" (input)="form.description = val($event)"
                  placeholder="Brief description of the project..." rows="3" class="field-textarea"></textarea>
              </div>

              <div>
                <label class="field-label">Project Story &amp; History</label>
                <textarea [value]="form.story" (input)="form.story = val($event)"
                  placeholder="Tell the story behind this project..." rows="3" class="field-textarea"></textarea>
              </div>
            </div>

            <hr class="border-border" />

            <!-- §2 Tech Stack -->
            <div>
              <h3 class="section-title">
                <lucide-icon name="git-branch" class="h-4 w-4 text-primary"></lucide-icon>
                Tech Stack
              </h3>
              <div class="flex gap-2">
                <input type="text" #techInput (keydown.enter)="addTech(techInput)"
                  placeholder="e.g., Java 17, Spring Boot, PostgreSQL" class="field-input flex-1" />
                <button (click)="addTech(techInput)" class="btn-primary px-5">
                  <lucide-icon name="plus" class="h-4 w-4"></lucide-icon> Add
                </button>
              </div>
              @if (form.techStack.length > 0) {
                <div class="flex flex-wrap gap-2 mt-3">
                  @for (tech of form.techStack; track tech) {
                    <span class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full
                                 bg-secondary text-secondary-foreground font-medium">
                      {{ tech }}
                      <button (click)="removeTech(tech)" class="hover:text-destructive transition-colors ml-0.5">
                        <lucide-icon name="x" class="h-3 w-3"></lucide-icon>
                      </button>
                    </span>
                  }
                </div>
              }
            </div>

            <hr class="border-border" />

            <!-- §3 Repository & Docs -->
            <div>
              <h3 class="section-title">
                <lucide-icon name="link" class="h-4 w-4 text-primary"></lucide-icon>
                Repository &amp; Documentation
              </h3>
              <div class="mb-4">
                <label class="field-label">Repository URL</label>
                <input type="url" [value]="form.repositoryUrl" (input)="form.repositoryUrl = val($event)"
                  placeholder="https://github.com/org/repo" class="field-input" />
                <p class="text-xs text-muted-foreground mt-1">
                  Required for "Build Now" — DeepWiki will clone and index this repository
                </p>
              </div>
              <div>
                <label class="field-label">Confluence Page Link</label>
                <input type="url" [value]="form.confluenceLink" (input)="form.confluenceLink = val($event)"
                  placeholder="https://confluence.company.com/pages/..." class="field-input" />
              </div>
            </div>

            <hr class="border-border" />

            <!-- §4 Architecture Diagram -->
            <div>
              <h3 class="section-title">
                <lucide-icon name="image" class="h-4 w-4 text-primary"></lucide-icon>
                Architecture Diagram
              </h3>
              <div class="flex gap-1 rounded-lg border bg-muted p-1 mb-4 w-fit">
                <button (click)="form.diagramMode = 'upload'"
                  [class]="'px-3 py-1.5 text-xs font-medium rounded-md transition-colors '
                    + (form.diagramMode === 'upload' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground')">
                  Upload File
                </button>
                <button (click)="form.diagramMode = 'url'"
                  [class]="'px-3 py-1.5 text-xs font-medium rounded-md transition-colors '
                    + (form.diagramMode === 'url' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground')">
                  Enter URL
                </button>
              </div>
              @if (form.diagramMode === 'upload') {
                <div class="border-2 border-dashed border-border rounded-xl p-8 text-center">
                  @if (!selectedFile()) {
                    <div class="space-y-3">
                      <lucide-icon name="upload" class="h-10 w-10 text-muted-foreground mx-auto"></lucide-icon>
                      <p class="text-sm text-muted-foreground">PNG, JPG, SVG up to 10MB</p>
                      <label class="btn-outline cursor-pointer inline-flex mx-auto">
                        <lucide-icon name="upload" class="h-4 w-4"></lucide-icon> Select File
                        <input type="file" accept="image/*" class="hidden" (change)="onFile($event)" />
                      </label>
                    </div>
                  } @else {
                    <div class="space-y-3">
                      <div class="flex items-center justify-center gap-2 text-sm">
                        <lucide-icon name="image" class="h-4 w-4 text-green-600"></lucide-icon>
                        <span class="font-medium">{{ selectedFile()!.name }}</span>
                      </div>
                      @if (form.architectureDiagram) {
                        <img [src]="form.architectureDiagram" alt="Preview"
                          class="max-h-48 mx-auto rounded-lg border shadow-sm" />
                      }
                      <button (click)="removeFile()" class="btn-outline mx-auto inline-flex text-xs px-3 h-8">
                        <lucide-icon name="trash-2" class="h-3 w-3"></lucide-icon> Remove
                      </button>
                    </div>
                  }
                </div>
              } @else {
                <input type="url" [value]="form.diagramUrl" (input)="form.diagramUrl = val($event)"
                  placeholder="https://example.com/architecture.png" class="field-input" />
                @if (form.diagramUrl) {
                  <img [src]="form.diagramUrl" alt="Preview"
                    class="max-h-48 rounded-lg border shadow-sm mt-2" (error)="form.diagramUrl = ''" />
                }
              }
            </div>

            <hr class="border-border" />

            <!-- Submit row -->
            <div class="flex justify-end gap-3">
              <button (click)="resetForm()" class="btn-outline" [disabled]="saving()">Reset</button>
              <button (click)="submitMetaOnly()" class="btn-outline" [disabled]="saving()">
                <lucide-icon name="save" class="h-4 w-4"></lucide-icon>
                Save Metadata
              </button>
              <button (click)="buildNow()" class="btn-build" [disabled]="saving() || !!buildJob()">
                @if (saving()) {
                  <lucide-icon name="loader-circle" class="h-4 w-4 animate-spin"></lucide-icon> Starting…
                } @else {
                  <lucide-icon name="zap" class="h-4 w-4"></lucide-icon> Build Now
                }
              </button>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="space-y-4">

            <!-- ── Build progress panel ── -->
            @if (buildJob()) {
              <div class="rounded-xl border bg-card p-5 space-y-4">
                <!-- Header -->
                <div class="flex items-center justify-between">
                  <h3 class="font-semibold text-sm flex items-center gap-2">
                    @if (buildJob()!.status === 'done') {
                      <lucide-icon name="check-circle-2" class="h-4 w-4 text-green-600"></lucide-icon>
                      Build complete
                    } @else if (buildJob()!.status === 'error') {
                      <lucide-icon name="alert-circle" class="h-4 w-4 text-destructive"></lucide-icon>
                      Build failed
                    } @else {
                      <lucide-icon name="loader-circle" class="h-4 w-4 text-primary animate-spin"></lucide-icon>
                      Building {{ buildRepoId() }}…
                    }
                  </h3>
                  <span class="text-xs font-bold text-muted-foreground">{{ buildJob()!.progress }}%</span>
                </div>

                <!-- Progress bar -->
                <div class="h-2 rounded-full bg-muted overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                    [style.width]="buildJob()!.progress + '%'"
                    [class]="buildJob()!.status === 'error' ? 'bg-destructive'
                            : buildJob()!.status === 'done'  ? 'bg-green-500'
                            : 'bg-primary'">
                  </div>
                </div>

                <!-- Steps -->
                <ul class="space-y-2">
                  @for (step of buildJob()!.steps; track step.label) {
                    <li class="flex items-start gap-2.5 text-xs">
                      <span class="mt-0.5 flex-shrink-0">
                        @switch (step.status) {
                          @case ('done')      { <lucide-icon name="check-circle-2" class="h-3.5 w-3.5 text-green-600"></lucide-icon> }
                          @case ('skipped')   { <lucide-icon name="minus-circle"   class="h-3.5 w-3.5 text-muted-foreground"></lucide-icon> }
                          @case ('running')   { <lucide-icon name="loader-circle"  class="h-3.5 w-3.5 text-primary animate-spin"></lucide-icon> }
                          @case ('error')     { <lucide-icon name="alert-circle"   class="h-3.5 w-3.5 text-destructive"></lucide-icon> }
                          @case ('cancelled') { <lucide-icon name="ban"            class="h-3.5 w-3.5 text-muted-foreground/50"></lucide-icon> }
                          @default            { <lucide-icon name="clock"          class="h-3.5 w-3.5 text-muted-foreground/40"></lucide-icon> }
                        }
                      </span>
                      <div class="min-w-0">
                        <span [class]="stepLabelClass(step.status)">{{ step.label }}</span>
                        @if (step.detail) {
                          <span class="ml-1 text-muted-foreground">— {{ step.detail }}</span>
                        }
                      </div>
                    </li>
                  }
                </ul>

                <!-- Done stats -->
                @if (buildJob()!.status === 'done' && buildJob()!.stats) {
                  <div class="rounded-lg bg-green-50 border border-green-200 p-3 space-y-1">
                    <p class="text-xs font-semibold text-green-800">
                      <lucide-icon name="check-circle-2" class="h-3.5 w-3.5 inline mr-1"></lucide-icon>
                      Repo is live — Search and Ask DeepWiki are ready
                    </p>
                    <div class="flex gap-4 text-xs text-green-700 mt-1">
                      <span><strong>{{ buildJob()!.stats.code_units ?? 0 }}</strong> code units</span>
                      <span><strong>{{ buildJob()!.stats.contracts ?? 0 }}</strong> API contracts</span>
                    </div>
                  </div>
                  <button (click)="clearBuild()" class="btn-outline w-full justify-center text-xs h-8">
                    <lucide-icon name="plus" class="h-3.5 w-3.5"></lucide-icon> Add Another Project
                  </button>
                }

                <!-- Error -->
                @if (buildJob()!.status === 'error') {
                  <div class="rounded-lg bg-destructive/5 border border-destructive/20 p-3 text-xs text-destructive">
                    {{ buildJob()!.error }}
                  </div>
                  <button (click)="retryBuild()" class="btn-primary w-full justify-center text-xs h-9">
                    <lucide-icon name="refresh-cw" class="h-3.5 w-3.5"></lucide-icon> Retry Build
                  </button>
                }
              </div>
            }

            <!-- Guide card (hidden while build is running) -->
            @if (!buildJob()) {
              <div class="flex gap-3 rounded-xl border bg-muted/50 p-4">
                <lucide-icon name="info" class="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5"></lucide-icon>
                <p class="text-sm text-muted-foreground leading-relaxed">
                  <strong>Build Now</strong> clones the repository, parses all source files, builds the knowledge graph,
                  generates wiki summaries, extracts API contracts, and embeds everything into Qdrant — fully automated.
                </p>
              </div>
              <div class="rounded-xl border bg-card p-5 space-y-4">
                <h3 class="font-semibold text-sm">How Build Now works</h3>
                <ul class="space-y-3">
                  <li class="flex items-start gap-3">
                    <div class="step-num">1</div>
                    <p class="text-xs text-muted-foreground mt-0.5">Fill the form with project details and a GitHub/GitLab URL</p>
                  </li>
                  <li class="flex items-start gap-3">
                    <div class="step-num">2</div>
                    <p class="text-xs text-muted-foreground mt-0.5">Click <strong>Build Now</strong> — the pipeline starts instantly in the background</p>
                  </li>
                  <li class="flex items-start gap-3">
                    <div class="step-num">3</div>
                    <p class="text-xs text-muted-foreground mt-0.5">Watch live progress: 8 pipeline steps update every 2 seconds</p>
                  </li>
                  <li class="flex items-start gap-3">
                    <div class="step-check">
                      <lucide-icon name="check-circle-2" class="h-4 w-4 text-accent"></lucide-icon>
                    </div>
                    <p class="text-xs text-muted-foreground mt-0.5">Done — your project is searchable and ready for Ask DeepWiki</p>
                  </li>
                </ul>
              </div>
              <div class="rounded-xl border border-penske-yellow/40 bg-penske-yellow/5 p-5">
                <div class="flex gap-3">
                  <lucide-icon name="zap" class="h-5 w-5 text-penske-yellow flex-shrink-0 mt-0.5"></lucide-icon>
                  <div>
                    <p class="text-sm font-semibold">Save Metadata vs Build Now</p>
                    <p class="text-xs text-muted-foreground mt-1 leading-relaxed">
                      <strong>Save Metadata</strong> adds the project card without ingestion.
                      <strong>Build Now</strong> runs the full pipeline — use this when you have a repo URL to index.
                    </p>
                  </div>
                </div>
              </div>
            }
          </div>
        </div>
      }

      <!-- ══════════════ MANAGE PROJECTS ══════════════ -->
      @if (tab() === 'manage-projects') {
        <div class="rounded-xl border bg-card p-6 space-y-4">
          <div>
            <h2 class="font-semibold text-lg">Existing Projects</h2>
            <p class="text-sm text-muted-foreground mt-0.5">Manage and re-index existing projects</p>
          </div>
          @if (loadingProjects()) {
            <div class="space-y-2">
              @for (_ of [1,2,3]; track $index) {
                <div class="h-16 rounded-lg bg-muted animate-pulse"></div>
              }
            </div>
          } @else {
            <div class="space-y-2">
              @for (p of allProjects(); track p.id) {
                <div class="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/40 transition-colors">
                  <div class="min-w-0 flex-1">
                    <h4 class="font-semibold text-sm truncate">
                      {{ p.name }}
                      @if (p.isDummy) {
                        <span class="ml-2 inline-flex items-center rounded-full bg-amber-100 text-amber-700 px-2 py-0.5 text-[10px] font-semibold align-middle">
                          DUMMY
                        </span>
                      }
                    </h4>
                    <p class="text-xs text-muted-foreground mt-0.5">
                      @if (p.suite && p.suite !== 'unassigned') {
                        {{ p.suite }}
                      } @else {
                        <span class="italic text-muted-foreground/60">No Suite</span>
                      }
                      @if (p.status) {
                        &bull; <span [class]="statusClass(p.status)">{{ p.status }}</span>
                      }
                      @if (p.repositoryUrl) {
                        &bull; <span class="text-green-600">has repo</span>
                      }
                    </p>
                  </div>
                  <div class="flex gap-2 ml-3 flex-shrink-0">
                    <!-- Re-index button -->
                    @if (p.repositoryUrl) {
                      @if (reindexJobs()[p.id]) {
                        <div class="h-8 px-3 rounded-lg border bg-primary/5 flex items-center gap-1.5 text-xs font-medium text-primary">
                          <lucide-icon name="loader-circle" class="h-3.5 w-3.5 animate-spin"></lucide-icon>
                          @if (reindexJobs()[p.id]!.status === 'done') {
                            Done
                          } @else if (reindexJobs()[p.id]!.status === 'error') {
                            Error
                          } @else {
                            {{ reindexJobs()[p.id]!.progress }}%
                          }
                        </div>
                      } @else {
                        <button (click)="reindex(p)"
                          class="h-8 px-3 rounded-lg border text-xs font-medium hover:bg-muted transition-colors flex items-center gap-1.5">
                          <lucide-icon name="refresh-cw" class="h-3.5 w-3.5"></lucide-icon>
                          Re-index
                        </button>
                      }
                    }
                    <button (click)="openEdit(p)"
                      class="h-8 px-3 rounded-lg border text-xs font-medium hover:bg-muted transition-colors flex items-center gap-1.5">
                      <lucide-icon name="pencil" class="h-3.5 w-3.5"></lucide-icon>
                      {{ p.isDummy ? 'Fix Dummy' : 'Edit' }}
                    </button>
                    <button (click)="askDelete(p)"
                      class="h-8 px-3 rounded-lg border border-destructive/30 bg-destructive/5
                             flex items-center gap-1.5 hover:bg-destructive/15 transition-colors">
                      <lucide-icon name="trash-2" class="h-3.5 w-3.5 text-destructive"></lucide-icon>
                      <span class="text-xs font-medium text-destructive">Delete</span>
                    </button>
                  </div>
                </div>
              }
              @if (allProjects().length === 0) {
                <p class="text-center py-10 text-sm text-muted-foreground">No projects found.</p>
              }
            </div>
          }
        </div>

        <!-- Reindex progress panel -->
        @for (entry of reindexJobEntries(); track entry.repoId) {
          @if (entry.job.status !== 'done') {
            <div class="rounded-xl border bg-card p-5 space-y-3">
              <div class="flex items-center justify-between">
                <h3 class="font-semibold text-sm flex items-center gap-2">
                  <lucide-icon name="refresh-cw" class="h-4 w-4 text-primary animate-spin"></lucide-icon>
                  Re-indexing {{ entry.repoId }}…
                </h3>
                <span class="text-xs font-bold text-muted-foreground">{{ entry.job.progress }}%</span>
              </div>
              <div class="h-1.5 rounded-full bg-muted overflow-hidden">
                <div class="h-full rounded-full bg-primary transition-all duration-500"
                  [style.width]="entry.job.progress + '%'"></div>
              </div>
              <p class="text-xs text-muted-foreground">{{ entry.job.current_step }}</p>
            </div>
          }
        }

        <!-- Delete confirm dialog -->
        @if (deleteTarget()) {
          <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
               (click)="deleteTarget.set(null)">
            <div class="bg-background rounded-xl border shadow-xl p-6 max-w-sm w-full space-y-4"
                 (click)="$event.stopPropagation()">
              <h3 class="font-semibold text-lg">Delete Project</h3>
              <p class="text-sm text-muted-foreground">
                Are you sure you want to delete
                <span class="font-medium text-foreground">"{{ deleteTarget()!.name }}"</span>?
                This action cannot be undone.
              </p>
              <div class="flex justify-end gap-3 pt-1">
                <button (click)="deleteTarget.set(null)" class="btn-outline">Cancel</button>
                <button (click)="doDelete()" [disabled]="saving()"
                  class="h-10 px-4 rounded-lg bg-destructive text-destructive-foreground text-sm font-medium
                         hover:bg-destructive/90 transition-colors disabled:opacity-50">
                  @if (saving()) { Deleting... } @else { Delete }
                </button>
              </div>
            </div>
          </div>
        }

        <!-- Edit modal -->
        @if (editTarget()) {
          <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
               (click)="editTarget.set(null)">
            <div class="bg-background rounded-xl border shadow-xl p-6 max-w-lg w-full space-y-4 max-h-[90vh] overflow-y-auto"
                 (click)="$event.stopPropagation()">
              <h3 class="font-semibold text-lg flex items-center gap-2">
                <lucide-icon name="pencil" class="h-5 w-5"></lucide-icon> Edit Project
              </h3>
              <div class="space-y-3">
                <div>
                  <label class="field-label">Project Name *</label>
                  <input type="text" [value]="editForm.name" (input)="editForm.name = val($event)" class="field-input" />
                </div>
                <div>
                  <label class="field-label">Suite</label>
                  <div class="relative">
                    <select [value]="editForm.suite" (change)="editForm.suite = val($event)"
                      class="field-input appearance-none pr-8 cursor-pointer">
                      @for (s of suites(); track s.id) {
                        <option [value]="s.id">{{ s.name }}</option>
                      }
                    </select>
                    <lucide-icon name="chevron-down"
                      class="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none">
                    </lucide-icon>
                  </div>
                </div>
                <div>
                  <label class="field-label">Status</label>
                  <div class="relative">
                    <select [value]="editForm.status" (change)="editForm.status = val($event)"
                      class="field-input appearance-none pr-8 cursor-pointer">
                      <option value="active">Active</option>
                      <option value="beta">Beta</option>
                      <option value="deprecated">Deprecated</option>
                    </select>
                    <lucide-icon name="chevron-down"
                      class="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none">
                    </lucide-icon>
                  </div>
                </div>
                <div>
                  <label class="field-label">Description</label>
                  <textarea [value]="editForm.description" (input)="editForm.description = val($event)"
                    rows="3" class="field-textarea"></textarea>
                </div>
                <div>
                  <label class="field-label">Repository URL</label>
                  <input type="url" [value]="editForm.repositoryUrl" (input)="editForm.repositoryUrl = val($event)"
                    placeholder="https://github.com/org/repo" class="field-input" />
                </div>
                <div>
                  <label class="field-label">Confluence Link</label>
                  <input type="url" [value]="editForm.confluenceLink" (input)="editForm.confluenceLink = val($event)"
                    placeholder="https://confluence.company.com/..." class="field-input" />
                </div>
                <div>
                  <label class="field-label">Architecture Diagram URL</label>
                  <input type="url" [value]="editForm.diagramUrl" (input)="editForm.diagramUrl = val($event)"
                    placeholder="https://example.com/diagram.png" class="field-input" />
                </div>
              </div>
              <div class="flex justify-end gap-3 pt-2">
                <button (click)="editTarget.set(null)" class="btn-outline">Cancel</button>
                <button (click)="doEdit()" [disabled]="saving()" class="btn-primary">
                  @if (saving()) { Saving... } @else {
                    <lucide-icon name="save" class="h-4 w-4"></lucide-icon> Save Changes
                  }
                </button>
              </div>
            </div>
          </div>
        }
      }

      <!-- ══════════════ SETTINGS ══════════════ -->
      @if (tab() === 'settings') {
        <div class="rounded-xl border bg-card p-6 space-y-6">
          <h2 class="font-semibold text-lg">Admin Settings</h2>
          <div class="space-y-4 max-w-md">
            <div>
              <label class="field-label">Admin Password</label>
              <div class="flex gap-2">
                <input type="password" [value]="newPassword()" (input)="newPassword.set(val($event))"
                  placeholder="New password" class="field-input flex-1" />
                <button (click)="savePassword()" class="btn-primary px-4"
                  [disabled]="!newPassword().trim()">
                  <lucide-icon name="save" class="h-4 w-4"></lucide-icon> Save
                </button>
              </div>
              <p class="text-xs text-muted-foreground mt-1">
                Password is stored in session only — updating here sets the active session password.
              </p>
            </div>
            <hr class="border-border" />
            <div>
              <h3 class="text-sm font-medium mb-2">Pipeline Status</h3>
              <div class="rounded-lg border bg-muted/30 p-4 space-y-2 text-sm text-muted-foreground">
                <div class="flex justify-between">
                  <span>Active ingestion jobs</span>
                  <span class="font-medium text-foreground">{{ activeJobCount() }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Total projects</span>
                  <span class="font-medium text-foreground">{{ allProjects().length }}</span>
                </div>
                <div class="flex justify-between">
                  <span>Application suites</span>
                  <span class="font-medium text-foreground">{{ suites().length }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      }

    </div>
  `,
})
export class AdminComponent implements OnInit, OnDestroy {
  private title          = inject(Title);
  private projectService = inject(ProjectService);
  private adminService   = inject(AdminService);

  tab             = signal<'add-project' | 'manage-projects' | 'settings'>('add-project');
  newSuiteMode    = signal(false);
  selectedFile    = signal<File | null>(null);
  toast           = signal<Toast | null>(null);
  deleteTarget    = signal<Project | null>(null);
  editTarget      = signal<Project | null>(null);
  allProjects     = signal<Project[]>([]);
  suites          = signal<{ id: string; name: string }[]>([]);
  saving          = signal(false);
  loadingProjects = signal(false);
  authenticated   = signal(false);
  authError       = signal(false);
  newPassword     = signal('');

  // Build Now state
  buildJob    = signal<JobStatus | null>(null);
  buildRepoId = signal<string | null>(null);

  // Re-index state per project
  reindexJobs = signal<Record<string, JobStatus>>({});

  form:     ProjectForm = EMPTY_FORM();
  editForm: ProjectForm = EMPTY_FORM();

  private _pollSub:          Subscription | null = null;
  private _reindexSubs:      Record<string, Subscription> = {};
  private _sessionPassword = environment.adminPassword;

  get reindexJobEntries() {
    return () => Object.entries(this.reindexJobs()).map(([repoId, job]) => ({ repoId, job }));
  }

  activeJobCount() {
    const buildRunning = this.buildJob()?.status === 'running' ? 1 : 0;
    const reindexRunning = Object.values(this.reindexJobs()).filter(j => j.status === 'running').length;
    return buildRunning + reindexRunning;
  }

  ngOnInit() {
    this.title.setTitle('DeepWiki — Admin');
    this._loadSuites();
  }

  ngOnDestroy() {
    this._pollSub?.unsubscribe();
    Object.values(this._reindexSubs).forEach(s => s.unsubscribe());
  }

  checkPassword(pw: string): void {
    if (pw === this._sessionPassword) {
      this.authenticated.set(true);
      this.authError.set(false);
    } else {
      this.authError.set(true);
    }
  }

  savePassword(): void {
    const pw = this.newPassword().trim();
    if (!pw) return;
    this._sessionPassword = pw;
    this.newPassword.set('');
    this.notify('success', 'Session password updated.');
  }

  private _loadSuites(): void {
    this.loadingProjects.set(true);
    this.projectService.getSuites().subscribe({
      next: (s) => {
        this.suites.set(s.map(x => ({ id: x.id, name: x.name })));
        // Also load ALL repos so orphans (no suite) are visible in Manage Projects
        this.projectService.getAllRepos().subscribe({
          next: (allRows) => {
            const suiteProjects = s.flatMap(suite => suite.projects);
            const suiteIds = new Set(suiteProjects.map(p => p.id));
            const orphans: import('../../core/models').Project[] = allRows
              .filter(r => !suiteIds.has(r.id))
              .map(r => ({
                id:          r.id,
                name:        r.name,
                suite:       r.suite_id || 'unassigned',
                techStack:   r.tech_stack?.length ? r.tech_stack : r.language ? [r.language] : [],
                description: r.description,
                modules:     [],
                relations:   [],
                apis:        [],
                status:      (r.status as any) || 'active',
                repositoryUrl:  r.repository_url || undefined,
                confluenceLink: r.confluence_link || undefined,
                isDummy: !!r.is_dummy,
              }));
            this.allProjects.set([...suiteProjects, ...orphans]);
            this.loadingProjects.set(false);
          },
          error: () => {
            this.allProjects.set(s.flatMap(suite => suite.projects));
            this.loadingProjects.set(false);
          },
        });
      },
      error: () => {
        // Fallback: try to show all repos directly
        this.projectService.getAllRepos().subscribe({
          next: (allRows) => {
            const suiteSet = new Set<string>();
            allRows.forEach(r => { if (r.suite_id) suiteSet.add(r.suite_id); });
            this.suites.set([...suiteSet].map(id => {
              const row = allRows.find(r => r.suite_id === id)!;
              return { id, name: row.suite_name || id };
            }));
            this.allProjects.set(allRows.map(r => ({
              id:          r.id,
              name:        r.name,
              suite:       r.suite_id || 'unassigned',
              techStack:   r.tech_stack?.length ? r.tech_stack : r.language ? [r.language] : [],
              description: r.description,
              modules:     [],
              relations:   [],
              apis:        [],
              status:      (r.status as any) || 'active',
              repositoryUrl:  r.repository_url || undefined,
              confluenceLink: r.confluence_link || undefined,
              isDummy: !!r.is_dummy,
            })));
            this.loadingProjects.set(false);
          },
          error: () => {
            const fb = MOCK_SUITES;
            this.suites.set(fb.map(x => ({ id: x.id, name: x.name })));
            this.allProjects.set(fb.flatMap(s => s.projects));
            this.loadingProjects.set(false);
          },
        });
      },
    });
  }

  // ── Form helpers ────────────────────────────────────────────────────────

  addTech(input: HTMLInputElement): void {
    const v = input.value.trim();
    if (!v || this.form.techStack.includes(v)) return;
    this.form = { ...this.form, techStack: [...this.form.techStack, v] };
    input.value = '';
  }

  removeTech(tech: string): void {
    this.form = { ...this.form, techStack: this.form.techStack.filter(t => t !== tech) };
  }

  onFile(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      this.notify('error', 'Please upload an image file.');
      return;
    }
    this.selectedFile.set(file);
    const reader = new FileReader();
    reader.onload = e => {
      this.form = { ...this.form, architectureDiagram: e.target?.result as string };
    };
    reader.readAsDataURL(file);
  }

  removeFile(): void {
    this.selectedFile.set(null);
    this.form = { ...this.form, architectureDiagram: '' };
  }

  resetForm(): void {
    this.form = EMPTY_FORM();
    this.selectedFile.set(null);
    this.newSuiteMode.set(false);
    this.buildJob.set(null);
    this.buildRepoId.set(null);
    this._pollSub?.unsubscribe();
    this._pollSub = null;
  }

  clearBuild(): void {
    this.buildJob.set(null);
    this.buildRepoId.set(null);
    this._pollSub?.unsubscribe();
    this._pollSub = null;
    this.form = EMPTY_FORM();
    this.selectedFile.set(null);
    this.newSuiteMode.set(false);
  }

  // ── Validate & resolve suite ─────────────────────────────────────────────

  private _validateForm(): boolean {
    if (!this.form.name.trim()) {
      this.notify('error', 'Project name is required.');
      return false;
    }
    if (!this.form.description.trim()) {
      this.notify('error', 'Description is required.');
      return false;
    }
    const suite = this.newSuiteMode() ? this.form.newSuite.trim() : this.form.suite;
    if (!suite) {
      this.notify('error', 'Please select or create an application suite.');
      return false;
    }
    return true;
  }

  private _getSuiteId(): string {
    return this.newSuiteMode() ? this.form.newSuite.trim() : this.form.suite;
  }

  // ── Save metadata only (no pipeline) ─────────────────────────────────────

  submitMetaOnly(): void {
    if (!this._validateForm()) return;
    let suiteId = this._getSuiteId();
    this.saving.set(true);

    const doCreate = (sid: string) => {
      const diagram = this.form.diagramMode === 'url'
        ? this.form.diagramUrl : this.form.architectureDiagram;
      this.projectService.createProject({
        name: this.form.name.trim(), description: this.form.description.trim(),
        story: this.form.story.trim(), suite_id: sid,
        tech_stack: this.form.techStack, repository_url: this.form.repositoryUrl.trim(),
        confluence_link: this.form.confluenceLink.trim(), architecture_diagram: diagram,
        language: this.form.techStack[0] ?? '', status: this.form.status,
      }).subscribe({
        next: () => {
          this.saving.set(false);
          this.notify('success', `Project "${this.form.name}" saved.`);
          this.resetForm();
          this._loadSuites();
        },
        error: (err) => {
          this.saving.set(false);
          this.notify('error', err?.error?.detail ?? 'Failed to save project.');
        },
      });
    };

    if (this.newSuiteMode() && suiteId) {
      this.projectService.createSuite({ name: suiteId, description: this.form.newSuiteDesc.trim() })
        .subscribe({
          next: (res) => doCreate(res.id),
          error: () => { this.saving.set(false); this.notify('error', 'Failed to create suite.'); },
        });
    } else {
      doCreate(suiteId);
    }
  }

  // ── Build Now ─────────────────────────────────────────────────────────────

  buildNow(): void {
    if (!this._validateForm()) return;
    if (!this.form.repositoryUrl.trim() && !this.form.confluenceLink.trim()) {
      this.notify('error', 'Build Now requires a Repository URL or Confluence link.');
      return;
    }

    const startBuild = (suiteId: string) => {
      const diagram = this.form.diagramMode === 'url'
        ? this.form.diagramUrl : this.form.architectureDiagram;
      this.saving.set(true);
      this.adminService.onboardRepo({
        name:                this.form.name.trim(),
        suite_id:            suiteId,
        repo_url:            this.form.repositoryUrl.trim(),
        confluence_link:     this.form.confluenceLink.trim(),
        description:         this.form.description.trim(),
        story:               this.form.story.trim(),
        tech_stack:          this.form.techStack,
        architecture_diagram: diagram,
        status:              this.form.status,
      }).subscribe({
        next: (res) => {
          this.saving.set(false);
          this.buildRepoId.set(res.repo_id);
          this._startPolling(res.repo_id);
        },
        error: (err) => {
          this.saving.set(false);
          this.notify('error', err?.error?.detail ?? 'Failed to start build.');
        },
      });
    };

    if (this.newSuiteMode() && this.form.newSuite.trim()) {
      this.saving.set(true);
      this.projectService.createSuite({
        name: this.form.newSuite.trim(), description: this.form.newSuiteDesc.trim()
      }).subscribe({
        next: (res) => { this.saving.set(false); startBuild(res.id); },
        error: () => { this.saving.set(false); this.notify('error', 'Failed to create suite.'); },
      });
    } else {
      startBuild(this._getSuiteId());
    }
  }

  retryBuild(): void {
    const repoId = this.buildRepoId();
    if (!repoId) return;
    this.buildJob.set(null);
    this.saving.set(true);
    // Restart the pipeline via reindex — the backend resets job state and re-runs from scratch.
    // Clone step is resume-safe: if the repo was already cloned it skips re-cloning.
    this.adminService.reindex(repoId).subscribe({
      next: () => {
        this.saving.set(false);
        this._startPolling(repoId);
      },
      error: (err) => {
        this.saving.set(false);
        this.notify('error', err?.error?.detail ?? 'Failed to restart pipeline.');
      },
    });
  }

  private _startPolling(repoId: string): void {
    this._pollSub?.unsubscribe();
    // Show initial skeleton job
    this.buildJob.set({
      repo_id: repoId, status: 'running', progress: 0,
      current_step: 'Cloning repository',
      steps: [
        'Cloning repository', 'Parsing source files', 'Writing knowledge graph',
        'Generating wiki summaries', 'Extracting API contracts', 'Embedding to Qdrant',
        'Matching API contracts', 'Registering project',
      ].map(label => ({ label, status: 'pending', detail: '' })),
      stats: {},
    });
    this._pollSub = this.adminService.pollStatus(repoId).subscribe({
      next: (status) => {
        this.buildJob.set(status);
        if (status.status === 'done') {
          this._loadSuites();
          this.notify('success', 'Build complete! Project is now live in DeepWiki.');
        }
      },
      error: () => {
        this.buildJob.update(j => j ? { ...j, status: 'error', error: 'Lost connection to pipeline.' } : j);
      },
    });
  }

  // ── Re-index ─────────────────────────────────────────────────────────────

  reindex(p: Project): void {
    this.reindexJobs.update(jobs => ({
      ...jobs,
      [p.id]: {
        repo_id: p.id, status: 'running', progress: 0,
        current_step: 'Starting…',
        steps: [], stats: {},
      },
    }));

    this.adminService.reindex(p.id).subscribe({
      next: () => {
        this._reindexSubs[p.id]?.unsubscribe();
        this._reindexSubs[p.id] = this.adminService.pollStatus(p.id).subscribe({
          next: (status) => {
            this.reindexJobs.update(jobs => ({ ...jobs, [p.id]: status }));
            if (status.status === 'done') {
              this.notify('success', `"${p.name}" re-indexed successfully.`);
              setTimeout(() => {
                this.reindexJobs.update(jobs => {
                  const copy = { ...jobs };
                  delete copy[p.id];
                  return copy;
                });
              }, 3000);
            }
          },
          error: () => {
            this.reindexJobs.update(jobs => ({
              ...jobs,
              [p.id]: { ...jobs[p.id], status: 'error', error: 'Lost connection.' },
            }));
          },
        });
      },
      error: (err) => {
        this.notify('error', err?.error?.detail ?? `Failed to re-index "${p.name}".`);
        this.reindexJobs.update(jobs => {
          const copy = { ...jobs };
          delete copy[p.id];
          return copy;
        });
      },
    });
  }

  // ── Edit ──────────────────────────────────────────────────────────────────

  openEdit(p: Project): void {
    this.editTarget.set(p);
    this.editForm = {
      name: p.name, suite: p.suite, newSuite: '', newSuiteDesc: '',
      techStack: [...p.techStack], description: p.description, story: p.story ?? '',
      repositoryUrl: p.repositoryUrl ?? '', confluenceLink: p.confluenceLink ?? '',
      architectureDiagram: p.architectureDiagram ?? '',
      diagramMode: 'url', diagramUrl: p.architectureDiagram ?? '',
      status: p.status ?? 'active',
    };
  }

  doEdit(): void {
    const t = this.editTarget();
    if (!t || !this.editForm.name.trim()) {
      this.notify('error', 'Project name is required.');
      return;
    }
    this.saving.set(true);
    this.projectService.updateProject(t.id, {
      name: this.editForm.name.trim(), description: this.editForm.description.trim(),
      story: this.editForm.story.trim(), suite_id: this.editForm.suite || undefined,
      tech_stack: this.editForm.techStack, repository_url: this.editForm.repositoryUrl.trim(),
      confluence_link: this.editForm.confluenceLink.trim(),
      architecture_diagram: this.editForm.diagramUrl.trim(),
      status: this.editForm.status,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.editTarget.set(null);
        this.notify('success', `"${this.editForm.name}" updated.`);
        this._loadSuites();
      },
      error: (err) => {
        this.saving.set(false);
        this.notify('error', err?.error?.detail ?? 'Failed to update project.');
      },
    });
  }

  // ── Delete ────────────────────────────────────────────────────────────────

  askDelete(p: Project): void { this.deleteTarget.set(p); }

  doDelete(): void {
    const t = this.deleteTarget();
    if (!t) return;
    this.saving.set(true);
    this.projectService.deleteProject(t.id).subscribe({
      next: () => {
        this.saving.set(false);
        this.allProjects.update(list => list.filter(p => p.id !== t.id));
        this.notify('success', `"${t.name}" deleted.`);
        this.deleteTarget.set(null);
      },
      error: (err) => {
        this.saving.set(false);
        this.notify('error', err?.error?.detail ?? 'Failed to delete project.');
        this.deleteTarget.set(null);
      },
    });
  }

  // ── Utilities ─────────────────────────────────────────────────────────────

  stepLabelClass(status: string): string {
    switch (status) {
      case 'done':      return 'text-foreground font-medium';
      case 'running':   return 'text-primary font-medium';
      case 'error':     return 'text-destructive font-semibold';
      case 'skipped':   return 'text-muted-foreground';
      case 'cancelled': return 'text-muted-foreground/50 line-through';
      default:          return 'text-muted-foreground/60';
    }
  }

  statusClass(status: string): string {
    if (status === 'active')     return 'text-green-600 font-medium';
    if (status === 'beta')       return 'text-blue-600 font-medium';
    if (status === 'deprecated') return 'text-muted-foreground line-through';
    return '';
  }

  val(e: Event): string {
    return (e.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value;
  }

  private notify(type: 'success' | 'error', message: string): void {
    this.toast.set({ type, message });
    setTimeout(() => this.toast.set(null), 5000);
  }
}
