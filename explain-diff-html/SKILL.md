---
name: explain-diff-html
description: "Use when the user asks for a rich explanation of a code change, diff, branch, or PR. Produces a self-contained HTML file plus a published Artifact."
---

# Explain Diff

Please make me a rich, interactive explanation of the specified code change.

It should have these sections:

*   Background: Explain the existing system relevant to this change. (You should broadly explore surrounding code for this.) We don't know how much the reader already knows, so include a deep background for beginners (note that it can be skipped if the reader is already familiar), and then a more narrow background directly relevant to the change.
*   Prerequisite: If this change introduce new concept or terminology, provide 1-2 related resources for each, so that reader can understand the explanation better with prerequisite knowledge.
*   Intuition: Explain the core intuition for the code change. The focus here is to explain the essence, not the full details. Use concrete examples with toy data. Use figures and diagrams liberally.
*   Code: Do a high-level walkthrough of the changes to the code. Group/order the changes in an understandable way.
*   Quiz: Come up with five questions that test the reader's knowledge of this PR. This should be medium difficulty, difficult enough that you actually need to understand the substance of the PR to answer them, but not gotchas. The goal is to help the reader make sure that they've actually understood. These should be presented as interactive multiple-choice questions, and when the user clicks, it tells them whether they were correct and gives feedback.
*   Language: Use Traditional Chinese for response.

Format:

*   Output a single self-contained HTML file which includes CSS and JavaScript. Make the whole thing one long page with section headers and a table of contents. Don't use tabs for the top-level structure. Basic responsive styling so you can view it on a phone is nice too. Put the file in `/tmp`, outside the code repo, and make sure the filename always starts with today's date in `YYYY-MM-DD-` format, because it helps keep the files time-sorted and out of version control. For example: /tmp/2026-01-12-explanation-.html
*   Also publish that same explanation as an **Artifact**, so the reader can open it from any device and share the link. Call the `Artifact` tool with the file path (read the `artifact-design` skill first — that tool requires it). The Artifact runtime wraps your content in its own `<!doctype html><head>…</head><body>`, so the file you publish must **not** contain `<!DOCTYPE>`, `<html>`, `<head>` or `<body>` tags — put `<title>` and `<style>` at the top and the content below. Keep everything inline: external stylesheets are blocked by the page's CSP, and scripts may only come from `cdnjs.cloudflare.com` (the inline quiz JavaScript works fine). Easiest flow is to write the body-only version first, publish it, then produce the local dated `.html` in `/tmp` by wrapping that same content in a `<!DOCTYPE html><html><head>…` skeleton. Give a `favicon` emoji and a one-line `description` on the first publish, and when you're done report both the local path and the Artifact URL.
*   Please write with the clarity and flow of Martin Kleppmann, making it engaging and written in classic style. Transitions between sections should be smooth.
*   Some tips on diagrams. Ideally, you should pick a small number of diagram families that can be reused throughout the explanation to explain various cases. Some useful kinds of diagrams:
    *   A very simplified version of the UI that the user sees in the app, to explain UI changes.
    *   A system diagram showing data flow or communication between components. Make sure to include example data here!
*   Don't use ASCII diagrams. Always use simple HTML designs for your diagrams, HTML lists for lists of things, etc.
    *   For code blocks, always use `<pre>` tags. If you use a custom styled div instead, it **must** have `white-space: pre-wrap` in its CSS, or the browser will collapse all newlines into a single line. Before saving the file, scan each code block in the HTML source and confirm its CSS includes `white-space: pre` or `pre-wrap`.
*   Use callouts for key concepts or definitions, important edge cases, etc.
