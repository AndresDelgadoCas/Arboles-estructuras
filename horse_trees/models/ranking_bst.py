"""Binary Search Tree that ranks horses by competition points.

Ordering key: (points, name). Smaller keys go left, larger keys go right,
so an in-order traversal returns the horses from lowest to highest score.
"""


class RankNode:
    def __init__(self, name, points, discipline=""):
        self.name = name
        self.points = points
        self.discipline = discipline
        self.left = None
        self.right = None

    @property
    def key(self):
        return (self.points, self.name.lower())


class RankingBST:
    def __init__(self):
        self.root = None

    # ---------- insert ----------
    def insert(self, name, points, discipline=""):
        new_node = RankNode(name, points, discipline)
        if self.root is None:
            self.root = new_node
            return
        current = self.root
        while True:
            if new_node.key == current.key:
                raise ValueError("That horse already exists with the same points.")
            side = "left" if new_node.key < current.key else "right"
            child = getattr(current, side)
            if child is None:
                setattr(current, side, new_node)
                return
            current = child

    # ---------- search ----------
    def find_by_name(self, name):
        target = name.strip().lower()
        return next((n for n in self._nodes() if n.name.lower() == target), None)

    def minimum(self):
        node = self.root
        while node and node.left:
            node = node.left
        return node

    def maximum(self):
        node = self.root
        while node and node.right:
            node = node.right
        return node

    # ---------- delete ----------
    def delete(self, name):
        node = self.find_by_name(name)
        if node is None:
            raise LookupError("Horse not found.")
        self.root = self._delete(self.root, node.key)

    def _delete(self, node, key):
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            successor = node.right  # smallest node of the right subtree
            while successor.left:
                successor = successor.left
            node.name, node.points, node.discipline = (
                successor.name, successor.points, successor.discipline,
            )
            node.right = self._delete(node.right, successor.key)
        return node

    # ---------- traversals / metrics ----------
    def _nodes(self):
        """In-order generator (lowest score to highest)."""
        stack, node = [], self.root
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node
            node = node.right

    def ranking(self):
        """Horses from best to worst."""
        return [
            {"position": i + 1, "name": n.name, "points": n.points, "discipline": n.discipline}
            for i, n in enumerate(reversed(list(self._nodes())))
        ]

    def size(self):
        return sum(1 for _ in self._nodes())

    def height(self):
        def h(node):
            return -1 if node is None else 1 + max(h(node.left), h(node.right))

        return h(self.root)

    def to_dict(self):
        def convert(node):
            if node is None:
                return None
            return {
                "id": node.name,
                "label": node.name,
                "sub": f"{node.points:g} pts",
                "side": "bst",
                "left": convert(node.left),
                "right": convert(node.right),
            }

        return convert(self.root)

    @classmethod
    def sample(cls):
        tree = cls()
        for name, points, discipline in [
            ("Trueno", 870, "Trocha y galope"),
            ("Relámpago", 920, "Trocha y galope"),
            ("Luna", 790, "Trote y galope"),
            ("Centella", 955, "Trocha y galope"),
            ("Aurora", 740, "Trote y galope"),
            ("Estrella", 830, "Trocha y galope"),
            ("Huracán", 990, "Trocha y galope"),
        ]:
            tree.insert(name, points, discipline)
        return tree
