import { Suite, Project, Module } from './index';

export interface GraphNode {
  id: string;
  label: string;
  shortLabel: string;
  type: 'suite' | 'suite-center' | 'project' | 'project-center' | 'module' | 'external';
  color: string;
  r: number;
  data: Suite | Project | Module;
  alpha?: number;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: 'owns' | 'connects' | 'inter-suite';
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export type GraphLevel = 'cosmos' | 'suite' | 'project';
