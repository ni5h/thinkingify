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
  { path: 'blog', loadComponent: () => import('./features/blog/blog.component') },
  { path: 'progress', loadComponent: () => import('./features/progress/progress.component') },
];
