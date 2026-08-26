#!/usr/bin/env python3
"""Generate the GCP variant of an example from its local manifest.

The two files must differ only in PLACEMENT: namespace, provider requirement,
sizing and the lifetime block (an idle policy and its ttl backstop, which exist
because a cloud VM bills and a laptop VM does not). Everything else — tools,
scripts, files, the agent — has to track, or the example stops making the
argument it exists to make. Generating the cloud file rather than hand-editing it
is what keeps that true, and it is why the idle policy's process name is DERIVED
from the local manifest's agent devtool rather than written out beside it.

    python3 hack/gen-gcp-variant.py --check    # fail if a file is stale
    python3 hack/gen-gcp-variant.py --write    # regenerate
"""
import argparse, pathlib, re, sys

try:
    import yaml
except ModuleNotFoundError:
    yaml = None   # reported where it is needed, with the install line

ROOT = pathlib.Path(__file__).resolve().parent.parent

EXAMPLES = [
    {
        "local": "with/dlthub/dlt-box.yaml",
        "gcp": "with/dlthub/dlt-box-gcp.yaml",
        "what": "dlt workstation",
        "box": "dlt-box",
        "machine_type": "n2-standard-2",
        "disk": 50,
    },
    {
        "local": "with/stacklok-toolhive/toolhive-box.yaml",
        "gcp": "with/stacklok-toolhive/toolhive-box-gcp.yaml",
        "what": "ToolHive workstation",
        "box": "toolhive-box",
        # ToolHive pulls and runs container images, so it needs the same headroom
        # the local variant asks for: 8 GiB / 4 vCPU.
        "machine_type": "n2-standard-4",
        "disk": 60,
    },
]

def header(e):
    return f"""# The same {e['what']}, running in Google Cloud instead of on your laptop.
#
# BEFORE THIS WILL WORK, replace `your-namespace` in ALL THREE documents below and
# set the label your own CloudIdentity selects on (see the comment on it). The
# README explains both, and https://docs.ringleader.dev/cloud-onboarding/gcp/ has
# the onboarding. Because those are edits, download this one rather than applying
# it from a link:
#
#   curl -O https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/{e['gcp']}
"""

LABEL = """    # THE LABEL THAT PICKS YOUR CloudIdentity — the one thing here you cannot copy
    # from us. Find yours with `rl get cloudidentity -n <your-namespace> -o yaml`
    # and use its spec.selector.matchLabels. If nothing matches, provisioning fails
    # with `providerConfig.gcp requires both project and zone`.
    cloud: gcp
"""

# The agent devtools an example may install, mapped to the executable name a
# process condition has to name. `processes` is matched against /proc/<pid>/comm
# exactly — never a path, a wildcard or a command line — so nothing but the
# binary's own name ever matches.
AGENT_COMM = {"claude-code": "claude", "codex": "codex"}

def agent_comm(e, src):
    """The comm name of the agent the LOCAL manifest installs.

    Derived from the manifest rather than configured beside it, because this
    script exists to keep the two files tracking and the agent is one of the
    things that has to track. An idle policy naming an agent the box does not
    run is a condition that can never hold the box up, and nothing would say so.

    PARSED, not pattern-matched. YAML lets the devtools sequence sit at its key's
    own column or indented under it, and in flow style on a single line; a regex
    over the text reads one of those legal shapes as no devtools at all. Reading
    spec.devtools is also what confines the search to devtools — `scripts` and
    `files` entries carry a `name:` too, so a step called `codex` would otherwise
    count as an agent.
    """
    if yaml is None:
        raise SystemExit(
            "PyYAML is required to read the local manifest's devtools: "
            "pip install PyYAML"
        )
    found = sorted({
        AGENT_COMM[tool["name"]]
        for doc in yaml.safe_load_all(src) if isinstance(doc, dict)
        for tool in (doc.get("spec") or {}).get("devtools") or []
        if isinstance(tool, dict) and tool.get("name") in AGENT_COMM
    })
    if len(found) != 1:
        raise SystemExit(
            f"{e['local']}: expected exactly one agent devtool from "
            f"{sorted(AGENT_COMM)}, found {found or 'none'} — the idle policy in "
            "the GCP variant names that agent's process"
        )
    return found[0]

def gcp_spec(e, comm):
    return f"""spec:
  requirements: ["provider:gcp"]   # chooses the provider; the label above chooses the credentials

  providerConfig:      # sizing lives HERE only — a WorkstationConfig cannot set it
    gcp:
      machineType: {e['machine_type']}
      diskGiB: {e['disk']}

  # A cloud VM bills while it runs, and what should power it down is nobody USING
  # it rather than a deadline. So the idle policy is the control here and `ttl` is
  # the backstop it always was. Ringleader evaluates both with no client running,
  # so they still fire if you close your laptop and forget.
  lifecycle:
    idle:
      timeout: 2h                # stop the box once it has been idle this long
      sshSessions: true          # an `rl shell` or `rl tmux` session means in use
      processes: ["{comm}"]{' ' * max(1, 12 - len(comm))}# ...and so does the agent, left running unattended
      # EVERY condition here must agree the box is idle before the clock starts, so
      # declaring another can only make the box harder to stop. Two gaps to know
      # about: a PTY-less session (VS Code Remote-SSH, `scp`, `ssh box <cmd>`) is not
      # an `sshSessions` hit, and neither is a DETACHED tmux; the process above covers
      # those whenever the agent is what is running, and a `ports` or `checkCommand`
      # condition covers you when it is not.
      # SWAPPED THE AGENT for `codex`? Change this name with it. The probe compares
      # the executable name exactly, so `claude` never matches a `codex` process — it
      # would just quietly stop holding the box up.
      # `stop` is the only action there is; nothing here can delete your box.
    # And a hard ceiling underneath it, measured from when the box was created and
    # moved by nothing — not a stop, not a start. It stops the box at 8h whether or
    # not somebody is using it, so raise it if you run longer sessions than that.
    ttl: 8h
    ttlAction: stop              # stop, not delete: the box is yours to start again
"""

def render(e):
    src = (ROOT / e["local"]).read_text()
    docs = src.split("\n---\n")

    ws = docs[0]
    # the workstation's own spec is replaced wholesale: local says `spec: {}` or
    # carries local-only sizing, and neither is meaningful in the cloud.
    ws = re.sub(r"\nspec:.*\Z", "\n" + gcp_spec(e, agent_comm(e, src)), ws, flags=re.S)
    if "labels:" not in ws:
        raise SystemExit(f"{e['local']}: workstation has no labels block to extend")
    ws = re.sub(r"(  labels:\n(?:    [^\n]*\n)+)", r"\1" + LABEL, ws, count=1)
    docs[0] = ws

    out = header(e) + "\n---\n".join(docs)
    return out.replace("namespace: local", "namespace: your-namespace")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    bad = 0
    for e in EXAMPLES:
        want, path = render(e), ROOT / e["gcp"]
        have = path.read_text() if path.exists() else None
        if want == have:
            print(f"ok      {e['gcp']}")
        elif a.write:
            path.write_text(want)
            print(f"written {e['gcp']}")
        else:
            print(f"STALE   {e['gcp']}")
            bad = 1
    sys.exit(bad if a.check else 0)
