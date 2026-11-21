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

solution, destination, objective, seed_arg, *trace_args = sys.argv[1:]
assert len(trace_args) <= 1
trace_runner = Path(trace_args[0]).resolve() if trace_args else None
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
    if trace_runner:
        assert trace_runner.is_file()
        entry = command.index('--entrypoint')
        command[entry:entry] = ['-v', f'{trace_runner}:/arena_public_trace.py:ro']
        module = command.index('-m')
        assert command[module+1]=='nethackers.arena.run'
        command[module:module+2] = ['/arena_public_trace.py']
    subprocess.run(command, **kwargs)
    if trace_dir.is_symlink():
        return
    for name, filename, cap, is_tail in (
            ('bot_public.log','bot-tail.txt',120000,True),
            ('arena-observations.json','arena-observations.json',320000,False)):
        log = trace_dir/name
        if not log.is_file() or log.is_symlink():
            continue
        fd=os.open(log,os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as file:
            meta=os.fstat(file.fileno())
            if not stat.S_ISREG(meta.st_mode) or (not is_tail and meta.st_size>cap):
                continue
            if is_tail:
                file.seek(max(0,meta.st_size-cap))
            (out/filename).write_bytes(file.read(cap))

out.mkdir(exist_ok=True)
evidence = eval_batch(Path(solution),scope,ARENA_IMAGE,now=datetime.now(timezone.utc).isoformat(),
                      runner=run_box,max_parallel_evals=1)
(out/'diagnostic.json').write_text(json.dumps({'diagnostic_only':True,'evaluation':evidence.to_dict()},indent=2)+'\n')
