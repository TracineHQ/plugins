# Tracine Plugins

Official catalog of [TracineHQ](https://github.com/TracineHQ) Claude Code plugins. Add this marketplace once, install any current or future Tracine plugin.

## Install

Inside Claude Code:

```
/plugin marketplace add TracineHQ/plugins
/plugin install guard@tracine
/plugin install convo@tracine
```

The first command registers the `tracine` marketplace. The second/third install individual plugins from it. Run `/plugin marketplace update tracine` to pull newer plugin versions later.

## Plugins

### guard
Safety hooks for Claude Code — validates bash commands, protects credentials, enforces git discipline, scopes subagents, and guards protected files. Pure stdlib Python, no third-party dependencies.

Source: [TracineHQ/guard](https://github.com/TracineHQ/guard) · 1060 tests · Apache-2.0

### convo
SQLite-backed analytics CLI for Claude Code sessions. Auto-indexes session logs, adds full-text search across transcripts, tool-call analytics, and atomic snapshot/restore. Pure stdlib Python.

Source: [TracineHQ/convo](https://github.com/TracineHQ/convo) · 438 tests · Apache-2.0

## Verification

Every push to this repo runs an install check on fresh `ubuntu-latest` and `macos-latest` GitHub runners — installs Claude Code from npm, runs the install commands above, and asserts each plugin reports `Status: ✔ enabled`. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## License

Apache-2.0
