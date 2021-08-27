"""Symbolic data-structure-level constraint parsing for constraint concretization at deletion time. """
from arpeggio import Optional, ZeroOrMore, OneOrMore, EOF, PTNodeVisitor
from arpeggio import RegExMatch as _


def merge_constraints(constraints, other):
    """Merge two constraints."""
    merged_constraints = []
    if not constraints:
        return other
    elif not other:
        return constraints
    for constraint in constraints:
        for new_constraint in other:
            merged_constraint = {}
            for key in constraint:
                val = [i for i in constraint[key]]
                if key in new_constraint:
                    val.extend(new_constraint[key])
                merged_constraint[key] = val
            for key in new_constraint:
                if key not in merged_constraint:
                    val = [i for i in new_constraint[key]]
                    merged_constraint[key] = val
            merged_constraints.append(merged_constraint)
    return merged_constraints


def symbolic(): return OneOrMore([conditioned_dnf, dnf]), EOF


def conditioned_dnf(): return "if", condition, "then", dnf, \
                              ZeroOrMore("elif", condition, "then", dnf), Optional("else", dnf)


def dnf(): return Optional("("), cnf, Optional(")"), ZeroOrMore("OR", Optional("("), cnf, Optional(")"))


def cnf(): return Optional("("), constraint, Optional(")"), ZeroOrMore("AND", Optional("("), constraint, Optional(")"))


def constraint():
    # 'condition' must be placed before 'func_name', since matching is ordered.
    # However, for simplicity, we require that all func_names are provided before conditions
    # xeq is paired with xeq_constraint() in synthesis.py for string synthesis.
    return ["gt", "ge", "lt", "le", "eq", "ne", "xeq"], "(", OneOrMore([condition, func_name], Optional(",")), ")"


def condition(): return condition_op, "(", ZeroOrMore(condition), ")"


def number(): return _(r'[0-9]+')


def condition_op(): return _(r'\w+')


def func_name(): return _(r'\w+')


class SymbolicVisitor(PTNodeVisitor):
    """Semantic analysis of a parsed tree of symbolic constraints."""
    def __init__(self, obj, struct, dg=False, *args, **kwargs):
        """
        self.obj corresponds to the Splice* object to be synthesized.
        self.struct corresponds to the object's enclosing data structure.
        self.constraints is the final concrete constraints in DNF. It is
        a list of maps where each map is a set of CNF constraints.
        """
        super().__init__(*args, **kwargs)
        self.obj = obj
        self.struct = struct
        self.constraints = []
        # internal use: if dg (dependency graph) is set to be True,
        # We are building a dependency graph and the way we visit
        # each nodes in the parser tree will be slightly different,
        # i.e., we will be building a conditional constraints list.
        self.dg = dg
        self.cond_constraints = []

    # The following methods visit each type of nodes in a parsed tree.
    # See reference: https://textx.github.io/Arpeggio/stable/semantics/

    def visit_condition(self, node, children):
        op = children[0]
        try:
            if len(children) > 1:   # condition has at least one argument
                val = getattr(self.struct, op)(*children[1:])
                if self.dg:
                    self.cond_constraints.extend(children[1:])
            else:   # condition has no argument, self.obj will be an implicit argument
                val = getattr(self.struct, op)(self.obj)
        except AttributeError:
            raise AttributeError("Operation {} is not defined".format(op))
        return val

    def visit_constraint(self, node, children):
        op = children[0]
        if len(children) == 1:  # condition might return None which means only one child exist
            return None
        elif len(children) == 2:
            if 'func_name' in children.results:
                # If the constraint contains a function, we obtain the function
                try:
                    val = getattr(self.struct, str(children[1]))
                except AttributeError:
                    raise AttributeError("Function {} is not defined".format(children[1]))
            else:
                if children[1] is not False:  # condition might return False (instead of None), which is also invalid
                    val = children[1]
                else:
                    return None
        else:   # If more than one condition exists, it is returned as a tuple (we must remove ',' in the expression)
            val = []
            if "func_name" in children.results:
                for func in children.results["func_name"]:
                    try:
                        func = getattr(self.struct, func)
                    except AttributeError:
                        raise AttributeError("Function {} is not defined".format(func))
                    val.append(func)
            if "condition" in children.results:
                for cond in children.results["condition"]:
                    val.append(cond)
            val = tuple(val)
        return {str(op): val}

    def visit_cnf(self, node, children):
        constraints = {}
        for child in children:
            if isinstance(child, dict):
                for key in child:
                    if key in constraints:
                        constraints[key].append(child[key])
                    else:
                        constraints[key] = [child[key]]
        return constraints

    def visit_dnf(self, node, children):
        dnf = []
        for child in children:
            if isinstance(child, dict):
                dnf.append(child)
        return dnf

    def visit_conditioned_dnf(self, node, children):
        if self.dg:
            merged_constraints = []
            for i in range(0, len(children) - 1, 2):
                merged_constraints = merge_constraints(children[i+1], merged_constraints)
            return merged_constraints
        # if and elifs (the first true condition is returned)
        for i in range(0, len(children) - 1, 2):
            if children[i]:
                return children[i+1]
        # If none of the if and elifs pass, we return else (if exists), which is the last in children
        if "else" in node:
            return children[-1]
        else:
            # No constraints are produced.
            return []

    def visit_symbolic(self, node, children):
        merged_constraints = []
        for child in children:
            if isinstance(child, list):
                merged_constraints = merge_constraints(child, merged_constraints)
        if self.dg:
            merged_constraints = merge_constraints([{'conds': self.cond_constraints}], merged_constraints)
        self.constraints = merged_constraints
