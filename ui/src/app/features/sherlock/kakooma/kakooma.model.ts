export type KakoomaOperation = 'add' | 'multiply';

export interface KakoomaPuzzle {
  numbers: number[];
  answerIndex: number;
  operation: KakoomaOperation;
}
