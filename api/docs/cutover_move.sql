-- Thinkingify cutover: move all objects from public schema into thinkingify schema.
-- Run on the OLD prod DB (direct 5432 connection) as a single transaction.
BEGIN;
CREATE SCHEMA IF NOT EXISTS thinkingify;
-- Enum types:
ALTER TYPE public.accounttype SET SCHEMA thinkingify;
ALTER TYPE public.brothersessionstatus SET SCHEMA thinkingify;
ALTER TYPE public.brothertierstatus SET SCHEMA thinkingify;
ALTER TYPE public.companionmessagerole SET SCHEMA thinkingify;
ALTER TYPE public.contentstatus SET SCHEMA thinkingify;
ALTER TYPE public.familylinkstatus SET SCHEMA thinkingify;
ALTER TYPE public.grammarflagstatus SET SCHEMA thinkingify;
ALTER TYPE public.mathanswerkind SET SCHEMA thinkingify;
ALTER TYPE public.mathcoachmessagerole SET SCHEMA thinkingify;
ALTER TYPE public.mathproblemstatus SET SCHEMA thinkingify;
ALTER TYPE public.puzzletier SET SCHEMA thinkingify;
ALTER TYPE public.sentenceframingflagstatus SET SCHEMA thinkingify;
ALTER TYPE public.spellingerrortype SET SCHEMA thinkingify;
ALTER TYPE public.spellingflagstatus SET SCHEMA thinkingify;
ALTER TYPE public.topicstatus SET SCHEMA thinkingify;
ALTER TYPE public.userrole SET SCHEMA thinkingify;
-- Tables (alembic_version last):
ALTER TABLE public.brother_attempts SET SCHEMA thinkingify;
ALTER TABLE public.brother_sessions SET SCHEMA thinkingify;
ALTER TABLE public.brother_tier_progress SET SCHEMA thinkingify;
ALTER TABLE public.companion_messages SET SCHEMA thinkingify;
ALTER TABLE public.content SET SCHEMA thinkingify;
ALTER TABLE public.family_links SET SCHEMA thinkingify;
ALTER TABLE public.grammar_flags SET SCHEMA thinkingify;
ALTER TABLE public.math_attempts SET SCHEMA thinkingify;
ALTER TABLE public.math_coach_messages SET SCHEMA thinkingify;
ALTER TABLE public.math_problems SET SCHEMA thinkingify;
ALTER TABLE public.notes SET SCHEMA thinkingify;
ALTER TABLE public.parent_reports SET SCHEMA thinkingify;
ALTER TABLE public.puzzle_attempts SET SCHEMA thinkingify;
ALTER TABLE public.puzzle_game_progress SET SCHEMA thinkingify;
ALTER TABLE public.sentence_framing_flags SET SCHEMA thinkingify;
ALTER TABLE public.spelling_flags SET SCHEMA thinkingify;
ALTER TABLE public.topics SET SCHEMA thinkingify;
ALTER TABLE public.users SET SCHEMA thinkingify;
ALTER TABLE public.alembic_version SET SCHEMA thinkingify;
COMMIT;
