# 03 · Browser IDE

A complete environment in one file: a Debian box running VS Code in the browser,
with the port forwarded back to your machine so it feels local.

## Run it

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/03-browser-ide/ide-box.yaml
rl workstation wait ide-box -n local --for condition=Configured --timeout 15m
```

Then open **http://127.0.0.1:8080**.

The devtool installs are real network installs inside the VM, so the first run
takes a few minutes. Wait on `Configured` rather than `Ready`, for the reason
[02](../02-adding-tools/) gives: `Ready` only means the machine is up, and
code-server is installed after that.

## What this example adds

**Two resources in one file.** A `WorkstationConfig` and a `Workstation`,
separated by `---`. Applying a multi-document file creates or updates each
resource in it.

**`toolconfigs` vs `devtools`.** Two separate channels: `devtools` *installs*
software, `toolconfigs` *configures* software that is already installed. Here
`vscode-web` is installed by one and pointed at port 8080 by the other.

**Forwarding is not implicit.** Nothing reaches your machine unless you ask.
`defaultLocalBinding` seeds a device-local binding the first time the box runs,
forwarding its listening ports back 1:1. Without it the IDE would be running
happily and unreachable.

**`providerConfig` does not merge.** VM sizing is read from the **Workstation**
spec only, never from a config layer. Put `memory` and `cpus` on the workstation
itself. On a shared config they are silently ignored.

## A note on `auth: none`

code-server is served without authentication here, which is only acceptable
because the forward is loopback-only: nothing outside your machine can reach it.
Do not carry this setting into anything exposed on a network.

## Clean up

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/03-browser-ide/ide-box.yaml -y
```

Pass the manifest rather than the workstation name. `rl workstation delete
ide-box -n local` removes the machine but leaves the `ide` config behind, still
waiting to attach to the next workstation labelled `tier: dev`.

## Next

Something real: [an AI coding agent](../../environments/ai-coding-agent/) in a
governed environment, able to use your own browser to sign in.
