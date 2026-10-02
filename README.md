# Tracine Plugins

Official catalog of [TracineHQ](https://github.com/TracineHQ) Claude Code plugins. Add this marketplace once, install any current or future Tracine plugin.

## Install

Inside Claude Code:

```
/plugin marketplace add TracineHQ/plugins
/plugin install guard@tracine
/plugin install convo@tracine
/plugin install eval-kit@tracine
```

The first command registers the `tracine` marketplace. The rest install individual plugins from it. Run `/plugin marketplace update tracine` to pull newer plugin versions later.

## Plugins

### guard
Safety hooks for Claude Code. Validates bash commands, protects credentials, enforces git discipline, scopes subagents, and guards protected files. Pure stdlib Python, no third-party dependencies.

Source: [TracineHQ/guard](https://github.com/TracineHQ/guard) · Apache-2.0

### convo
SQLite-backed analytics CLI for Claude Code sessions. Auto-indexes session logs, adds full-text search across transcripts, tool-call analytics, and atomic snapshot/restore. Pure stdlib Python.

Source: [TracineHQ/convo](https://github.com/TracineHQ/convo) · Apache-2.0

### eval-kit
Did the eval get better, or is that noise? A Claude Code skill and CLI that sizes the runs before you test and says "can't tell yet" when the data can't support a call. Zero-dependency JS with a scipy-backed Python twin, cross-validated in CI. Beta.

Source: [TracineHQ/eval-kit](https://github.com/TracineHQ/eval-kit) · Apache-2.0

## Verification

Every push to this repo runs an install check on fresh `ubuntu-latest` and `macos-latest` GitHub runners. It installs Claude Code from npm, runs the install commands above, and asserts each plugin reports `Status: ✔ enabled`. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## License

Apache-2.0
