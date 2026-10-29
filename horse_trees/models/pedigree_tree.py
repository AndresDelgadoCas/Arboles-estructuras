"""Binary tree that models the pedigree (family tree) of a horse.

Each node is a horse:
    left child  -> sire (father)
    right child -> dam  (mother)
The root is the horse whose ancestry we are studying.
"""
from collections import deque
from itertools import count


class HorseNode:
    _ids = count(1)

    def __init__(self, name, breed="", birth_year=None):
        self.id = next(HorseNode._ids)
        self.name = name
        self.breed = breed
        self.birth_year = birth_year
        self.sire = None  # left child
        self.dam = None   # right child

    def __repr__(self):
        return f"HorseNode({self.name!r})"


class PedigreeTree:
    def __init__(self):
        self.root = None

    # ---------- basic operations ----------
    def set_root(self, name, breed="", birth_year=None):
        self.root = HorseNode(name, breed, birth_year)
        return self.root

    def find_by_id(self, node_id):
        for node in self._level_order_nodes():
            if node.id == node_id:
                return node
        return None

    def add_ancestor(self, child_id, role, name, breed="", birth_year=None):
        """Add a sire or dam to the horse identified by child_id."""
        if role not in ("sire", "dam"):
            raise ValueError("The role must be 'sire' or 'dam'.")
        child = self.find_by_id(child_id)
        if child is None:
            raise LookupError("Horse not found.")
        if getattr(child, role) is not None:
            raise ValueError(f"{child.name} already has a {role}.")
        new_node = HorseNode(name, breed, birth_year)
        setattr(child, role, new_node)
        return new_node

    def remove_subtree(self, node_id):
        """Remove a horse and all of its ancestors (the root cannot be removed)."""
        if self.root is None or self.root.id == node_id:
            raise ValueError("The root horse cannot be removed.")
        for node in self._level_order_nodes():
            for role in ("sire", "dam"):
                child = getattr(node, role)
                if child is not None and child.id == node_id:
                    setattr(node, role, None)
                    return child
        raise LookupError("Horse not found.")

    # ---------- traversals ----------
    def preorder(self):
        result = []

        def visit(node):
            if node:
                result.append(node.name)
                visit(node.sire)
                visit(node.dam)

        visit(self.root)
        return result

    def inorder(self):
        result = []

        def visit(node):
            if node:
                visit(node.sire)
                result.append(node.name)
                visit(node.dam)

        visit(self.root)
        return result

    def postorder(self):
        result = []

        def visit(node):
            if node:
                visit(node.sire)
                visit(node.dam)
                result.append(node.name)

        visit(self.root)
        return result

    def level_order(self):
        return [node.name for node in self._level_order_nodes()]

    def _level_order_nodes(self):
        if self.root is None:
            return
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            yield node
            for child in (node.sire, node.dam):
                if child:
                    queue.append(child)

    # ---------- measurements ----------
    def size(self):
        return sum(1 for _ in self._level_order_nodes())

    def height(self):
        """Number of generations above the root (root alone = 0)."""

        def h(node):
            if node is None:
                return -1
            return 1 + max(h(node.sire), h(node.dam))

        return h(self.root)

    def generations(self):
        """Names grouped by generation (0 = the horse, 1 = parents, ...)."""
        levels = []

        def visit(node, depth):
            if node is None:
                return
            if len(levels) == depth:
                levels.append([])
            levels[depth].append(node.name)
            visit(node.sire, depth + 1)
            visit(node.dam, depth + 1)

        visit(self.root, 0)
        return levels

    def path_to(self, node_id):
        """Names from the root down to the given horse."""

        def search(node, path):
            if node is None:
                return None
            path = path + [node.name]
            if node.id == node_id:
                return path
            return search(node.sire, path) or search(node.dam, path)

        return search(self.root, []) or []

    def repeated_ancestors(self):
        """Horses that appear more than once in the pedigree (inbreeding / linebreeding)."""
        appearances = {}

        def visit(node, depth):
            if node is None:
                return
            if depth > 0:
                appearances.setdefault(node.name.strip().lower(), []).append((node.name, depth))
            visit(node.sire, depth + 1)
            visit(node.dam, depth + 1)

        visit(self.root, 0)
        return [
            {"name": spots[0][0], "times": len(spots), "generations": [d for _, d in spots]}
            for spots in appearances.values()
            if len(spots) > 1
        ]

    # ---------- serialization ----------
    def to_dict(self):
        def convert(node, side):
            if node is None:
                return None
            sub = " · ".join(str(x) for x in (node.breed, node.birth_year) if x)
            return {
                "id": node.id,
                "label": node.name,
                "sub": sub,
                "side": side,
                "left": convert(node.sire, "sire"),
                "right": convert(node.dam, "dam"),
            }

        return convert(self.root, "root")

    @classmethod
    def sample(cls):
        """A small Paso Fino pedigree with a repeated ancestor (Centella)."""
        tree = cls()
        root = tree.set_root("Trueno", "Paso Fino Colombiano", 2020)
        sire = tree.add_ancestor(root.id, "sire", "Relámpago", "Paso Fino Colombiano", 2014)
        dam = tree.add_ancestor(root.id, "dam", "Luna", "Paso Fino Colombiano", 2015)
        s_sire = tree.add_ancestor(sire.id, "sire", "Centella", "Paso Fino Colombiano", 2008)
        tree.add_ancestor(sire.id, "dam", "Aurora", "Criollo Colombiano", 2009)
        tree.add_ancestor(dam.id, "sire", "Centella", "Paso Fino Colombiano", 2008)
        tree.add_ancestor(dam.id, "dam", "Estrella", "Criollo Colombiano", 2010)
        tree.add_ancestor(s_sire.id, "sire", "Huracán", "Paso Fino Colombiano", 2002)
        return tree
