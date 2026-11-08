import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BooksService } from '../../core/books.service';

// The home screen: a welcome, the shelf of books kids are offering, and a
// little form to add your own. A "component" is one screen (or one piece of a
// screen). It asks the BooksService for the books and shows them.
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule],
  template: `
    <!-- Welcome -->
    <section class="pt-10 pb-6 text-center">
      <h1 class="font-display text-3xl sm:text-4xl text-ink">Trade books with friends</h1>
      <p class="text-muted mt-2 max-w-md mx-auto">Finished a book? Offer it here and swap it for one you haven't read yet.</p>
    </section>

    <!-- Add a book -->
    <section class="rounded-2xl border border-cloud bg-white shadow-sm p-5 mb-8">
      <h2 class="font-display text-lg text-ink mb-3">Offer a book</h2>
      <div class="grid gap-3 sm:grid-cols-2">
        <input class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss" placeholder="Book title" [(ngModel)]="title" />
        <input class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss" placeholder="Author" [(ngModel)]="author" />
        <input class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss" placeholder="Your name" [(ngModel)]="owner" />
        <input class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss" placeholder="Swap it for…" [(ngModel)]="swapFor" />
        <input class="rounded-xl border border-cloud bg-paper px-3 py-2.5 focus:outline-none focus:border-moss sm:col-span-2" placeholder="Pick a cover emoji (like 🐉 or ⚽)" [(ngModel)]="emoji" />
      </div>
      <button
        class="mt-4 rounded-xl bg-spine px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:brightness-95 disabled:opacity-50 transition"
        [disabled]="!title().trim() || !owner().trim()"
        (click)="addBook()">
        Add to the shelf
      </button>
    </section>

    <!-- The shelf -->
    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      @for (book of books.all(); track book.id) {
        <article class="rounded-2xl border border-cloud bg-white shadow-sm p-5 transition hover:-translate-y-1 hover:shadow-md">
          <div class="text-5xl text-center leading-none">{{ book.emoji || '📘' }}</div>
          <h3 class="font-display text-lg text-ink mt-3">{{ book.title }}</h3>
          <p class="text-sm text-muted">by {{ book.author || 'unknown' }}</p>
          <p class="text-xs font-mono text-muted mt-1">offered by {{ book.owner }}</p>
          <p class="mt-3 rounded-xl bg-spine-tint px-3 py-2 text-sm">
            Swap for: <b class="text-moss-dark">{{ book.swapFor || 'anything good' }}</b>
          </p>
        </article>
      } @empty {
        <p class="text-muted col-span-full text-center py-8">No books yet — add the first one above!</p>
      }
    </section>
  `,
})
export default class HomeComponent {
  readonly books = inject(BooksService);

  // The words currently typed into the form.
  readonly title = signal('');
  readonly author = signal('');
  readonly owner = signal('');
  readonly swapFor = signal('');
  readonly emoji = signal('');

  addBook(): void {
    this.books.add({
      title: this.title().trim(),
      author: this.author().trim(),
      owner: this.owner().trim(),
      swapFor: this.swapFor().trim(),
      emoji: this.emoji().trim(),
    });
    // Clear the form for the next book.
    this.title.set('');
    this.author.set('');
    this.owner.set('');
    this.swapFor.set('');
    this.emoji.set('');
  }
}
