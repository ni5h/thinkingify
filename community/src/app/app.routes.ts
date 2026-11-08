import { Routes } from '@angular/router';

// Every screen in the app is a route. Right now there's one: the home page.
// When you design a new screen (like "My Shelf" or "Add a Book"), we add a
// line here that points its web address to a component.
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home.component'),
  },
];
