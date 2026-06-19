import { Routes } from '@angular/router';
import { authGuard } from './services/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/auth/auth').then(m => m.Auth)
  },
  {
    path: 'home',
    loadComponent: () => import('./pages/home/home').then(m => m.Home),
    canActivate: [authGuard]
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard').then(m => m.Dashboard),
    canActivate: [authGuard]
  },
  {
    path: 'devices',
    loadComponent: () => import('./pages/devices/devices').then(m => m.Devices),
    canActivate: [authGuard]
  },
  {
    path: 'agent-hub',
    loadComponent: () => import('./pages/agent-hub/agent-hub').then(m => m.AgentHub),
    canActivate: [authGuard]
  },
  {
    path: 'automations',
    loadComponent: () => import('./pages/automations/automations').then(m => m.Automations),
    canActivate: [authGuard]
  },
  {
    path: 'history',
    loadComponent: () => import('./pages/history/history').then(m => m.History),
    canActivate: [authGuard]
  }
];
