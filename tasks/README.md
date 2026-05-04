# Tasks Prompt Conventions

Future prompt files should use simple sequence numbers under `tasks/prompts/`:

- `tasks/prompts/001_<short_topic>.md`
- `tasks/prompts/002_<short_topic>.md`
- `tasks/prompts/003_<short_topic>.md`

Rules:
- Use 3-digit sequential IDs.
- Use short snake_case topic names.
- Do not use large phase ranges for small bugfixes.
- Keep only currently useful prompts.
- Delete or archive stale prompts after work is completed.
- Roadmaps may stay in `tasks/` root with descriptive names.

Current retained prompt:
- `tasks/prompts/001_eurusd_gui_sample_index_state_fix.md`
