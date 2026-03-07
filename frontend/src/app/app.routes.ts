import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    loadComponent: () => import('./pages/home/home').then(m => m.Home)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard').then(m => m.Dashboard)
  },
  {
    path: 'devices',
    loadComponent: () => import('./pages/devices/devices').then(m => m.Devices)
  },
  {
    path: 'agent-hub',
    loadComponent: () => import('./pages/agent-hub/agent-hub').then(m => m.AgentHub)
  },
  {
    path: 'automations',
    loadComponent: () => import('./pages/automations/automations').then(m => m.Automations)
  },
  {
    path: 'history',
    loadComponent: () => import('./pages/history/history').then(m => m.History)
  }
];