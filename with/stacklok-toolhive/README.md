# Stacklok ToolHive

Run [ToolHive](https://github.com/stacklok/toolhive), Stacklok's platform for
running and managing MCP servers, inside a Ringleader workstation, and give a
coding agent tools it did not have before.

Ringleader is not affiliated with or endorsed by Stacklok.

## Why these fit together

ToolHive gives each MCP server its own container, with ingress, egress and DNS
around it, so an agent's tools run isolated from each other and from the host.
That is a strong default, and it is the reason a container runtime is part of
the picture.

Ringleader's job here is the easy half: the runtime, `thv` and the agent are all
declared in one file, so applying it gives you a box where the three are present
and already know about each other. The same box, every time, for everyone.

The more interesting consequence: **the MCP servers an agent can reach become
part of the environment definition**, rather than something each person wires up
on their own laptop. What tools your agents have stops being a per-developer
accident and becomes something you can review in a pull request.

One caveat, since it surprises people. If your agent signs in with an account that
has claude.ai connectors attached, those connectors come with the account, not the
machine, so `claude mcp list` will show them here alongside the server you declared.
Nothing leaked out of your laptop and no product is misbehaving: the connectors are
account-level by design, and you would see the same list signing in on any machine
anywhere. It does mean the manifest describes the servers *this box* provides rather
than the complete set the agent can reach.

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

## Run it in the cloud

`toolhive-box-gcp.yaml` is this same box on a GCP VM. Compare the two files and
the entire difference is placement: a namespace that is not `local`,
`requirements: ["provider:gcp"]`, a `providerConfig` for sizing, and a `ttl` so a
billing VM cannot outlive your attention. The container runtime, `thv`, the MCP
server and the agent are identical, which is the argument for describing an
environment rather than a machine.

It needs a namespace of your own, a CloudIdentity for gcp in it, and the label
that CloudIdentity selects on. That label is the one thing you cannot copy from
us: it is how the project and zone reach your VM, and if nothing matches you get
`providerConfig.gcp requires both project and zone`, which names the symptom
rather than the cause. The manifest says how to find yours.

Because those are edits you make before applying, download this one rather than
running it from a link:

```bash
curl -O https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/stacklok-toolhive/toolhive-box-gcp.yaml
# edit `your-namespace` and the CloudIdentity label in all three documents, then:
rl apply -f toolhive-box-gcp.yaml
rl workstation wait toolhive-box --for condition=Configured --timeout 20m -n your-namespace
rl shell toolhive-box -n your-namespace
```

Every step above is unchanged from there: the registry, the MCP server, the agent
and the sign-in all behave the same.

**A cloud VM bills until it is deleted**, and this box is the most expensive in the
repository, since it carries a container runtime and pulls images. The manifest's
`ttl: 8h` / `ttlAction: delete` is the backstop that runs even if you close your
laptop and forget; deleting it yourself is faster and cheaper:

```bash
rl workstation delete -f toolhive-box-gcp.yaml -y
```

If you have not onboarded a cloud yet, start with the
[GCP guide](https://docs.ringleader.dev/cloud-onboarding/gcp/). Azure and AWS are
the same file with a different `provider:` and config block.

## Going further

Steps 2 and 3 are runtime commands, so they are not in the manifest. They could
be: a `scripts` step with `phase: user` can run `thv run` and
`thv client register claude-code` at provision time, so the box comes up with the
MCP server already wired to the agent and nobody has to remember the sequence.

That is the version to build for a team, the difference between "here is a
box, now configure your tools" and "here is your environment, the tools are
already there." It is left out here so the moving parts stay visible.

## More on ToolHive

This example only scratches it. Stacklok's own
[CLI quickstart](https://docs.stacklok.com/toolhive/tutorials/quickstart-cli) and
[install guide](https://docs.stacklok.com/toolhive/guides-cli/install) go further,
including the Kubernetes operator and the permission profiles that govern what
each MCP server may reach.
