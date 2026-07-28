import { WritingStyle } from '../../../core/models/content';

export interface ScaffoldSection {
  /** Exact text after '## ' — doubles as the parse-back-out key when
   *  resuming a draft (see section-markdown.ts). Treat as immutable once
   *  shipped: renaming loses the ability to re-recognize old headings
   *  (harmless — falls back to blank mode, see resolveEditorMode). */
  id: string;
  /** Short tag, always visible near the section, never disappears —
   *  unlike the placeholder ghost text below, which vanishes on typing. */
  label: string;
  /** Longer question shown on first reveal; also doubles as this
   *  section's TipTap Placeholder ghost text. */
  prompt: string;
  /** Full example sentence/paragraph for the tap-for-example (💡) reveal. */
  example: string;
}

export interface StyleScaffold {
  value: WritingStyle;
  label: string;
  description: string;
  /** null = no scaffold at all (blank style): single flat editor. */
  sections: ScaffoldSection[] | null;
}

export const STYLE_SCAFFOLDS: Record<WritingStyle, StyleScaffold> = {
  fairy_tale: {
    value: 'fairy_tale',
    label: 'Fairy Tale',
    description: 'Once upon a time...',
    sections: [
      {
        id: 'Once upon a time...',
        label: '🌱 The Beginning',
        prompt: "Set the scene — where are we, and who's in it?",
        example:
          'Once upon a time, in a quiet village at the edge of a dark forest, there lived a girl who could talk to owls.',
      },
      {
        id: 'One day...',
        label: '⚡ The Event',
        prompt: 'What happens that changes everything?',
        example: 'One day, an owl landed on her windowsill carrying a message no one else could read.',
      },
      {
        id: 'So they decided to...',
        label: '🏃 The Action',
        prompt: 'What do they do about it?',
        example: 'So they decided to follow the owl into the forest, even though everyone said it was forbidden.',
      },
      {
        id: 'In the end...',
        label: '🏁 The Ending',
        prompt: 'How does it all turn out?',
        example:
          "In the end, she discovered the forest wasn't dangerous at all — it just needed someone willing to listen.",
      },
    ],
  },
  news_report: {
    value: 'news_report',
    label: 'News Report',
    description: 'Headline, lead, body, quote.',
    sections: [
      {
        id: 'Headline',
        label: '📰 Headline',
        prompt: 'Sum up the story in one punchy line.',
        example: 'Local Kid Discovers Owls Can Talk — Village Stunned',
      },
      {
        id: 'Lead',
        label: '🔍 The Lead',
        prompt: 'Who, what, when, where — the basics, fast.',
        example: 'Yesterday afternoon, a nine-year-old from the village reported speaking with a forest owl for the first time.',
      },
      {
        id: 'Body',
        label: '📝 The Details',
        prompt: 'Now tell the full story.',
        example: 'Witnesses say the owl appeared just after 3pm and repeated the same three words for several minutes.',
      },
      {
        id: 'Quote',
        label: '💬 Quote Box',
        prompt: 'What did someone say about it? Write it like a quote.',
        example: '"I always knew something was out there," said her neighbor. "I just never expected an owl."',
      },
    ],
  },
  diary_entry: {
    value: 'diary_entry',
    label: 'Diary Entry',
    description: 'Dear Diary...',
    sections: [
      {
        id: 'Dear Diary...',
        label: '📔 Opening',
        prompt: "Start the way you always start — what's on your mind?",
        example: "Dear Diary, today was the strangest day I've had in a long time.",
      },
      {
        id: 'Today I learned...',
        label: '💭 What Happened',
        prompt: "Tell it the way you'd tell yourself — no need to be formal.",
        example: 'Today I learned that owls can apparently understand more than people give them credit for.',
      },
      {
        id: 'Tomorrow I want to find out...',
        label: '🌙 Closing',
        prompt: 'What are you still wondering about?',
        example: 'Tomorrow I want to find out if the owl will come back, and whether it has a name.',
      },
    ],
  },
  letter: {
    value: 'letter',
    label: 'Letter',
    description: 'Dear someone...',
    sections: [
      {
        id: 'Dear...',
        label: '✉️ Greeting',
        prompt: 'Who are you writing to? Fill in their name.',
        example: 'Dear Grandma,',
      },
      {
        id: "I'm writing because...",
        label: "🖊️ Why I'm Writing",
        prompt: 'What made you want to write this letter?',
        example: "I'm writing because something happened this week that I think you'd love to hear about.",
      },
      {
        id: "Here's what happened...",
        label: '⭐ The Interesting Part',
        prompt: 'Tell them the good part.',
        example: "Here's what happened: I found an owl that seemed to understand exactly what I was saying to it.",
      },
      {
        id: 'Write back and tell me...',
        label: '❓ Sign-off',
        prompt: 'End with your name and a question for them.',
        example: 'Write back and tell me — have you ever seen anything like that? From, Neo',
      },
    ],
  },
  how_to: {
    value: 'how_to',
    label: 'How-To / Instructions',
    description: "What you'll need, then the steps.",
    sections: [
      {
        id: "What you'll need",
        label: "🧰 What You'll Need",
        prompt: 'List everything someone needs before they start.',
        example: 'A quiet spot outside, some patience, and maybe a snack for the owl.',
      },
      {
        id: 'Steps',
        label: '🔢 The Steps',
        prompt: 'Walk them through it, one step at a time — a numbered list works great.',
        example: '1. Sit somewhere quiet at dusk.\n2. Stay still and listen.\n3. Wait for a reply.',
      },
      {
        id: 'Tip',
        label: '⚠️ Tip or Warning',
        prompt: "What's one thing that would've helped you know beforehand?",
        example: "Don't get too close too fast — owls startle easily, just like people do.",
      },
    ],
  },
  blank: {
    value: 'blank',
    label: 'Write from scratch',
    description: 'A blank page — write it your own way.',
    sections: null,
  },
};
