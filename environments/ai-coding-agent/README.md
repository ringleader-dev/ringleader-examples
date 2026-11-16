# AI coding agent

A workstation of its own for a coding agent. It gets a real machine with real
tools, and **not your laptop**: none of your other repositories, none of the
credentials on your disk, nothing on that machine you did not put in this file.
It reaches only the hosts the file lists, and it deletes itself, disk included,
a week after you create it.

What the box cannot bound is the account the agent signs in with. claude.ai
connectors are attached to the account rather than the machine. Claude Code
reaches them through `mcp-proxy.anthropic.com`, which this file does not list,
so add that host if you want the agent to use them.

## Run it

First, tell your machine to ask you before it opens a link from a workstation.
Without this, it opens every link a workstation sends. The command needs `rl`
0.52.4 or later:

```bash
rl urlopenrules default queue
```

Then, on a Mac:

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/environments/ai-coding-agent/agent-box.yaml
rl workstation wait agent-box --for condition=Configured --timeout 15m -n local
rl shell agent-box -n local
```

On Windows, save [`agent-box.yaml`](agent-box.yaml), change `provider: vz` to
`provider: hcs`, and apply your copy. On Linux, use `provider: qemu`.

Then, inside the workstation:

```bash
claude
```

When Claude Code asks you to sign in, list the links waiting on your own machine,
then approve the sign-in link by its ID within 10 minutes. Your machine opens it
in your browser:

```bash
rl urlopenrules history --pending
rl urlopenrules approve <id>
```

## How the browser sign-in works

Claude Code runs in the VM, and you sign in from the browser on your own machine.
Three parts make that work:

- The `passthrough-www-browser` devtool stands in for the browser inside the VM.
  When Claude Code opens its sign-in link, the devtool hands the link to
  Ringleader instead. It is **opt-in**, never installed by default.
- **`urlForward`** in the `LocalBinding` sends that link to your machine, which
  records it. `rl urlopenrules default queue` makes your machine hold each link
  until you approve it, so a program in the workstation cannot make your browser
  load a page on its own. `rl urlopenrules history` lists every link and what
  became of it.
- **`autoForward`** forwards every port the VM listens on to your machine, not
  only the sign-in's. Claude Code waits for the end of the sign-in on a port it
  picks at random, so the sign-in needs it.

Claude Code also prints a sign-in link of its own. If you open that one instead,
the sign-in page shows a code, which you paste where Claude Code asks for it.

## What the file allows

The `Workstation` names its provider, because Ringleader enforces an egress
policy only on a provider it knows can hold it. Its `egress` block lists the
hosts the box may reach: Debian's package mirror, the Node.js and npm package
hosts, and Anthropic's hosts for the model and the sign-in. Every other
connection is refused.

`lifecycle.ttl: 7d` deletes the workstation and its disk a week after you
create it. Push your work before then, or change the value and apply the file
again.

## Why run an agent this way

The usual alternative is running the agent directly on your laptop, where it has
whatever access you have. That is fine right up until it is not.

Here the blast radius is the file you wrote. The agent gets `git`, `ripgrep`,
Node and the browser passthrough, on Debian 13, and nothing you did not declare.
If it does something surprising, it does it somewhere you can delete:

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/environments/ai-coding-agent/agent-box.yaml -y
```

Pass the manifest, not the workstation name: this file declares a
WorkstationConfig and a LocalBinding as well, and deleting the machine alone
would leave both behind.

And because the environment is a manifest, a teammate applying the same file
gets the same tools and the same boundaries. Note that it does not yet get the
same *versions*: nothing here is pinned except the image, so `nodejs` and
`claude-code` track whatever the registry installs today. Pin them when that
matters to you:

```yaml
devtools:
  - name: nodejs
    version: "20"
```

## Adapting it

- **A different agent:** swap the `claude-code` devtool for `codex`, and replace
  the two Anthropic hosts in `egress` with the hosts Codex reaches. To find them,
  apply the file with `enforcement: audit` first, let the agent work, and run
  `rl workstation egress agent-box -n local --suggest`. For an agent that is not
  in the registry but ships an npm CLI, put it in `packages` as
  `{type: npm, name: ...}` instead.
- **More tools:** add to `packages` (system or npm) or `devtools`, and add the
  hosts they download from to `egress`.
- **A cloud machine instead of local:** drop the `namespace: local` and replace
  `provider: vz` with your cloud's provider. On a cloud, a `strict` list of
  hosts needs an Edge, as
  [Restricting outbound connections](https://docs.ringleader.dev/reference/workstationconfig/#restricting-outbound-connections)
  explains.

[Harden a local workstation](https://docs.ringleader.dev/security/hardening-local-workstations/)
explains each setting, and adds GitHub access and a model key that never enter
the workstation.
