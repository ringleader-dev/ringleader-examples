# dltHub

Have an AI agent build a working [dlt](https://dlthub.com) data pipeline, inside
a Ringleader workstation you declared, and load real data into SQLite.

## Why these fit together

A data pipeline is only reproducible if the environment around it is. The Python
version, the virtualenv, the system libraries, the destination credentials.
Those are the things that differ between laptops and produce a pipeline
that "works on mine".

`dlt` gives you a pipeline defined in code. This gives you the machine that runs
it defined in code too, so the whole thing is one reviewable artifact rather than
a script plus a page of setup instructions.

Which is what makes it a good place to put an agent. Writing a pipeline is
the kind of work you want to hand off, and it is also the kind of work
that touches real credentials and real destinations. Here the agent gets the
tools it needs and nothing else, in a box you can delete. What it can reach is
something you declared, not something it inherited from your laptop.

## Run it

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/dlthub/dlt-box.yaml
rl workstation wait dlt-box --for condition=Configured --timeout 20m -n local
rl shell dlt-box -n local
```

Then start your agent, inside the workstation:

```bash
claude          # or: codex
```

The first run asks you to sign in, and the page opens on **your** machine rather
than printing a URL the VM cannot open. That is the `passthrough-www-browser`
devtool and the `LocalBinding` in the manifest doing their job.

## Ask it to build the pipeline

`dlt` is already installed and on the path, so the agent can get straight to
work. Give it something like:

```
Using dlt, write and run a pipeline that loads the current Hacker News top
stories into a local SQLite database called hackernews.db. Use the
sqlalchemy destination, and merge on the story id so a second run refreshes
rows rather than duplicating them.
```

Then look at what it produced:

```bash
sqlite3 -header -column hackernews.db \
  "select substr(title,1,50) as title, score, by from stories order by score desc limit 5;"
```

```
title                                               score  by
--------------------------------------------------  -----  ---------------
Tailscale Traces Database Corruption to 16y/o RAM   719    ropbear
DeepSeek V4 Pro 0813                                676    explosion-s
2026 Eclipse Webcams                                451    zoenolan
```

Ask it to run the pipeline a second time and the row count should stay the same.
That is the merge working. It is also the part of the brief an agent is most
likely to skip, so check it.

**You will end up with more than one `.db` file, and that is correct.** SQLite
has no schemas, so dlt gives each dataset its own database file, and a merge load
needs a staging dataset. Expect `hackernews.db` next to a
`hackernews__main_staging.db`. Do not ask the agent to collapse them into one
file: it would be working against how the destination is designed, and the extra
file is dlt doing its job.

## Look at the data

`sqlite3` is fine for a spot check. For an actual look at what loaded, dlt has a
dashboard. Inside the workstation:

```bash
dlt pipeline hackernews show
```

It prints `URL: http://localhost:2718`. Open that on **your own machine**: the
port comes back to you automatically, because the LocalBinding in this manifest
sets `autoForward.forwardAll`. Nothing to configure, and nothing listening
outside your laptop. Give it a few seconds after the dashboard starts, since the
forward is established once the new port is noticed.

The dashboard shows the tables that loaded, their row counts and schemas, and it
will run queries against the dataset, which is a faster way to check the agent's
work than writing `select` statements by hand.

**Pick your table, then click Run query.** The dashboard does not fetch rows
until you ask it to, so a table can look empty when it is not.

**If it says "Could not connect to destination", your agent put the credentials
inside `dlt.pipeline(...)`.** The dashboard is a separate process and resolves
the destination from dlt's config, so it cannot see them. This box declares the
destination in `~/.dlt/secrets.toml` so the code only has to name it
(`destination="sqlalchemy"`). Worth correcting in the agent's version too.

Two smaller commands are useful without leaving the terminal:

```bash
dlt pipeline hackernews info     # dataset, schema, when it last ran
dlt pipeline hackernews trace    # what the last run actually did, step by step
```

`trace` is the one to reach for when a pipeline ran but the data looks wrong.

## Bring your own agent

The manifest names an agent on exactly one line:

```yaml
devtools:
  - name: nodejs
  - name: claude-code     # <- swap for `codex`
  - name: passthrough-www-browser
```

`claude-code` and `codex` are both in the devtool registry. Everything else here
is agent-agnostic: Node, the browser passthrough, and the LocalBinding are what
*any* agent needs to run and to sign in. For an agent that is not in the
registry but ships an npm CLI, use `packages` instead:

```yaml
packages:
  - type: npm
    name: some-other-agent
```

## A reference pipeline, for comparison

`~/pipeline.py` is on the box already, declared in the manifest under `files`. It
does what the prompt above asks for, and it is there for two reasons: so you can
compare it against whatever your agent wrote, and so the example still gives you
something runnable if you would rather not use an agent at all.

```bash
python pipeline.py
```

Shipping it in the manifest rather than beside it is deliberate, and not only for
tidiness. Nothing about applying a manifest uploads the directory it came from,
so a README that says "run `python pipeline.py`" is simply wrong unless something
puts that file on the box. `files` is that something. It materializes after
packages and before scripts, and it also takes `contentBase64`, a `url`, or
`${secret:NAME}` references.

## Taking it further

Everything that turns this from a demo into a real pipeline is in the manifest,
not in `pipeline.py`. The manifest is commented: read it for why the virtualenv
sits where it does, and why the dlt version and the base image are pinned.

**Run it in the cloud.** `dlt-box-gcp.yaml` is this same box on a GCP VM. Compare
the two files and the entire difference is placement: a namespace that is not
`local`, `requirements: ["provider:gcp"]`, a `providerConfig` for sizing, and a
`ttl` so a billing VM cannot outlive your attention. The tools, the pipeline, the
agent and the dashboard are byte-identical, which is the argument for describing
an environment rather than a machine.

It needs a namespace of your own, a CloudIdentity for gcp in it, and the label
that CloudIdentity selects on. That label is the one thing you cannot copy from
us: it is how the project and zone reach your VM, and if nothing matches you get
`providerConfig.gcp requires both project and zone`, which names the symptom
rather than the cause. The manifest says how to find yours.

Because those are edits you make before applying, this is the one example in the
repository to download rather than run from a link:

```bash
curl -O https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/dlthub/dlt-box-gcp.yaml
# edit `your-namespace` and the CloudIdentity label in all three documents, then:
rl apply -f dlt-box-gcp.yaml
rl workstation wait dlt-box --for condition=Configured --timeout 20m -n your-namespace
rl shell dlt-box -n your-namespace
```

Everything after that is the same as the local box: the agent, the pipeline and the
dashboard are unchanged.

**A cloud VM bills until it is deleted**, so clean up when you are done. The manifest's
`ttl: 8h` / `ttlAction: delete` is the backstop that runs even if you close your laptop
and forget; deleting it yourself is faster and cheaper:

```bash
rl workstation delete -f dlt-box-gcp.yaml -y
```

If you have not onboarded a cloud yet, start with the
[GCP guide](https://docs.ringleader.dev/cloud-onboarding/gcp/). Azure and AWS are
the same file with a different `provider:` and config block.

**A real destination.** Swap the extra in the install script:

```yaml
"$VENV/bin/pip" install "dlt[bigquery]==${DLT_VERSION}" requests
```

Credentials go through Ringleader rather than into the file. dlt reads
`DESTINATION__*` environment variables as configuration, so this reaches the
pipeline and the dashboard alike, and the value never enters the manifest, git,
or Terraform state:

```yaml
environment:
  DESTINATION__BIGQUERY__CREDENTIALS: ${secret:bq-service-account}
```

```bash
rl secret create bq-service-account --from-string value='<json>' -n local
```

**Telemetry.** dlt sends anonymous usage data by default, to
`telemetry.scalevector.ai`. It is genuinely anonymous — a random id in
`~/.dlt/.anonymous_id`, no account, no email — and it helps the project. This
manifest turns it off anyway with `RUNTIME__DLTHUB_TELEMETRY: "false"`, because an
example is a template people copy and a box that quietly talks to a third party is
not a good default to spread. Declaring it in the manifest rather than letting the
box write itself a config file is the point: outbound traffic is something a
reviewer can see in the diff. Delete that line to opt back in.

## Clean up

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/with/dlthub/dlt-box.yaml -y
```

Passing the manifest removes everything it declares: the workstation, the
WorkstationConfig and the LocalBinding. Deleting only the workstation would leave
the other two behind.

## Status

**The environment is verified end to end**, by applying this manifest to a fresh
workstation and following this README: the box configures, `dlt 1.30.0` is on the
login shell's path, the reference pipeline is on the box, `python pipeline.py`
loads 25 stories into SQLite, and a second run leaves the count unchanged, so the
merge behaviour is confirmed rather than assumed.

The agent-authored path depends on your agent, so what it writes will vary. The
box, the tools and the sign-in are the parts we can and do test.

Not affiliated with or endorsed by dltHub.
