"""A predeclared local research panel distinct from all Hub evaluation seeds."""
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from nethackers._image_pins import ARENA_IMAGE
from nethackers.eval.runner import eval_batch
from nethackers.hub.objectives import CATALOG

solution, destination, identity = sys.argv[1:]
objective=CATALOG[identity]
panel=replace(objective,name=f'research-100-114-{identity}',
              batch=tuple((seed,identity) for seed in range(100,115)))
evidence=eval_batch(Path(solution),panel,ARENA_IMAGE,now=datetime.now(timezone.utc).isoformat())
Path(destination).write_text(json.dumps({'research_only':True,'evaluation':evidence.to_dict()},indent=2)+'\n')
