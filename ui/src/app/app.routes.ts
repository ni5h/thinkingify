import { Routes } from '@angular/router';
import { noAuthGuard, noPuzzleAuthGuard, requireLearnerRole, requireStudioRole } from './core/auth.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/vision/vision.component') },
  { path: 'profile', loadComponent: () => import('./features/profile/profile.component') },
  { path: 'dashboard', loadComponent: () => import('./features/dashboard/dashboard.component') },
  {
    path: 'puzzle/login',
    loadComponent: () => import('./features/puzzle/login/puzzle-login.component'),
    canActivate: [noPuzzleAuthGuard],
  },
  {
    path: 'puzzle/kakooma',
    loadComponent: () => import('./features/puzzle/kakooma/kakooma.component'),
    canActivate: [requireLearnerRole],
  },
  {
    path: 'puzzle',
    loadComponent: () => import('./features/puzzle/home/puzzle-home.component'),
    canActivate: [requireLearnerRole],
  },
  { path: 'learn', loadComponent: () => import('./features/learn/learn.component') },
  { path: 'journal/new', loadComponent: () => import('./features/journal/journal-entry.component') },
  { path: 'journal/:id', loadComponent: () => import('./features/journal/journal-entry.component') },
  {
    path: 'journal',
    loadComponent: () => import('./features/journal/journal-list.component'),
  },
  {
    path: 'studio/login',
    loadComponent: () => import('./features/studio/login/login.component'),
    canActivate: [noAuthGuard],
  },
  {
    path: 'studio/posts/new',
    loadComponent: () => import('./features/studio/post-editor/post-editor.component'),
    canActivate: [requireStudioRole],
  },
  {
    path: 'studio/posts/:id/edit',
    loadComponent: () => import('./features/studio/post-editor/post-editor.component'),
    canActivate: [requireStudioRole],
  },
  {
    path: 'studio/posts',
    loadComponent: () => import('./features/studio/posts-list/posts-list.component'),
    canActivate: [requireStudioRole],
  },
  {
    path: 'studio',
    loadComponent: () => import('./features/studio/dashboard/dashboard.component'),
    canActivate: [requireStudioRole],
  },
  { path: 'blog/:slug', loadComponent: () => import('./features/blog/blog-post.component') },
  { path: 'blog', loadComponent: () => import('./features/blog/blog-home.component') },
  { path: 'progress', loadComponent: () => import('./features/progress/progress.component') },
];
