# Ringleader examples

Ready-to-run examples for [Ringleader](https://ringleader.dev): persistent,
reproducible development environments for people and the AI agents working
alongside them.

Every example is a real manifest you can apply, and `-f` takes a URL as readily
as a local path, so you can run any of them without cloning anything first.

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/01-hello-workstation/workstation.yaml
```

Copy one, change what you need, and it is yours.

## Start here

New to Ringleader? These build on each other, in order.

| | |
| -- | -- |
| [01 · Hello, workstation](getting-started/01-hello-workstation/) | One file, one command, a Linux machine you can shell into |
| [02 · Adding tools](getting-started/02-adding-tools/) | Install software with a reusable config that attaches by label |
| [03 · Browser IDE](getting-started/03-browser-ide/) | VS Code in the browser, forwarded to your own machine |

## Environments

Complete, purpose-built setups.

| | |
| -- | -- |
| [AI coding agent](environments/ai-coding-agent/) | Claude Code or Codex in a governed box, signing in through your own browser |

## With other tools

Ringleader alongside tools you may already use. These are ours, not theirs: we
are not affiliated with the projects below, and each example says so.

| | |
| -- | -- |
| [Stacklok ToolHive](with/stacklok-toolhive/) | Host MCP servers in a workstation that has the container runtime they need |
| [dltHub](with/dlthub/) | Have your agent build a `dlt` data pipeline, in an environment as reproducible as the pipeline |

## Applying by URL

Each example gives you its commands with its own URL already filled in, so
nothing you run needs a file on disk. `rl diff -f` and `rl workstation delete -f`
take a URL on the same terms, which means you can preview an example before
running it and remove it afterwards without ever cloning this repository.

```bash
rl diff -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/01-hello-workstation/workstation.yaml
```

Two things worth knowing. The link has to be the **raw** one: a
`github.com/.../blob/...` address serves the HTML page around the file, and
applying that fails with a YAML parse error that does not explain itself. The
**Raw** button on any file here gives you the right link. And these URLs point at
`main`, so an example can change under you. Swap `main` for a commit SHA to pin
one to a version that will not move.

To edit an example rather than run it, take a copy:

```bash
git clone https://github.com/ringleader-dev/ringleader-examples.git
```

Or fetch a single file. That is what the one example needing edits before it
will run asks you to do:

```bash
curl -O https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/dlthub/dlt-box-gcp.yaml
```

## The idea

Describe the machine, the tools, and the agent your project needs in one file,
then apply it. Ringleader builds the same environment every time, on your laptop
or in your cloud. Hand the file to a teammate and they are running in minutes.
Give an agent exactly the tools and access it needs, and nothing else.

Three things show up across these examples:

**Two resources, deliberately separate.** A `Workstation` is an instance, the
machine itself. A `WorkstationConfig` is a reusable layer of software and settings that
finds machines *by label*, not by name. That indirection is what lets one config
equip a whole team.

**`Ready` is not `Configured`.** `Ready` means the machine is up. `Configured`
means your declared setup has actually landed on it. After a config change, wait
on `Configured`.

**Nothing reaches your machine unless you ask.** Port forwarding and
browser-open passthrough are opt-in, per environment. That is why the browser IDE
and the coding agent each declare what they expose. The same applies in reverse:
if an example expects you to sign in to something *inside* the box, it has to
declare the `passthrough-www-browser` devtool and a `LocalBinding`, or the
sign-in page has nowhere to open.

## Requirements

Ringleader installed, and the `rl` CLI on your path:

```bash
rl version
```

If not, start with the [installation guide](https://docs.ringleader.dev/getting-started/).
The `getting-started` examples run entirely on your own machine, with no cloud
account needed.

## Conventions

- Examples use the reserved **`local`** namespace, so they run against your
  machine's own runtime and never touch a control plane. Drop it to let
  Ringleader place the workstation elsewhere.
- **The base image is pinned** on every example that assumes anything about the
  distribution, and third-party tool **versions are pinned**.
  An example that silently changed under you would not be much of an argument
  for reproducibility. Each README says where to bump.
- Every example includes its **clean-up** command, and it deletes by manifest
  (`rl workstation delete -f <manifest> -y`) rather than by name. A manifest usually
  declares more than a machine, and deleting the machine alone leaves the config
  behind to attach itself to whatever you create next.

## Contributing

Issues and pull requests are welcome, especially:

- an example pairing Ringleader with a tool you use
- a correction where an example has drifted from reality

Keep an example runnable end to end, explain *why* rather than only *what*, and
pin versions.

## Licence

[Apache 2.0](LICENSE). Copy these into your own projects freely.
