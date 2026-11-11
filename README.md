# NetHackers rehearsal bots

Each directory is a complete NetHackers solution root with its own
`bot.py`, manifest, AutoAscend code, and learned opening rules.

| Solution | Mean progress |
| --- | ---: |
| [opening-19b78fba9fb1](opening-19b78fba9fb1) | 0.15209 |
| [opening-b50849c11046](opening-b50849c11046) | 0.14347 |

Both results use the same 15 clean-start seeds for `val-dwa-law-fem`.
Stock AutoAscend scored 0.11217 on that panel.

Pass the absolute path to either solution directory as `--seed` when
starting checkpoint evolution. See the [rehearsal setup guide](https://github.com/vltrifonov/nethackers-w-rehearsal/blob/main/docs/harness.md#experimental-checkpoint-training)
for the arena build and command.
