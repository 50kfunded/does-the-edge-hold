"""Protocol choices and executed implementations have separate identities."""
from __future__ import annotations
import hashlib
import importlib.metadata
import inspect
import json
import marshal
import platform
import subprocess
import types
from pathlib import Path
from .plan import _digest

def _portable_code(code):
    constants = tuple(_portable_code(v) if isinstance(v, types.CodeType) else v for v in code.co_consts)
    return code.replace(co_filename="", co_firstlineno=1, co_linetable=b"", co_consts=constants)

def callable_identity(fn):
    if not inspect.isfunction(fn):
        raise ValueError("execution requires a registered Python function")
    filename = inspect.getsourcefile(fn)
    source = Path(filename).read_text(encoding="utf-8-sig").replace("\r\n", "\n") if filename and Path(filename).is_file() else None
    def captured(value):
        if inspect.isclass(value):
            filename = inspect.getsourcefile(value)
            source = Path(filename).read_text(encoding="utf-8-sig").replace("\r\n", "\n") if filename and Path(filename).is_file() else None
            return {"class": value.__module__ + "." + value.__qualname__, "source_sha256": hashlib.sha256(source.encode()).hexdigest() if source else None}
        if inspect.isfunction(value):
            return {"code": hashlib.sha256(marshal.dumps(_portable_code(value.__code__))).hexdigest()}
        try:
            json.dumps(value, allow_nan=False)
            return value
        except (TypeError, ValueError):
            raise ValueError("unregistered non-serializable closure/default in execution callable")
    return {"module": fn.__module__, "name": fn.__qualname__,
            "code_sha256": hashlib.sha256(marshal.dumps(_portable_code(fn.__code__))).hexdigest(),
            "defaults": [captured(v) for v in fn.__defaults__ or ()],
            "keyword_defaults": {k: captured(v) for k, v in (fn.__kwdefaults__ or {}).items()},
            "closure": [captured(c.cell_contents) for c in fn.__closure__ or ()],
            "source_sha256": hashlib.sha256(source.encode()).hexdigest() if source else None}

def seal(plan_hash, sources, *, evidence=None, callables=None):
    root = Path(__file__).parent
    code = {p.name: hashlib.sha256(p.read_text(encoding="utf-8-sig").replace("\r\n", "\n").encode()).hexdigest()
            for p in sorted(root.glob("*.py"))}
    env = {name: importlib.metadata.version(name) for name in
           ("numpy", "pandas", "pyarrow", "scipy", "matplotlib", "psutil")}
    identity = {"schema": 1, "protocol_sha256": plan_hash, "sources": sources,
                "evidence": evidence or {}, "source_code": code,
                "callables": {name: callable_identity(fn) for name, fn in (callables or {}).items()},
                "environment": {"python": platform.python_version(), "packages": env}}
    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    return {"execution_sha256": _digest(identity), "identity": identity,
            "git_revision": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain")),
            "note": "revision/dirty state are recorded; identity uses code bytes and actual callable code, not report paths or creation times"}

def write_manifest(manifest, path):
    Path(path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
