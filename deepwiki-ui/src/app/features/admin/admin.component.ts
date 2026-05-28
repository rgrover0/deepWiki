import { Component, OnInit, inject, signal } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { Project, Suite } from '../../core/models';
import { LucideAngularModule } from 'lucide-angular';
import { ProjectService } from '../../core/services/project.service';
import { MOCK_SUITES } from '../../core/services/mock-data';

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
             text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50;
    }
    .btn-outline {
      @apply flex items-center gap-2 h-10 px-4 rounded-lg border bg-background
             text-sm font-medium hover:bg-muted transition-colors;
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
    <div class="space-y-6">

      <!-- Page header -->
      <div>
        <h1 class="text-4xl font-bold tracking-tight flex items-center gap-3">
          <lucide-icon name="settings" class="h-8 w-8 text-primary"></lucide-icon>
          Admin Panel
        </h1>
        <p class="text-muted-foreground text-lg mt-2">
          Manage projects, repositories, and documentation
        </p>
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
                Add a new project to your DeepWiki catalog with documentation and architecture details
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
                  <input type="text"
                    [value]="form.name"
                    (input)="form.name = val($event)"
                    placeholder="e.g., Authentication Service"
                    class="field-input" />
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
                <div class="relative">
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
                  placeholder="Brief description of the project..." rows="3"
                  class="field-textarea"></textarea>
              </div>

              <div>
                <label class="field-label">Project Story &amp; History</label>
                <textarea [value]="form.story" (input)="form.story = val($event)"
                  placeholder="Tell the story behind this project..." rows="4"
                  class="field-textarea"></textarea>
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
                <input type="text" #techInput
                  (keydown.enter)="addTech(techInput)"
                  placeholder="e.g., Node.js, PostgreSQL, Redis"
                  class="field-input flex-1" />
                <button (click)="addTech(techInput)" class="btn-primary px-5">
                  <lucide-icon name="plus" class="h-4 w-4"></lucide-icon>
                  Add
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
                <div class="flex gap-2">
                  <input type="url" [value]="form.repositoryUrl" (input)="form.repositoryUrl = val($event)"
                    placeholder="https://github.com/org/repo" class="field-input flex-1" />
                  <button class="btn-icon">
                    <lucide-icon name="link" class="h-4 w-4 text-muted-foreground"></lucide-icon>
                  </button>
                </div>
              </div>
              <div>
                <label class="field-label">Confluence Page Link</label>
                <div class="flex gap-2">
                  <input type="url" [value]="form.confluenceLink" (input)="form.confluenceLink = val($event)"
                    placeholder="https://confluence.company.com/pages/..." class="field-input flex-1" />
                  <button class="btn-icon">
                    <lucide-icon name="file-text" class="h-4 w-4 text-muted-foreground"></lucide-icon>
                  </button>
                </div>
              </div>
            </div>

            <hr class="border-border" />

            <!-- §4 Architecture Diagram -->
            <div>
              <h3 class="section-title">
                <lucide-icon name="image" class="h-4 w-4 text-primary"></lucide-icon>
                Architecture Diagram
              </h3>

              <!-- Toggle upload / URL -->
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
                      <lucide-icon name="upload" class="h-12 w-12 text-muted-foreground mx-auto"></lucide-icon>
                      <div>
                        <p class="text-sm text-muted-foreground">Click to upload or drag and drop</p>
                        <p class="text-xs text-muted-foreground mt-0.5">PNG, JPG, SVG up to 10MB</p>
                      </div>
                      <label class="btn-outline cursor-pointer inline-flex mx-auto">
                        <lucide-icon name="upload" class="h-4 w-4"></lucide-icon>
                        Select File
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
                        <img [src]="form.architectureDiagram" alt="Architecture preview"
                          class="max-h-64 mx-auto rounded-lg border shadow-sm" />
                      }
                      <button (click)="removeFile()"
                        class="btn-outline mx-auto inline-flex text-xs px-3 h-8">
                        <lucide-icon name="trash-2" class="h-3 w-3"></lucide-icon>
                        Remove
                      </button>
                    </div>
                  }
                </div>
              } @else {
                <div class="space-y-2">
                  <input type="url" [value]="form.diagramUrl" (input)="form.diagramUrl = val($event)"
                    placeholder="https://example.com/architecture.png"
                    class="field-input" />
                  @if (form.diagramUrl) {
                    <img [src]="form.diagramUrl" alt="Diagram preview"
                      class="max-h-64 rounded-lg border shadow-sm mt-2"
                      (error)="form.diagramUrl = ''" />
                  }
                </div>
              }

              <p class="text-xs text-muted-foreground mt-2">
                Upload or link an architecture diagram to help visualize the project structure
              </p>
            </div>

            <hr class="border-border" />

            <!-- Submit row -->
            <div class="flex justify-end gap-3">
              <button (click)="resetForm()" class="btn-outline">Reset</button>
              <button (click)="submit()" [disabled]="saving()" class="btn-primary">
                @if (saving()) {
                  <lucide-icon name="loader-circle" class="h-4 w-4 animate-spin"></lucide-icon>
                  Saving...
                } @else {
                  <lucide-icon name="save" class="h-4 w-4"></lucide-icon>
                  Add Project
                }
              </button>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="space-y-4">
            <div class="flex gap-3 rounded-xl border bg-muted/50 p-4">
              <lucide-icon name="info" class="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5"></lucide-icon>
              <p class="text-sm text-muted-foreground leading-relaxed">
                Use this admin panel to manage your DeepWiki project catalog. Add new projects,
                update documentation links, and upload architecture diagrams.
              </p>
            </div>
            <div class="rounded-xl border bg-card p-6 space-y-4">
              <div>
                <h3 class="font-semibold text-base">Quick Start Guide</h3>
                <p class="text-sm text-muted-foreground mt-0.5">Follow these steps to add your first project</p>
              </div>
              <ul class="space-y-4">
                <li class="flex items-start gap-3">
                  <div class="step-num">1</div>
                  <div>
                    <p class="text-sm font-medium">Fill in basic information</p>
                    <p class="text-xs text-muted-foreground mt-0.5">Enter project name, description, and select an application suite</p>
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <div class="step-num">2</div>
                  <div>
                    <p class="text-sm font-medium">Add tech stack</p>
                    <p class="text-xs text-muted-foreground mt-0.5">List all technologies used in the project</p>
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <div class="step-num">3</div>
                  <div>
                    <p class="text-sm font-medium">Link documentation</p>
                    <p class="text-xs text-muted-foreground mt-0.5">Add repository URL and Confluence page for easy access</p>
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <div class="step-num">4</div>
                  <div>
                    <p class="text-sm font-medium">Attach architecture diagram</p>
                    <p class="text-xs text-muted-foreground mt-0.5">Upload a file or paste an image URL</p>
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <div class="step-check">
                    <lucide-icon name="check-circle-2" class="h-4 w-4 text-accent"></lucide-icon>
                  </div>
                  <div>
                    <p class="text-sm font-medium">Save and publish</p>
                    <p class="text-xs text-muted-foreground mt-0.5">Your project will be immediately available in DeepWiki</p>
                  </div>
                </li>
              </ul>
            </div>
            <div class="rounded-xl border border-accent/40 bg-accent/5 p-5">
              <div class="flex gap-3">
                <lucide-icon name="info" class="h-5 w-5 text-accent flex-shrink-0 mt-0.5"></lucide-icon>
                <div>
                  <p class="text-sm font-semibold">Creating a new suite</p>
                  <p class="text-xs text-muted-foreground mt-1 leading-relaxed">
                    Click the + button next to the suite selector to create a new application suite.
                    This is useful when onboarding a completely new product line or business unit.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- ══════════════ MANAGE PROJECTS ══════════════ -->
      @if (tab() === 'manage-projects') {
        <div class="rounded-xl border bg-card p-6 space-y-4">
          <div>
            <h2 class="font-semibold text-lg">Existing Projects</h2>
            <p class="text-sm text-muted-foreground mt-0.5">Manage and update existing projects in your catalog</p>
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
                  <div>
                    <h4 class="font-semibold text-sm">{{ p.name }}</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">
                      {{ p.suite }} &bull;
                      @if (p.status) { <span [class]="statusClass(p.status)">{{ p.status }}</span> }
                    </p>
                  </div>
                  <div class="flex gap-2">
                    <button (click)="openEdit(p)"
                      class="h-8 px-3 rounded-lg border text-xs font-medium hover:bg-muted transition-colors flex items-center gap-1.5">
                      <lucide-icon name="pencil" class="h-3 w-3"></lucide-icon>
                      Edit
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
                <lucide-icon name="pencil" class="h-5 w-5"></lucide-icon>
                Edit Project
              </h3>

              <div class="space-y-3">
                <div>
                  <label class="field-label">Project Name *</label>
                  <input type="text" [value]="editForm.name" (input)="editForm.name = val($event)"
                    class="field-input" />
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
                    <lucide-icon name="save" class="h-4 w-4"></lucide-icon>
                    Save Changes
                  }
                </button>
              </div>
            </div>
          </div>
        }
      }

      <!-- ══════════════ SETTINGS ══════════════ -->
      @if (tab() === 'settings') {
        <div class="rounded-xl border bg-card p-6 space-y-2">
          <h2 class="font-semibold text-lg">Admin Settings</h2>
          <p class="text-sm text-muted-foreground">Configure admin panel preferences and permissions</p>
          <p class="text-sm text-muted-foreground py-10 text-center">Settings configuration coming soon...</p>
        </div>
      }

    </div>
  `,
})
export class AdminComponent implements OnInit {
  private title          = inject(Title);
  private projectService = inject(ProjectService);

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

  form:     ProjectForm = EMPTY_FORM();
  editForm: ProjectForm = EMPTY_FORM();

  ngOnInit() {
    this.title.setTitle('DeepWiki — Admin');
    this._loadSuites();
  }

  private _loadSuites(): void {
    this.projectService.getSuites().subscribe({
      next: (s) => {
        this.suites.set(s.map(x => ({ id: x.id, name: x.name })));
        this.allProjects.set(s.flatMap(suite => suite.projects));
      },
      error: () => {
        const fallback = MOCK_SUITES;
        this.suites.set(fallback.map(x => ({ id: x.id, name: x.name })));
        this.allProjects.set(fallback.flatMap(s => s.projects));
      },
    });
  }

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
      this.notify('error', 'Please upload an image file (PNG, JPG or SVG).');
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

  submit(): void {
    if (!this.form.name.trim() || !this.form.description.trim()) {
      this.notify('error', 'Please fill in required fields: Name and Description.');
      return;
    }

    let suiteId = this.form.suite;

    if (this.newSuiteMode()) {
      if (!this.form.newSuite.trim()) {
        this.notify('error', 'Please enter a name for the new suite.');
        return;
      }
      this.saving.set(true);
      this.projectService.createSuite({
        name: this.form.newSuite.trim(),
        description: this.form.newSuiteDesc.trim(),
      }).subscribe({
        next: (res) => {
          suiteId = res.id;
          this._createProject(suiteId);
        },
        error: () => {
          this.saving.set(false);
          this.notify('error', 'Failed to create suite. Please try again.');
        },
      });
      return;
    }

    if (!suiteId) {
      this.notify('error', 'Please select or create an application suite.');
      return;
    }
    this.saving.set(true);
    this._createProject(suiteId);
  }

  private _createProject(suiteId: string): void {
    const diagram = this.form.diagramMode === 'url'
      ? this.form.diagramUrl
      : this.form.architectureDiagram;

    this.projectService.createProject({
      name:                 this.form.name.trim(),
      description:          this.form.description.trim(),
      story:                this.form.story.trim(),
      suite_id:             suiteId,
      tech_stack:           this.form.techStack,
      repository_url:       this.form.repositoryUrl.trim(),
      confluence_link:      this.form.confluenceLink.trim(),
      architecture_diagram: diagram,
      language:             this.form.techStack[0] ?? '',
      status:               this.form.status,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.notify('success', `Project "${this.form.name}" added successfully!`);
        this.resetForm();
        this._loadSuites();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail ?? 'Failed to add project. Please try again.';
        this.notify('error', detail);
      },
    });
  }

  resetForm(): void {
    this.form = EMPTY_FORM();
    this.selectedFile.set(null);
    this.newSuiteMode.set(false);
  }

  openEdit(p: Project): void {
    this.editTarget.set(p);
    this.editForm = {
      name:                p.name,
      suite:               p.suite,
      newSuite:            '',
      newSuiteDesc:        '',
      techStack:           [...p.techStack],
      description:         p.description,
      story:               p.story ?? '',
      repositoryUrl:       p.repositoryUrl ?? '',
      confluenceLink:      p.confluenceLink ?? '',
      architectureDiagram: p.architectureDiagram ?? '',
      diagramMode:         'url',
      diagramUrl:          p.architectureDiagram ?? '',
      status:              p.status ?? 'active',
    };
  }

  doEdit(): void {
    const t = this.editTarget();
    if (!t) return;
    if (!this.editForm.name.trim()) {
      this.notify('error', 'Project name is required.');
      return;
    }
    this.saving.set(true);
    this.projectService.updateProject(t.id, {
      name:                 this.editForm.name.trim(),
      description:          this.editForm.description.trim(),
      story:                this.editForm.story.trim(),
      suite_id:             this.editForm.suite || undefined,
      tech_stack:           this.editForm.techStack,
      repository_url:       this.editForm.repositoryUrl.trim(),
      confluence_link:      this.editForm.confluenceLink.trim(),
      architecture_diagram: this.editForm.diagramUrl.trim(),
      status:               this.editForm.status,
    }).subscribe({
      next: () => {
        this.saving.set(false);
        this.editTarget.set(null);
        this.notify('success', `"${this.editForm.name}" updated successfully.`);
        this._loadSuites();
      },
      error: (err) => {
        this.saving.set(false);
        const detail = err?.error?.detail ?? 'Failed to update project.';
        this.notify('error', detail);
      },
    });
  }

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
        const detail = err?.error?.detail ?? 'Failed to delete project.';
        this.notify('error', detail);
        this.deleteTarget.set(null);
      },
    });
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
    setTimeout(() => this.toast.set(null), 4000);
  }
}
