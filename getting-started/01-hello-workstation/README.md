# 01 · Hello, workstation

The smallest thing that works: one file, one command, a real Linux machine you
can shell into.

## Run it

```bash
rl apply -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/01-hello-workstation/workstation.yaml
rl workstation wait hello --for Ready --timeout 10m -n local
rl shell hello -n local
```

That URL is `workstation.yaml` in this directory. `-f` takes a local path just as
happily, so `rl apply -f workstation.yaml` is the same command if you cloned the
repository.

The first run downloads a base image, so it takes a few minutes. Later
workstations on the same image start much faster because the image is cached.

Have a look around, then leave with `exit` or **Ctrl-D**.

## What just happened

You described a machine in a file and Ringleader made it real. Three things are
going on:

**The spec is empty on purpose.** With nothing specified, Ringleader picks where
to run the workstation and applies defaults. You did not choose an image, a size,
or a provider.

**`apply` is declarative and safe to re-run.** Running it again reconciles the
workstation to match the file and reports `unchanged` when nothing differs, so
there is no separate "create" and "update" to think about.

**It stays.** Leaving the shell does not stop the machine. Close your laptop,
come back tomorrow, run `rl shell hello -n local` again, and you are where you
left off. That persistence is the point: the environment is a durable thing you
return to, not something you rebuild each morning.

## Clean up

```bash
rl workstation delete -f https://raw.githubusercontent.com/ringleader-dev/ringleader-examples/main/getting-started/01-hello-workstation/workstation.yaml -y
```

This is immediate and final for that machine. Its disk and state are gone.

Deleting by manifest rather than by name (`rl workstation delete hello -n local`
also works) is the habit to get into from the next example onward, where a
file declares more than one resource and the name form would leave some behind.

## Next

[02 · Adding tools](../02-adding-tools/): install software with a reusable
config that attaches by label.
