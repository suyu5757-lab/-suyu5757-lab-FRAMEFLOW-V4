---
name: gpt-image-2-style-library
version: 1.0.4
description: Choose GPT-Image2 visual styles and industrial prompt templates from the awesome-gpt-image-2 style library.
---

# GPT-Image2 Style Library

Use this skill to turn an image-generation intent into a production-ready prompt using the versioned awesome-gpt-image-2 style library catalog.

## Reference

Read `style-library-1.0.4.md` before choosing a template, visual style, scene tag, or example case. The reference is the versioned runtime snapshot of the upstream library.

## Workflow

1. Detect the user's language and answer in that language.
2. Identify the target output: product, poster, UI, infographic, brand, photo, illustration, character, scene, history, document, or special task.
3. Match the request in this order: template category, visual style tag, scene tag, then nearest example cases.
4. Choose the strongest matching template; when the application exposes template override, honor that override.
5. Build the image prompt with subject/task, composition/layout, visual style/materials, text/labels, aspect ratio/output format, and concrete constraints/negative details.

## Output Defaults

- Produce a copyable image-generation prompt first.
- Keep constraints concrete: exact visible text, aspect ratio, readable labels, layout hierarchy, and avoided artifacts.
- Use the user's language for the final prompt unless the user asks for another language.
- Template IDs, tags, example IDs, QA diagnostics, provider routing, workflow state, and asset IDs are internal metadata and must not be copied into the image prompt.

## Runtime Boundary

The application may add only its documented production invariants: asset canvas ratio, image output format, project-ratio inheritance for fusion/shot outputs, and the character horizontal four-zone reference-sheet layout. Retired prompt contracts, legacy field concatenation, provider pixel-size mappings, and image execution instructions are not visual prompt rules.
