# Stacklok ToolHive

Run [ToolHive](https://github.com/stacklok/toolhive), Stacklok's platform for
running and managing MCP servers, inside a Ringleader workstation, and give a
coding agent tools it did not have before.

Ringleader is not affiliated with or endorsed by Stacklok.

## Why these fit together

ToolHive runs each MCP server in a container, so it needs a container runtime.
That is the dependency that makes environments annoying to share:
"install Docker first" is where a lot of onboarding documents start, and where a
lot of them go wrong.

Here the runtime, the gateway, and the agent are all declared in one file. Apply
it and you have a box where all three are present and already know about each
other. The same box, every time, for everyone.

The more interesting consequence: **the MCP servers an agent can reach become
part of the environment definition**, rather than something each person wires up
on their own laptop. What tools your agents have stops being a per-developer
accident and becomes something you can review in a pull request.

## Run it

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/stacklok-toolhive/toolhive-box.yaml
rl workstation wait toolhive-box --for condition=Configured --timeout 20m -n local
rl shell toolhive-box -n local
```

Everything below happens **inside** the workstation.

### 1. See what is available

```bash
thv registry list
```

ToolHive ships a registry of MCP servers. We will use `toolhive-doc-mcp`, which
lets an agent search ToolHive's own documentation. It needs no API keys, so it
works immediately.

```bash
thv registry info toolhive-doc-mcp
```

### 2. Run the MCP server

```bash
thv run toolhive-doc-mcp
thv list
```

`thv run` pulls the image, starts the server as a detached process, and returns
before it is fully up, so give it a few seconds before `thv list` shows it as
`running`. Checking immediately reports `No MCP servers found`.

This is where the `docker` devtool earns its place. `docker ps` shows **four**
containers, not one: the MCP server itself plus ingress, egress and DNS
sidecars that ToolHive puts around it.

### 3. Point the agent at it

```bash
thv client register claude-code    # or: thv client register codex
thv client status
```

`thv client status` lists every client ToolHive knows how to configure, with
which ones it found installed. Register the one matching the agent you put in
the manifest.

That writes the MCP configuration Claude Code reads, so the agent picks the
server up without you editing JSON by hand.

### 4. Ask it something it could not answer before

```bash
claude
```

The first run asks you to sign in, and the page opens on **your** machine rather
than printing a URL the VM cannot open. That is the `passthrough-www-browser`
devtool and the `LocalBinding` in the manifest doing their job.

Then ask:

```
What is a Virtual MCP Server and how do I use it with ToolHive?
```

Claude Code answers by **searching ToolHive's documentation through the MCP
server** rather than from memory. That round trip runs from the agent to the MCP
server to a container, all inside a workstation you declared.

### 5. Stop it when you are done

```bash
thv stop toolhive-doc-mcp
```

## Clean up

From your own machine, not inside the box:

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/stacklok-toolhive/toolhive-box.yaml -y
```

Passing the manifest removes everything it declares: the workstation, the
WorkstationConfig and the LocalBinding. This is the most expensive box in the
repo to leave running, since it carries a container runtime and several pulled
images.

## What the manifest does

| | |
| -- | -- |
| `image` | Debian 13, pinned because the install script is Debian-specific |
| `docker` devtool | the container runtime ToolHive requires |
| `nodejs` + `claude-code` devtools | the agent that consumes the MCP servers |
| `passthrough-www-browser` devtool | lets the agent's sign-in open on your machine |
| `scripts` step | installs the `thv` binary from the official release archive |
| `LocalBinding` | carries VM ports back, and lets the VM ask your host to open a URL |
| `providerConfig` | 8 GiB / 4 CPU, since ToolHive pulls and runs container images |

## Three choices in the manifest

**Release archive, not Homebrew.** Stacklok's docs lead with `brew install thv`,
which is right for a Mac and wrong for a Debian workstation. The script pulls the
official release tarball for the box's architecture instead, which is also why
the manifest pins `image` to Debian 13: `dpkg --print-architecture` only exists
on Debian and Ubuntu, so relying on whatever the provider defaults to would make
this example quietly provider-specific.

**Sign-in is declared, not assumed.** Any example that expects you to
authenticate something *inside* the box needs two things the box does not get by
default: the `passthrough-www-browser` devtool, so an in-VM "open this link"
becomes a request your host can act on, and a `LocalBinding` whose `autoForward`
carries the callback port back and whose `urlForward` actually launches the page.
Leave either out and `claude` prints a URL you have to copy across by hand.

**The version is pinned.** `THV_VERSION` is explicit rather than tracking
`latest`, because a reproducible environment is the entire point of describing it
as code, and an example that silently changed under you would undercut its own
argument. Bump it deliberately:

```yaml
env:
  THV_VERSION: "0.42.1"   # https://github.com/stacklok/toolhive/releases
```

The script is a no-op when that version is already installed, so re-applying is
cheap and only does work when you change the pin.

## Going further

Steps 2 and 3 are runtime commands, so they are not in the manifest. They could
be: a `scripts` step with `phase: user` can run `thv run` and
`thv client register claude-code` at provision time, so the box comes up with the
MCP server already wired to the agent and nobody has to remember the sequence.

That is the version to build for a team, the difference between "here is a
box, now configure your tools" and "here is your environment, the tools are
already there." It is left out here so the moving parts stay visible.

## Status

**Verified end to end**, by applying this manifest to a fresh workstation and
following every step above: `thv` installs at the pinned **v0.42.1** for the
box's architecture, `docker ps` works without `sudo`, `toolhive-doc-mcp` runs as
a real container, `thv client register claude-code` writes the config Claude Code
reads, `claude mcp list` reports the server **Connected**, and Claude answered the
Virtual MCP Server question through the MCP server rather than from memory.

Written against ToolHive's
[documented install method](https://docs.stacklok.com/toolhive/guides-cli/install)
and [CLI quickstart](https://docs.stacklok.com/toolhive/tutorials/quickstart-cli).
Pinned at v0.42.1, current as of August 2026.
