import { Routes } from '@angular/router';
import { noAuthGuard, noPuzzleAuthGuard, requireLearnerRole, requireStudioRole } from './core/auth.guard';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/vision/vision.component') },
  { path: 'profile', loadComponent: () => import('./features/profile/profile.component') },
  { path: 'dashboard', loadComponent: () => import('./features/dashboard/dashboard.component') },
  {
    path: 'sherlock/login',
    loadComponent: () => import('./features/sherlock/login/puzzle-login.component'),
    canActivate: [noPuzzleAuthGuard],
  },
  {
    path: 'sherlock/kakooma',
    loadComponent: () => import('./features/sherlock/kakooma/kakooma.component'),
    canActivate: [requireLearnerRole],
  },
  {
    path: 'sherlock',
    loadComponent: () => import('./features/sherlock/home/puzzle-home.component'),
    canActivate: [requireLearnerRole],
  },
  { path: 'ramanujan', loadComponent: () => import('./features/ramanujan/ramanujan.component') },
  { path: 'einstein', loadComponent: () => import('./features/einstein/einstein.component') },
  {
    path: 'rowling',
    loadComponent: () => import('./features/rowling/room-landing/room-landing.component'),
    canActivate: [requireLearnerRole],
  },
  {
    path: 'rowling/topics/:slug/style',
    loadComponent: () => import('./features/rowling/style-chooser/style-chooser.component'),
    canActivate: [requireLearnerRole],
  },
  {
    path: 'rowling/topics/:slug',
    loadComponent: () => import('./features/rowling/topic-reader/topic-reader.component'),
    canActivate: [requireLearnerRole],
  },
  {
    path: 'rowling/write/:id',
    loadComponent: () => import('./features/rowling/writing-studio/writing-studio.component'),
    canActivate: [requireLearnerRole],
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
    path: 'studio/topics/new',
    loadComponent: () => import('./features/studio/topic-editor/topic-editor.component'),
    canActivate: [requireStudioRole],
  },
  {
    path: 'studio/topics/:id/edit',
    loadComponent: () => import('./features/studio/topic-editor/topic-editor.component'),
    canActivate: [requireStudioRole],
  },
  {
    path: 'studio/topics',
    loadComponent: () => import('./features/studio/topics-list/topics-list.component'),
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
