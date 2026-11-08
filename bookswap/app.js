// 🛠️  THE ENGINE
//
// You don't HAVE to change this file — it's the part that turns your
// book list into cards on the page. But you can peek, and if you're
// curious, try changing things and see what happens!
//
// What it does, in plain words:
//   "For each book in myBooks, build a card and put it on the shelf."

// Find the empty shelf box in index.html
const shelf = document.getElementById("shelf");

// Go through every book, one at a time
for (const book of myBooks) {

  // Make a new card
  const card = document.createElement("article");
  card.className = "card";

  // Fill the card with the book's words.
  // (The emoji is the cover, then the title, author, and swap note.)
  card.innerHTML = `
    <div class="cover">${book.emoji}</div>
    <h2 class="title">${book.title}</h2>
    <p class="author">by ${book.author}</p>
    <p class="swap">I'll swap it for: <b>${book.swapFor}</b></p>
  `;

  // Put the finished card on the shelf
  shelf.appendChild(card);
}

// A tiny bonus: show a happy message if there are no books yet.
if (myBooks.length === 0) {
  shelf.innerHTML = `<p class="empty">Your shelf is empty — add your first book in books.js!</p>`;
}
