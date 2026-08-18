## Journey runner (merge into the project TECH_STACK.md)

The runner is the ONLY platform-specific piece of the journey layer. Declare exactly one:

```
JOURNEY_RUNNER: stub   # one of: playwright | maestro | appium | pty | http | stub
```

- `playwright` — web (browser automation)
- `maestro` / `appium` — mobile
- `pty` — CLI / terminal apps
- `http` — black-box API-only journeys
- `stub` — **Increment-1 placeholder ONLY.** The KLOSS framework repo itself has no real app to
  drive yet, so it declares `stub`. `journey-runner-resolve.sh` accepts `stub` only when
  `ALLOW_STUB_RUNNER=1` is set (local/fixture context). A real project must replace `stub` with a real
  runner before relying on the gates in production.

Resolve and validate the declared value with `journey-runner-resolve.sh <TECH_STACK_FILE>` — it never
executes the runner.
