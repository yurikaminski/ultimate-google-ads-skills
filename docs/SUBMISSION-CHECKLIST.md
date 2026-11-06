# Pre-submission checklist mapping

| Checklist area | Status |
|---|---|
| Repository and folder layout | `.claude-plugin/marketplace.json` at root; each plugin has `.claude-plugin/plugin.json` only in that folder; components at plugin root. |
| Manifest and plugin name | Kebab-case permanent names, `displayName`, semver versions. `claude plugin validate --strict` passes for the marketplace and all three plugins. |
| README and license | README at root and in each plugin; MIT `LICENSE` at root and in each plugin; `NOTICE` credits prior art. |
| Files in the plugin folder | No binaries, no secrets, no `.env`; `.gitignore` excludes venvs and runtime state. |
| What the plugin runs and connects to | Local Python only. Network: only the onboarding fetcher, to sites the user names. No MCP servers, no hooks. |
| Hooks, skills, commands, agents | Skills under `skills/<name>/SKILL.md`; scaffold skills set `disable-model-invocation: true`; agents are read-only (`Read, Grep, Glob, Bash`). No hooks. |
| Security scan | No credential handling, no remote code download, no shell interpolation of external content. |
| Behavior test | `pytest` suite; `claude plugin eval` suite: TODO before directory submission. |
| `homepage` / `repository` fields | Set to the GitHub repo in all three plugin.json files. |

