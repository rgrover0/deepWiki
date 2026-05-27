import { Project } from './project.model';

export interface Suite {
  id: string;
  name: string;
  description: string;
  color: string;
  projects: Project[];
}
