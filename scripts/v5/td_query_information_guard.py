"""Dependency-lineage guard for q-conditioned teacher/student information rights."""


class QueryLeakageError(ValueError):
    pass


class DependencyCycleError(ValueError):
    pass


FORBIDDEN_SINK_ROLES = {'student_sink', 'target_normalization_sink'}
FORBIDDEN_SOURCE_ROLES = {'q_scalar', 'q_scalar_descendant'}


def _find_forbidden_path(graph, roles, start):
    visiting = set()
    visited = set()

    def dfs(node, path):
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle = path[cycle_start:] + [node]
            raise DependencyCycleError('dependency cycle: ' + ' -> '.join(cycle))
        if node in visited:
            return None
        visiting.add(node)
        role = roles.get(node)
        if role in FORBIDDEN_SOURCE_ROLES:
            return path + [node]
        for parent in graph.get(node, []):
            hit = dfs(parent, path + [node])
            if hit:
                return hit
        visiting.remove(node)
        visited.add(node)
        return None

    return dfs(start, [])


def _assert_acyclic(graph):
    visiting = set()
    visited = set()

    def dfs(node, path):
        if node in visiting:
            raise DependencyCycleError('dependency cycle: ' + ' -> '.join(path + [node]))
        if node in visited:
            return
        visiting.add(node)
        for parent in graph.get(node, []):
            dfs(parent, path + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])


def assert_query_safe(graph, roles):
    _assert_acyclic(graph)
    for node, role in roles.items():
        if role not in FORBIDDEN_SINK_ROLES:
            continue
        path = _find_forbidden_path(graph, roles, node)
        if path:
            raise QueryLeakageError('query leakage path: ' + ' -> '.join(path))
