import { Editor } from '@tiptap/core';

export type ToolbarCommand = 'bold' | 'italic' | 'heading2' | 'heading3' | 'bulletList' | 'orderedList' | 'blockquote';

export function applyToolbarCommand(editor: Editor, command: ToolbarCommand): void {
  const chain = editor.chain().focus();
  switch (command) {
    case 'bold':
      chain.toggleBold().run();
      break;
    case 'italic':
      chain.toggleItalic().run();
      break;
    case 'heading2':
      chain.toggleHeading({ level: 2 }).run();
      break;
    case 'heading3':
      chain.toggleHeading({ level: 3 }).run();
      break;
    case 'bulletList':
      chain.toggleBulletList().run();
      break;
    case 'orderedList':
      chain.toggleOrderedList().run();
      break;
    case 'blockquote':
      chain.toggleBlockquote().run();
      break;
  }
}

export function computeActiveMarks(editor: Editor): Set<string> {
  const active = new Set<string>();
  if (editor.isActive('bold')) active.add('bold');
  if (editor.isActive('italic')) active.add('italic');
  if (editor.isActive('heading', { level: 2 })) active.add('heading2');
  if (editor.isActive('heading', { level: 3 })) active.add('heading3');
  if (editor.isActive('bulletList')) active.add('bulletList');
  if (editor.isActive('orderedList')) active.add('orderedList');
  if (editor.isActive('blockquote')) active.add('blockquote');
  return active;
}
