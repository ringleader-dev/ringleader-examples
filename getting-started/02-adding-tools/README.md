# 02 · Adding tools

Software arrives through a **separate, reusable resource** that finds machines by
label. That indirection is the whole idea: one config can equip a whole team.

## Run it

```bash
rl apply -f workstation.yaml
rl apply -f tools.yaml

# Installing happens inside the VM, so wait for it to finish.
rl workstation wait hello --for condition=Configured --timeout 15m -n local
```

Then check the tools are really there:

```bash
rl shell hello -n local
git --version && node --version
```

## Two resources, on purpose

| | |
| -- | -- |
| **Workstation** | an instance: the machine itself |
| **WorkstationConfig** | a reusable layer of packages, devtools, ports and environment |

Keeping them apart means one config can apply to many machines, and one machine
can pick up several configs. Label another workstation `example: hello` and it
gets exactly the same tools, which is how a team stays consistent from a small
set of shared configs.

## `Ready` is not `Configured`

Two different conditions, and the difference matters when you add tools:

- **`Ready`**: the machine is up
- **`Configured`**: the declared configuration has actually been applied on it

Waiting on `Ready` after a config change will return too early. Wait on
`Configured`.

## Re-applying either file is safe

They are separate resources, so `rl apply -f workstation.yaml` and
`rl apply -f tools.yaml` each update only their own. Re-applying the workstation
does not wipe the config, and the two stay paired as long as the label matches.

To see what a machine actually resolved to, once both are applied:

```bash
rl workstation get-resolved-configuration hello -n local
```

`git` and `nodejs` appear there even though neither is on the workstation
itself, and `appliedConfigs` names the config that contributed them, with
`source: selector` recording that it matched by label rather than by name.

## Clean up

```bash
rl workstation delete -f workstation.yaml -y
rl workstation delete -f tools.yaml -y
```

Once per file: `-f` takes a single manifest, and each of these declares one
resource. Deleting only the workstation leaves `hello-tools` behind, ready to
attach itself to the next machine you label `example: hello`.

## Next

[03 · Browser IDE](../03-browser-ide/): a fully configured environment with a
web IDE forwarded to your machine.
