"""Dependency-lineage guard for q-conditioned teacher/student information rights."""


class QueryLeakageError(ValueError):
    pass


class DependencyCycleError(ValueError):
    pass


class QueryContractError(ValueError):
    pass


FORBIDDEN_SINK_ROLES = {'student_sink', 'target_normalization_sink'}
FORBIDDEN_SOURCE_ROLES = {'q_scalar', 'q_scalar_descendant'}
ALLOWED_ROLES = {
    'student_sink',
    'target_normalization_sink',
    'teacher_aux_sink',
    'q_scalar',
    'q_scalar_descendant',
    'q_address',
    'lawful_evidence',
    'teacher_non_q_evidence',
    'derived',
}


def _validate_node_name(node):
    if not isinstance(node, str) or not node.strip():
        raise QueryContractError('node names must be nonempty strings')
    if '\0' in node:
        raise QueryContractError('node names must be NUL-free')


def _validate_contract(graph, roles):
    if not isinstance(graph, dict) or not isinstance(roles, dict):
        raise QueryContractError('graph and roles must be mappings')
    if not graph:
        raise QueryContractError('nonempty dependency graph required')
    for node in graph:
        _validate_node_name(node)
    for node in roles:
        _validate_node_name(node)
    if set(graph) != set(roles):
        raise QueryContractError('graph and roles must declare exactly the same nodes')
    for node, parents in graph.items():
        if not isinstance(parents, list):
            raise QueryContractError(f'parents must be a list: {node}')
        if len(set(parents)) != len(parents):
            raise QueryContractError(f'duplicate parent edge: {node}')
        for parent in parents:
            _validate_node_name(parent)
            if parent not in graph:
                raise QueryContractError(f'undeclared parent node: {parent}')
    for node, role in roles.items():
        if role not in ALLOWED_ROLES:
            raise QueryContractError(f'unknown query-information role: {node}: {role}')


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
        role = roles[node]
        if role in FORBIDDEN_SOURCE_ROLES:
            return path + [node]
        for parent in graph[node]:
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
        for parent in graph[node]:
            dfs(parent, path + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])


def assert_query_safe(graph, roles):
    _validate_contract(graph, roles)
    _assert_acyclic(graph)
    for node, role in roles.items():
        if role not in FORBIDDEN_SINK_ROLES:
            continue
        path = _find_forbidden_path(graph, roles, node)
        if path:
            raise QueryLeakageError('query leakage path: ' + ' -> '.join(path))
