# Front-end stack

A machine set up for front-end work, with a coding agent already installed:
Node.js 24, Playwright with Chromium, the GitHub CLI, git and ripgrep, on
Debian 13. It runs as a virtual machine on your own computer, so the agent works
inside it and not on your laptop.

Each file below is the same stack with a different agent. Pick the one you use.

| Agent | File | Start it with |
| -- | -- | -- |
| Claude Code | [`frontend-claude-code.yaml`](frontend-claude-code.yaml) | `claude` |
| Codex | [`frontend-codex.yaml`](frontend-codex.yaml) | `codex` |
| Cursor CLI | [`frontend-cursor.yaml`](frontend-cursor.yaml) | `cursor-agent` |
| Antigravity CLI | [`frontend-antigravity.yaml`](frontend-antigravity.yaml) | `agy` |

## Run it

Paste the three lines for your agent into a terminal. The first creates the
workstation, the second waits until every tool is installed, and the third opens
a shell inside it. Setup takes several minutes, and longer the first time, while
the base image downloads.

Claude Code:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-claude-code.yaml
rl workstation wait frontend-claude-code --for condition=Configured --timeout 20m -n local
rl shell frontend-claude-code -n local
```

Codex:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-codex.yaml
rl workstation wait frontend-codex --for condition=Configured --timeout 20m -n local
rl shell frontend-codex -n local
```

Cursor CLI:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-cursor.yaml
rl workstation wait frontend-cursor --for condition=Configured --timeout 20m -n local
rl shell frontend-cursor -n local
```

Antigravity CLI:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-antigravity.yaml
rl workstation wait frontend-antigravity --for condition=Configured --timeout 20m -n local
rl shell frontend-antigravity -n local
```

Then start your agent with the command from the table. When it asks you to sign
in, the sign-in page opens in the browser on your own machine.

If a ready machine is all you wanted, you are done. The rest of this page covers
the starter app, changing the stack, running it in a cloud, and removing it.

## Add the starter app

[`starter-app.yaml`](starter-app.yaml) adds a React and TypeScript app, made
from Vite's own template, so you and your agent have a project to work on from
the start. Add it as a second `-f` on the first line of your agent's block:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-claude-code.yaml -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/starter-app.yaml
```

Wait and open a shell as before, then start the dev server:

```bash
cd ~/app
npm run dev
```

Open <http://localhost:5173> in your browser. In a second terminal, open another
shell on the same workstation, `cd ~/app`, start your agent, and ask it for a
change, such as "add a dark mode toggle". The page updates each time the agent
saves a file.

The starter attaches to every workstation labeled `stack: frontend`, so you can
also apply it on its own to a front-end workstation you already have. It creates
`~/app` once and never overwrites it.

The dev server listens on `127.0.0.1` inside the workstation, set in
`vite.config.ts`, because that is the address the forward to your machine
connects to. If you bring your own Vite project, start it with
`npm run dev -- --host 127.0.0.1`, or set `server.host` the same way.

## What each agent comes with

The four files differ only in the agent's line, the workstation's name, and its
`agent` label. Each agent then starts with these defaults:

- Claude Code opens without permission prompts, because the workstation is the
  boundary those prompts protect, and its background auto-updater is off. A
  [`claude-code` toolconfig](https://docs.ringleader.dev/reference/toolconfigs/claude-code/)
  changes either one.
- Codex keeps its own defaults.
- The Cursor CLI installs a specific Cursor release.
- The Antigravity CLI installs a specific release, then updates itself as you
  use it.

## Make it yours

Fork this repository, or copy a file, and edit it. Each tool is one line:

- Add a curated tool to `devtools`, such as `- name: docker` for containers or
  `- name: python`. The
  [devtools reference](https://docs.ringleader.dev/reference/devtools/) lists
  every one.
- Add an operating-system package to `packages` by name, or an npm package as
  `{type: npm, name: ...}`.

Then apply your copy from its own raw URL, and hand that URL to your team so
everyone gets the same machine. The starter app shows a second way to add
things: a separate file that adds to every workstation carrying a label, so one
set of additions can be shared across several stacks.

## Versions

The base image is pinned to Debian 13 and Node.js to major version 24. Claude
Code, Codex and Playwright install their latest release when the workstation is
set up, because coding agents release often and you will usually want the newest
one. The Cursor CLI and the Antigravity CLI install the release Ringleader
currently pins. To pin any tool, add `version:` to its entry; each tool's page in
the devtools reference says what a version means for that tool.

The starter app pins create-vite 9.2.1. The app's own dependencies are resolved
when the app is created, and `package-lock.json` records them.

## Run it in a cloud

These files run on your own machine, in the reserved `local` namespace, with no
account needed. To run the same stack on a cloud VM, change four things in your
copy:

1. Remove `namespace: local`, so the workstation lands in your own namespace.
2. Add the label your organization uses to pick its cloud account, such as
   `cloud: gcp`.
3. Add `requirements: ["provider:gcp"]` (or `aws`, or `azure`).
4. Replace `providerConfig` with the cloud's own sizing, and add an idle policy
   so the VM stops when nobody is using it.

The [dltHub GCP example](../../with/dlthub/dlt-box-gcp.yaml) makes exactly these
changes, and [cloud onboarding](https://docs.ringleader.dev/cloud-onboarding/)
covers connecting your cloud account, once per organization.

## Clean up

Pass the same files to `delete` that you passed to `apply`:

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/frontend-claude-code.yaml -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/stacks/frontend/starter-app.yaml -y
```

Leave out `starter-app.yaml` if you did not apply it. If you did, include it:
otherwise its configuration stays behind and attaches itself to the next
front-end workstation you create.
