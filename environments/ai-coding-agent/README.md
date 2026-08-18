# AI coding agent

A governed home for a coding agent. It gets a real machine with real tools,
and **not your laptop**: none of your other repositories, none of the
credentials on your disk, nothing on that machine you did not put in this file.

What the box cannot bound is the account the agent signs in with. If yours has
claude.ai connectors attached, they come with the account rather than the
machine, and the agent can reach them from in here too.

## Run it

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/environments/ai-coding-agent/agent-box.yaml
rl workstation wait agent-box --for condition=Configured --timeout 15m -n local
rl shell agent-box -n local
```

Then, inside the workstation:

```bash
claude
```

Sign-in opens in **your own browser**, on your own machine, even though the
agent is running inside the VM.

## How the browser sign-in works

This is the part people expect to be painful. Two halves do it, both in the
`LocalBinding`:

- **`autoForward`** carries the VM's listening ports back to your device, so the
  OAuth callback can actually land on the login server running inside the VM.
- **`urlForward`** lets the VM ask your host to open a URL, and `open: true`
  actually launches it rather than only logging it.

Plus the `passthrough-www-browser` devtool inside the box, which is what turns an
in-VM "open this link" into a request your host can act on. It is **opt-in** by
design. Nothing reaches out of the workstation unless you say so.

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

- **A different agent:** swap the `claude-code` devtool for `codex`. Both are in
  the registry, and it is the only agent-specific line in the manifest. Node,
  the browser passthrough and the LocalBinding are what *any* agent needs. For
  an agent that is not in the registry but ships an npm CLI, put it in
  `packages` as `{type: npm, name: ...}` instead.
- **More tools:** add to `packages` (system or npm) or `devtools`.
- **A cloud machine instead of local:** drop the `namespace: local` and let
  Ringleader place it, or pin a provider on the workstation spec.
