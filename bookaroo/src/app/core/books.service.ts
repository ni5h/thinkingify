import { Injectable, signal } from '@angular/core';
import { Book } from './book.model';

// A "service" is where your product keeps its information and the things it can
// DO with that information. This one holds the list of books and can add new
// ones. Screens ask the service for the books — they don't keep their own copy.
//
// Right now the books live here in the code (the `starterBooks` list below).
// Later, Claude can help you move them to a real database so every kid sees
// everyone's books. The screens won't have to change when we do that — that's
// why the list lives behind a service.
@Injectable({ providedIn: 'root' })
export class BooksService {
  // The living list of books. `signal` means: when this changes, the screen
  // updates by itself. No refresh needed.
  private readonly books = signal<Book[]>(starterBooks);

  // Screens read the books through this.
  readonly all = this.books.asReadonly();

  // Add a new book to the top of the list.
  add(book: Omit<Book, 'id'>): void {
    const withId: Book = { ...book, id: crypto.randomUUID() };
    this.books.update((list) => [withId, ...list]);
  }
}

// 📚 The starter books. Edit these, or let Neo add real ones through the app.
const starterBooks: Book[] = [
  { id: '1', emoji: '🐉', title: 'The Dragon Who Lost His Fire', author: 'R. K. Sharma', owner: 'Neo', swapFor: 'any funny comic book' },
  { id: '2', emoji: '🚀', title: 'Zara and the Rocket to School', author: 'Meera Nair', owner: 'Aanya', swapFor: 'a space facts book' },
  { id: '3', emoji: '🦕', title: 'Big Book of Dinosaurs', author: 'Tom Alban', owner: 'Kabir', swapFor: 'a mystery story' },
  { id: '4', emoji: '🕵️', title: 'The Case of the Missing Lunchbox', author: 'Priya Das', owner: 'Ishaan', swapFor: 'anything about animals' },
];
