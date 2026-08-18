#!/usr/bin/env python3
"""Generate the GCP variant of an example from its local manifest.

The two files must differ only in PLACEMENT: namespace, provider requirement,
sizing and TTL. Everything else — tools, scripts, files, the agent — has to
track, or the example stops making the argument it exists to make. Generating
the cloud file rather than hand-editing it is what keeps that true.

    python3 hack/gen-gcp-variant.py --check    # fail if a file is stale
    python3 hack/gen-gcp-variant.py --write    # regenerate
"""
import argparse, pathlib, re, sys

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

def gcp_spec(e):
    return f"""spec:
  requirements: ["provider:gcp"]   # chooses the provider; the label above chooses the credentials

  providerConfig:      # sizing lives HERE only — a WorkstationConfig cannot set it
    gcp:
      machineType: {e['machine_type']}
      diskGiB: {e['disk']}

  # A cloud VM bills until it is deleted. Ringleader enforces this with no client
  # running, so the box goes away even if you close your laptop and forget.
  ttl: 8h
  ttlAction: delete
"""

def render(e):
    src = (ROOT / e["local"]).read_text()
    docs = src.split("\n---\n")

    ws = docs[0]
    # the workstation's own spec is replaced wholesale: local says `spec: {}` or
    # carries local-only sizing, and neither is meaningful in the cloud.
    ws = re.sub(r"\nspec:.*\Z", "\n" + gcp_spec(e), ws, flags=re.S)
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
