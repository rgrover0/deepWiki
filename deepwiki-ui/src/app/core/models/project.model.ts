export interface Module {
  id: string;
  name: string;
  description: string;
  features: string[];
  classCount?: number;
  type?: 'core' | 'security' | 'feature' | 'event' | 'analytics' | 'admin';
}

export interface Relation {
  projectId: string;
  projectName: string;
  type: 'depends-on' | 'provides-to' | 'integrates-with';
  description: string;
}

export interface ApiContract {
  id: string;
  name: string;
  type: 'exposed' | 'consumed';
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  description: string;
  authRequired?: boolean;
}

export interface Project {
  id: string;
  name: string;
  suite: string;
  techStack: string[];
  description: string;
  story?: string;
  modules: Module[];
  relations: Relation[];
  apis: ApiContract[];
  status?: 'active' | 'beta' | 'deprecated';
  lastDeploy?: string;
}
