import subprocess
import os
import re


def _run_git(path, *args):
    try:
        result = subprocess.run(
            ['git'] + list(args),
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None, result.stderr.strip()
        return result.stdout.strip(), None
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return None, str(e)


def is_git_repo(path):
    if not path or not os.path.isdir(path):
        return False
    out, err = _run_git(path, 'rev-parse', '--git-dir')
    return out is not None


def clone(url, dest_path, branch='main'):
    parent = os.path.dirname(dest_path)
    if not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    if os.path.isdir(dest_path):
        return None, 'Le chemin existe déjà'
    out, err = _run_git(parent, 'clone', '--branch', branch, url, dest_path)
    if out is None:
        return None, err
    return dest_path, None


def fetch(path):
    return _run_git(path, 'fetch', '--all')


def pull(path, branch='main'):
    return _run_git(path, 'pull', 'origin', branch)


def branches(path):
    out, err = _run_git(path, 'branch', '-a')
    if out is None:
        return [], err
    result = []
    for line in out.split('\n'):
        line = line.strip().replace('* ', '').strip()
        if line:
            result.append(line.replace('remotes/origin/', ''))
    return list(dict.fromkeys(result)), None


def tags(path):
    out, err = _run_git(path, 'tag', '--sort=-creatordate')
    if out is None:
        return [], err
    return [t.strip() for t in out.split('\n') if t.strip()], None


def log(path, max_count=50, branch=None, path_filter=None):
    args = ['log', f'--max-count={max_count}', '--format=%H||%h||%an||%ae||%at||%s', '--date=unix']
    if branch:
        args.append(branch)
    if path_filter:
        args.extend(['--', path_filter])
    out, err = _run_git(path, *args)
    if out is None:
        return [], err
    commits = []
    for line in out.split('\n'):
        if not line.strip():
            continue
        parts = line.split('||', 5)
        if len(parts) >= 6:
            import datetime
            commits.append({
                'hash': parts[0],
                'short_hash': parts[1],
                'author': parts[2],
                'author_email': parts[3],
                'timestamp': int(parts[4]),
                'date': datetime.datetime.fromtimestamp(int(parts[4])).strftime('%Y-%m-%d %H:%M'),
                'message': parts[5],
            })
    return commits, None


def commit_detail(path, commit_hash):
    out, err = _run_git(path, 'show', '--format=%H||%h||%an||%ae||%at||%s||%b', '--no-stat', commit_hash)
    if out is None:
        return None, err
    lines = out.split('\n')
    header = lines[0].split('||', 6)
    if len(header) < 6:
        return None, 'Format invalide'
    import datetime
    body = '\n'.join(lines[1:]) if len(lines) > 1 else ''
    commit = {
        'hash': header[0],
        'short_hash': header[1],
        'author': header[2],
        'author_email': header[3],
        'timestamp': int(header[4]),
        'date': datetime.datetime.fromtimestamp(int(header[4])).strftime('%Y-%m-%d %H:%M'),
        'message': header[5],
        'body': body,
    }
    # Get diff
    diff_out, _ = _run_git(path, 'diff', f'{commit_hash}~1', commit_hash, '--stat')
    commit['diff_stat'] = diff_out or ''
    return commit, None


def diff(path, from_ref, to_ref):
    out, err = _run_git(path, 'diff', from_ref, to_ref)
    if out is None:
        return '', err
    return out, None


def tree(path, treeish='HEAD', subpath=''):
    args = ['ls-tree', '--name-only', treeish]
    if subpath:
        args.append(subpath)
    out, err = _run_git(path, *args)
    if out is None:
        return [], err
    items = []
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        full = os.path.join(subpath, line) if subpath else line
        is_dir = False
        # Check if it's a directory by ls-tree with -d
        dt_out, _ = _run_git(path, 'ls-tree', treeish, full)
        if dt_out:
            for dl in dt_out.split('\n'):
                if dl.strip() and full in dl:
                    mode, kind, hash_val, name = dl.strip().split(None, 3)
                    is_dir = (kind == 'tree')
        # Simpler method: try ls-tree -d on the name
        if not is_dir:
            dt_out2, _ = _run_git(path, 'ls-tree', '-d', treeish, full)
            is_dir = dt_out2 is not None and dt_out2.strip() != ''
        items.append({'name': line, 'path': full, 'is_dir': is_dir})
    return items, None


def file_content(path, ref='HEAD', filepath=''):
    out, err = _run_git(path, 'show', f'{ref}:{filepath}')
    if out is None:
        return None, err
    return out, None


def contributors(path, branch=None):
    args = ['shortlog', '-sne', '--all']
    if branch:
        args.append(branch)
    out, err = _run_git(path, *args)
    if out is None:
        return [], err
    result = []
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^\s*(\d+)\s+(.+?)\s+<(.+)>\s*$', line)
        if m:
            result.append({
                'count': int(m.group(1)),
                'name': m.group(2),
                'email': m.group(3),
            })
    return result, None


def file_size(path, ref='HEAD', filepath=''):
    out, err = _run_git(path, 'cat-file', '-s', f'{ref}:{filepath}')
    if out is None:
        return 0, err
    return int(out), None
