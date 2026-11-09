# ShiftSathi — Solution Pitch

## Problem
Factory workers struggle to file structured incident reports: typing is slow, details are missed, and reports mix Hindi/English/Hinglish. Supervisors spend time interpreting unstructured notes.

## Solution
ShiftSathi is a voice-first industrial incident assistant. A worker speaks naturally; Gnani Prisma transcribes (Hindi/English/Hinglish); an LLM extracts structured fields (machine, area, category, severity, readings, actions); missing fields trigger contextual follow-up questions; Gnani Timbre reads back a confirmation; the worker confirms or corrects; the incident is stored and surfaced on a supervisor dashboard with shift handover summaries.

## Why it matters
- Faster, accessible reporting for non-typing workers
- Structured, auditable incident records
- Human approval before final submission
- Evidence-backed shift intelligence (recurring machines, pending actions)

## Tech
React + Vite + Tailwind | FastAPI + SQLAlchemy + SQLite | Gnani Prisma (STT) + Gnani Timbre (TTS) | OpenAI-compatible LLM with heuristic fallback

## Status
- 50-scenario eval: 91.3% field accuracy (heuristic fallback)
- 13 backend tests pass; frontend builds
- Live Gnani API verification pending (no credentials in this environment)
- Not deployed to cloud; Docker config provided

## Author
Anika (@anikak206) — individual contribution, Gnani AI Great Indian AI Internship Challenge 2026.
EOF