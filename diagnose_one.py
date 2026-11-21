"""Run one public trajectory with the bot's existing development log enabled."""
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

from nethackers._image_pins import ARENA_IMAGE
from nethackers.eval.runner import eval_batch
from nethackers.hub.objectives import CATALOG

solution, destination, objective, seed_arg = sys.argv[1:]
seed = int(seed_arg)
base = CATALOG[objective]
assert (seed,objective) in base.batch
scope = replace(base, batch=((seed,objective),))
out = Path(destination)

def run_box(command, **kwargs):
    mount = next(value for value in command if value.endswith(':/out'))
    output_dir = Path(mount.removesuffix(':/out'))
    trace_dir = output_dir/'diagnostics'
    trace_dir.mkdir(mode=0o777)
    trace_dir.chmod(0o777)
    entry = command.index('--entrypoint')
    command = command[:entry]+['-e','JF_LOG_DIR=/out/diagnostics','-e','JF_EPISODE=public',
                               '-e','JF_CFG={"SURV_LOG":true}']+command[entry:]
    subprocess.run(command, **kwargs)
    log = trace_dir/'bot_public.log'
    if trace_dir.is_symlink() or not log.is_file() or log.is_symlink():
        return
    fd=os.open(log,os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as file:
        meta=os.fstat(file.fileno())
        if stat.S_ISREG(meta.st_mode):
            file.seek(max(0,meta.st_size-120000))
            (out/'bot-tail.txt').write_bytes(file.read(120000))

out.mkdir(exist_ok=True)
evidence = eval_batch(Path(solution),scope,ARENA_IMAGE,now=datetime.now(timezone.utc).isoformat(),
                      runner=run_box,max_parallel_evals=1)
(out/'diagnostic.json').write_text(json.dumps({'diagnostic_only':True,'evaluation':evidence.to_dict()},indent=2)+'\n')
