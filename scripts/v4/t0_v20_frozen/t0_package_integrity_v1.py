from __future__ import annotations
import csv, hashlib
from pathlib import Path

HEADER=['filename','bytes','sha256']

def sha256_file(path: str|Path) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):
            h.update(b)
    return h.hexdigest()

def is_hex64(x: object) -> bool:
    return isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x)

def verify_flat_package(outdir: str|Path, members: set[str], manifest_name: str, root_name: str, *, label: str='package') -> str:
    out=Path(outdir)
    if not out.is_dir():
        raise ValueError(f'{label} directory missing')
    expected=set(members)|{manifest_name,root_name}
    entries=list(out.iterdir())
    if any(p.is_dir() for p in entries):
        raise ValueError(f'{label} unexpected directory')
    got={p.name for p in entries if p.is_file()}
    if got!=expected:
        raise ValueError(f'{label} member set mismatch')
    root_text=(out/root_name).read_text(encoding='utf-8')
    if not root_text.endswith('\n') or root_text.count('\n')!=1:
        raise ValueError(f'{label} root-file format mismatch')
    root=root_text[:-1]
    if not is_hex64(root):
        raise ValueError(f'{label} root invalid')
    if sha256_file(out/manifest_name)!=root:
        raise ValueError(f'{label} root mismatch')
    with (out/manifest_name).open('r',encoding='utf-8',newline='') as f:
        rows=list(csv.reader(f))
    if not rows or rows[0]!=HEADER:
        raise ValueError(f'{label} manifest columns mismatch')
    body=rows[1:]
    if len(body)!=len(members) or any(len(r)!=3 for r in body):
        raise ValueError(f'{label} manifest row count/shape mismatch')
    filenames=[r[0] for r in body]
    expected_order=sorted(members,key=lambda s:s.encode('utf-8'))
    if filenames!=expected_order or len(set(filenames))!=len(filenames):
        raise ValueError(f'{label} manifest member order/set mismatch')
    for filename,byte_text,digest in body:
        if not byte_text.isdigit() or str(int(byte_text))!=byte_text:
            raise ValueError(f'{label} manifest bytes invalid')
        if not is_hex64(digest):
            raise ValueError(f'{label} manifest sha256 invalid')
        p=out/filename
        if p.stat().st_size!=int(byte_text) or sha256_file(p)!=digest:
            raise ValueError(f'{label} member mismatch: {filename}')
    return root
