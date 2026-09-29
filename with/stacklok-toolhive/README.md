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
the entire difference is placement: no namespace, `requirements: ["provider:gcp"]`,
a `providerConfig` for the machine size and disk, and a `lifecycle` block that
powers the VM down once nobody is using it. The container runtime, `thv`, the MCP
server and the agent are identical, which is the argument for describing an
environment rather than a machine.

It applies from a link, like the local one. Two things have to be true first: you
are signed in to Ringleader (`rl auth status` says so), and your namespace has a
CloudIdentity for GCP, which is what [onboarding Google
Cloud](https://docs.ringleader.dev/cloud-onboarding/gcp/) creates. Nothing in the
file names a namespace. The box lands in the one your login gave you, and
`rl namespace use` with no argument prints which that is.

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/stacklok-toolhive/toolhive-box-gcp.yaml
rl workstation wait toolhive-box --for condition=Configured --timeout 20m
rl shell toolhive-box
```

Every step above is unchanged from there: the registry, the MCP server, the agent
and the sign-in all behave the same.

**If the box stops with the Ready reason `CloudIdentityNotMatched`, the label did
not match.** A CloudIdentity picks the workstations it applies to by label, and this
file carries `cloud: gcp`, the label the onboarding guide sets up. If your
administrator chose a different one, `rl workstation describe toolhive-box` says
so and `rl get cloudidentity -o yaml` shows the label under
`spec.selector.matchLabels`. Put that label on the Workstation in a copy of the
file, and apply the copy. The [dltHub example](../dlthub/#taking-it-further) shows
the three commands.

**A cloud VM bills while it runs, and its disk bills until you delete it** — and this
box is the most expensive in the repository, since it carries a container runtime and
pulls images. The control that does the work is `lifecycle.idle`: two hours in which
nothing holds an SSH session open and no `claude` is running, and Ringleader stops the
box, with no client attached and whether or not you are watching.

Note what that deliberately does not count. The MCP server `thv run` leaves behind is a
detached container, so a box sitting there serving nothing still goes down — which is the
point, but it means the server is not necessarily back when the box is. Starting it again
is cheap, since the image is already pulled:

```bash
rl workstation start toolhive-box
# then check `thv list`, and `thv run toolhive-doc-mcp` again if it is not running
```

`ttl: 8h` / `ttlAction: stop` sits underneath as a hard ceiling. It is measured from
when the box was created and moved by nothing, so it stops the box at eight hours
whether or not you are using it. Raise it if your sessions run longer than that.
Neither control deletes the box, so deleting it yourself is what ends the disk bill,
and the same link that created it removes it:

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/stacklok-toolhive/toolhive-box-gcp.yaml -y
```

Azure and AWS are the same file with a different provider and sizing block. The
[dltHub example](../dlthub/) has all three.

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
