import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', loadComponent: () => import('./features/home/home.component') },
  { path: 'puzzle', loadComponent: () => import('./features/puzzle/puzzle.component') },
  { path: 'learn', loadComponent: () => import('./features/learn/learn.component') },
  {
    path: 'journal',
    loadComponent: () => import('./features/journal/journal-list.component'),
  },
  { path: 'blog/manage/new', loadComponent: () => import('./features/blog/blog-editor.component') },
  {
    path: 'blog/manage/:id/edit',
    loadComponent: () => import('./features/blog/blog-editor.component'),
  },
  { path: 'blog/manage', loadComponent: () => import('./features/blog/blog-manage.component') },
  { path: 'blog/:id', loadComponent: () => import('./features/blog/blog-post.component') },
  { path: 'blog', loadComponent: () => import('./features/blog/blog-home.component') },
  { path: 'progress', loadComponent: () => import('./features/progress/progress.component') },
];
