import { Routes } from '@angular/router';
import { authGuard, noAuthGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/vision/vision.component') },
  { path: 'profile', loadComponent: () => import('./features/profile/profile.component') },
  { path: 'dashboard', loadComponent: () => import('./features/dashboard/dashboard.component') },
  { path: 'puzzle', loadComponent: () => import('./features/puzzle/puzzle.component') },
  { path: 'learn', loadComponent: () => import('./features/learn/learn.component') },
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
    canActivate: [authGuard],
  },
  {
    path: 'studio/posts/:id/edit',
    loadComponent: () => import('./features/studio/post-editor/post-editor.component'),
    canActivate: [authGuard],
  },
  {
    path: 'studio/posts',
    loadComponent: () => import('./features/studio/posts-list/posts-list.component'),
    canActivate: [authGuard],
  },
  {
    path: 'studio',
    loadComponent: () => import('./features/studio/dashboard/dashboard.component'),
    canActivate: [authGuard],
  },
  { path: 'blog/:slug', loadComponent: () => import('./features/blog/blog-post.component') },
  { path: 'blog', loadComponent: () => import('./features/blog/blog-home.component') },
  { path: 'progress', loadComponent: () => import('./features/progress/progress.component') },
];
