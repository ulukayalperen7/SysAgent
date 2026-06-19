# SysAgent Node Runtime

This package is the small runtime installed on a user machine so the SysAgent web app can execute approved commands through the backend command queue.

## Flow

1. User creates a device registration token in the web UI.
2. User runs `sysagent-node register --server <backend-url> --token <registration-token>`.
3. The backend returns a device id and one-time node runtime token.
4. The runtime stores the token locally in `~/.sysagent-node/config.json`.
5. `sysagent-node run` sends heartbeat, polls queued commands, executes approved scripts locally, and posts results back.
6. For always-on access, `sysagent-node service-install` writes the platform service definition and shows the install command.

## Commands

Install locally from this folder:

```powershell
python -m pip install .
```

Then register and run:

```powershell
sysagent-node register --server http://localhost:8080 --token <registration-token>
sysagent-node status
sysagent-node heartbeat
sysagent-node poll-once
sysagent-node run
```

Install as an always-on background runtime:

```powershell
sysagent-node service-install
sysagent-node service-install --apply
```

The installer uses the native user-level mechanism for the host OS:

- Windows: Scheduled Task at user logon
- Linux: `systemd --user` service
- macOS: LaunchAgent

Remove it with:

```powershell
sysagent-node service-uninstall --apply
```

For development from this folder:

```powershell
python -m sysagent_node.cli status
python -m unittest discover -s tests -q
```

The runtime stores the backend-issued node token in `~/.sysagent-node/config.json`. Keep that file private. Heartbeats include basic CPU/RAM usage when `psutil` is available. The runtime has a local denylist for critical destructive command patterns, but the main approval and audit boundary remains the Spring backend.
