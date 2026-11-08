// A "model" describes the SHAPE of one thing in your product.
// This says: every book in Bookaroo has these parts.
//
// When you want a book to hold something new (say, a star rating, or a
// "condition: like new / well-loved"), add it here first — then Claude can
// help you show it on the screen.
export interface Book {
  id: string;         // a unique tag so the app can tell books apart
  emoji: string;      // the cover picture, for now
  title: string;      // the book's name
  author: string;     // who wrote it
  owner: string;      // whose book it is (the kid offering it)
  swapFor: string;    // what they'd like to swap it for
}
