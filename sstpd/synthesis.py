"""
Synthesis classes.
"""

from z3 import Solver, sat
from z3 import String, StringVal, Concat
from z3 import Re, InRe, Union, Star, Plus
from z3 import Int, Real
from z3 import BitVec
from z3 import And, Or, If

from datetime import datetime
from abc import ABC, abstractmethod

from asyncio.splice import __splice__
from asyncio.splice.splicetypes import SpliceMixin, SpliceInt, SpliceFloat, SpliceStr, SpliceDatetime, SpliceUserString
from asyncio.splice.identity import empty_taint


def dependencies_from_constraints(constraints_list, taint):
    """
    Given constraints_list, find all tainted objects
    that are likely to contribute to synthesis.
    """
    if not constraints_list:
        return []
    objs = []
    for constraints in constraints_list:
        if constraints:
            # FIXME: Code replication from _splice_synthesis. Should refactor.
            lt, le, gt, ge, obj = None, None, None, None, None
            if 'lt' in constraints:
                lt = min(constraints['lt'])
            if 'le' in constraints:
                le = min(constraints['le'])
            if lt and le:
                obj = min(lt, le)
            elif lt:
                obj = lt
            elif le:
                obj = le
            if isinstance(obj, SpliceMixin) and obj.taints == taint:
                objs.append(obj)

            if 'gt' in constraints:
                gt = max(constraints['gt'])
            if 'ge' in constraints:
                ge = max(constraints['ge'])
            if gt and ge:
                obj = max(gt, ge)
            elif gt:
                obj = gt
            elif ge:
                obj = ge
            if isinstance(obj, SpliceMixin) and obj.taints == taint:
                objs.append(obj)

            if 'eq' in constraints:
                # 'eq' constraints is a list of (func, value)
                for constraint in constraints['eq']:
                    obj = constraint[1]
                    if isinstance(obj, SpliceMixin) and obj.taints == taint:
                        objs.append(obj)
            if 'ne' in constraints:
                for constraint in constraints['ne']:
                    if isinstance(constraint, SpliceMixin) and constraint.taints == taint:
                        objs.append(constraint)

            if 'conds' in constraints:
                for constraint in constraints['conds']:
                    if isinstance(constraint, SpliceMixin) and constraint.taints == taint:
                        objs.append(constraint)
    return objs


class Synthesizer(ABC):
    """Synthesis base class."""
    def __init__(self, symbol):
        self.solver = Solver()
        self.var = symbol

    def lt_constraint(self, values, **kwargs):
        """
        Add to solver a less-than constraint: values can be
        a single value or a *list* of values: for v in values,
        self.var < v. By default, we assume that the type
        of the values can be handled by Z3 directly with <, such
        as a list of integers, but this is not always the case.
        In some cases like string, this function should be overridden.
        """
        if isinstance(values, list):
            for v in values:
                self.solver.add(self.var < v)
        else:
            self.solver.add(self.var < values)

    def gt_constraint(self, values, **kwargs):
        """
        Add to solver a greater-than constraint: values can
        be a single value or a *list* of values: for v in
        values, self.var > v. By default, we assume that the type
        of the values can be handled by Z3 directly with >, such
        as integers, but this is not always the case. In some
        cases like string, this function should be overridden.
        """
        if isinstance(values, list):
            for v in values:
                self.solver.add(self.var > v)
        else:
            self.solver.add(self.var > values)

    def eq_constraint(self, func, value, **kwargs):
        """
        Add to solver an equal-to constraint:
        func(self.var, **kwargs) == value. Note that
        func can be any custom function but operations
        in func must be supported by the Z3 variable
        type. For example, Z3's Int() does not support
        << (bit shift); therefore, func cannot have
        operations that use << to manipulate Int().
        func can take any number of *keyed* arguments
        but the first argument (required, non-keyed)
        must be the value to be synthesized. In summary,
        not all func can be supported for synthesis!
        Note that func can return self.var itself to
        create a trivial equal-to constraint.
        """
        self.solver.add(func(self.var, **kwargs) == value)

    def ne_constraint(self, value, **kwargs):
        """
        Add to solver an not-equal-to constraint. self.var
        can be any value but "value" in the argument.
        """
        self.solver.add(self.var != value)

    def le_constraint(self, values, **kwargs):
        """
        Add to solver a less-than-or-equal-to constraint:
        values can be a single value or a *list* of values:
        for v in values, self.var <= v. By default, we
        assume that the type of the values can be handled
        by Z3 directly with <=, such as a list of integers,
        but this is not always the case. In some cases
        like string, this function should be overridden.
        """
        if isinstance(values, list):
            for v in values:
                self.solver.add(self.var <= v)
        else:
            self.solver.add(self.var <= values)

    def ge_constraint(self, values, **kwargs):
        """
        Add to solver a greater-than-or-equal-to constraint:
        values can be a single value or a *list* of values:
        for v in values, self.var >= v. By default, we assume
        that the type of the values can be handled by Z3
        directly with >=, such as integers, but this is not
        always the case. In some cases like string, this
        function should be overridden.
        """
        if isinstance(values, list):
            for v in values:
                self.solver.add(self.var >= v)
        else:
            self.solver.add(self.var >= values)

    def bounded_constraints(self, upper_bound, lower_bound, include_upper=False, include_lower=False, **kwargs):
        """
        Add to solver constraints derived from an upper bound and
        a lower bound, both of which must exist (if not, call either
        lt_constraint(), le_constraint(), gt_constraint(), or
        ge_constraint() instead). If include_upper is True, upper
        bound is included. If include_lower is True, lower bound is
        included. Default for both are False.
        A subclass can override this function if the synthesizer
        allows different bounded constraints. Note that this function
        is implemented mostly for convenience; In most all cases,
        one can easily combine lt_constraint() and gt_constraint()
        to create the same bounded constraints. In some cases like
        string, however, this function should be overridden.
        """
        if include_upper and include_lower:
            self.le_constraint(upper_bound)
            self.ge_constraint(lower_bound)
        elif include_upper:
            self.le_constraint(upper_bound)
            self.gt_constraint(lower_bound)
        elif include_lower:
            self.lt_constraint(upper_bound)
            self.ge_constraint(lower_bound)
        else:
            self.lt_constraint(upper_bound)
            self.gt_constraint(lower_bound)

    def is_satisfied(self):
        """Returns True if given constraints can be satisfied."""
        return self.solver.check() == sat

    @property
    def value(self):
        """
        Return synthesized variable value (Z3 type) if
        the model can be satisfied; otherwise None.
        """
        if self.is_satisfied():
            return self.solver.model()[self.var]
        else:
            return None

    @staticmethod
    @abstractmethod
    def to_python(value):
        """
        Convert the value of Z3 type to *untrusted* Python type (e.g., from
        z3.IntNumRef to UntrustedInt) depend on the type of _var. Return
        None if the value is None. One can also use this function to perform
        "double conversion" for Python types that are not supposed by Z3.
        For example, if a customized synthesizer is designed to synthesize
        Python's datetime value. You can define a function in the subclass
        to convert datetime values to integers and subclass IntSynthesizer.
        You should then override this function. In this function, `value`
        would be a synthesized z3.IntNumRef. You can first convert it to an
        int and then convert the integer value back to a synthesized
        (untrusted) datetime value and return it. A subclass should always
        override this function.
        """
        raise NotImplementedError("to_python() is not overridden in this subclass, "
                                  "subclassed from the abstract Synthesizer class.")

    def bounded_synthesis(self, *, upper_bound=None, lower_bound=None,
                          include_upper=False, include_lower=False, **kwargs):
        """
        Synthesis based on an upper and a lower bound,
        both of which must exist. Subclasses can override
        bounded_constraints() and call this function as public API.
        A synthesized value is returned if synthesis is successful;
        otherwise, we return None.
        """
        if not upper_bound or not lower_bound:
            raise ValueError("Two bounds must be specified. Perhaps use a different"
                             "synthesis method or simply call random()?")
        self.bounded_constraints(upper_bound, lower_bound, include_upper, include_lower, **kwargs)
        if self.value is not None:
            return self.to_python(self.value)
        else:
            return None

    @staticmethod
    @abstractmethod
    def simple_synthesis(value):
        """
        Synthesis by simply wrapping a value in an untrusted type
        (e.g., wrap Int to UntrustedInt) and set the type's
        synthesized flag to True. Returns None if value is None.
        A subclass should always override this function.
        """
        raise NotImplementedError("simple_synthesis() is not overridden in this subclass,"
                                  " subclassed from the abstract Synthesizer class.")

    def reset_constraints(self):
        """Remove all constraints in the solver."""
        self.solver.reset()

    def splice_synthesis(self, constraints_list):
        """
        Splice deletion-by-synthesis should call this method to generate a new
        synthesized value. "constraints_list" is a list of disjunctive constraints.
        Each member in "constraints_list" should be a dictionary of value constraints
        (conjunctive). Synthesis stops as soon as one set of conjunctive constraints
        generates a new value. If synthesis is unsuccessful for all sets, the caller
        then needs to make sure the object's trusted and synthesized flag are set
        properly (see middleware.py).
        """
        if not constraints_list:
            return None
        for constraints in constraints_list:
            synthesized_value = self._splice_synthesis(constraints)
            if synthesized_value is not None:
                return synthesized_value
        return None

    def _splice_synthesis(self, constraints):
        """
        "constraints" should be a dictionary of conjunctive value constraints.
        If constraints is None or an empty dictionary, no synthesis would occur.
        Note that depending on the constraints, synthesis may or may not succeed.
        """
        # Empty or None constraints case
        if not constraints:
            return None

        #####################################################################################
        # 'xeq' is special: we should have at most one 'gt', at most one 'lt'
        # and one and onl one 'xeq' in the constraints for this to work.
        # 'xeq' is used for sstable in LevelDB. #TODO: Can be made more general
        if 'xeq' in constraints:
            # FIXME: we can only handle one 'xeq' at the moment
            if len(constraints['xeq']) != 1:
                return None
            upper_bound, lower_bound = None, None
            if 'lt' in constraints:
                if len(constraints['lt']) != 1:
                    return None
                else:
                    upper_bound = constraints['lt'][0]
            if 'gt' in constraints:
                if len(constraints['gt']) != 1:
                    return None
                else:
                    lower_bound = constraints['gt'][0]
            # The one xeq constraint has two items, the first is the 'value' and the second is the 'fixed_length'.
            self.xeq_constraint(constraints['xeq'][0][0], constraints['xeq'][0][1], upper_bound, lower_bound)

            if self.value is not None:
                return self.to_python(self.value)
            else:
                return None
        #####################################################################################

        # Consolidate constraints as much as we can.
        # As a result, we create a new mapping 'cnts'
        cnts = dict()
        if 'lt' in constraints:
            cnts['lt'] = min(constraints['lt'])
        if 'le' in constraints:
            cnts['le'] = min(constraints['le'])
        if 'gt' in constraints:
            cnts['gt'] = max(constraints['gt'])
        if 'ge' in constraints:
            cnts['ge'] = max(constraints['ge'])
        upper_bound, lower_bound, include_upper, include_lower = None, None, False, False
        if 'lt' in cnts and 'le' in cnts:
            if cnts['lt'] <= cnts['le']:
                upper_bound = cnts['lt']
            else:
                upper_bound = cnts['le']
                include_upper = True
        elif 'lt' in cnts:
            upper_bound = cnts['lt']
        elif 'le' in cnts:
            upper_bound = cnts['le']
            include_upper = True
        if 'gt' in cnts and 'ge' in cnts:
            if cnts['gt'] >= cnts['ge']:
                lower_bound = cnts['gt']
            else:
                lower_bound = cnts['ge']
                include_lower = True
        elif 'gt' in cnts:
            lower_bound = cnts['gt']
        elif 'ge' in cnts:
            lower_bound = cnts['ge']
            include_lower = True
        if upper_bound is not None and lower_bound is not None:
            self.bounded_constraints(upper_bound, lower_bound, include_upper, include_lower)
        else:
            if 'lt' in cnts:
                self.lt_constraint(cnts['lt'])
            if 'le' in cnts:
                self.le_constraint(cnts['le'])
            if 'gt' in cnts:
                self.gt_constraint(cnts['gt'])
            if 'ge' in cnts:
                self.ge_constraint(cnts['ge'])

        if 'eq' in constraints:
            # 'eq' constraints is a list of (func, value)
            for constraint in constraints['eq']:
                self.eq_constraint(constraint[0], constraint[1])

        if 'ne' in constraints:
            for constraint in constraints['ne']:
                self.ne_constraint(constraint)

        if self.value is not None:
            return self.to_python(self.value)
        else:
            return None


class IntSynthesizer(Synthesizer):
    """Synthesize an integer value, subclass from Synthesizer."""
    def __init__(self):
        super().__init__(Int('var'))

    @staticmethod
    def to_python(value):
        if value is not None:
            # Synthesized value needs no taint
            return SpliceInt(value.as_long(), trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None

    @staticmethod
    def simple_synthesis(value):
        if value is not None:
            # Synthesized value needs no taint
            return SpliceInt(value, trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None


class FloatSynthesizer(Synthesizer):
    """Synthesize a float value, subclass from Synthesizer."""
    def __init__(self):
        super().__init__(Real('var'))

    @staticmethod
    def to_python(value):
        if value is not None:
            fraction_value = value.as_fraction()
            # Lose precision when casting into float
            float_value = float(fraction_value.numerator) / float(fraction_value.denominator)
            # Synthesized value needs no taint
            return SpliceFloat(float_value, trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None

    @staticmethod
    def simple_synthesis(value):
        if value is not None:
            # Synthesized value needs no taint
            return SpliceFloat(value, trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None


class BitVecSynthesizer(Synthesizer):
    """Synthesize bit vector value, subclass from Synthesizer."""
    def __init__(self, bits=32):
        """
        Create a bit-vector variable in Z3
        named b with given (32 by default) bits.
        """
        super().__init__(BitVec('b', bits))

    @staticmethod
    def to_python(value):
        if value is not None:
            # Synthesized value needs no taint
            return SpliceInt(value.as_long(), trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None

    @staticmethod
    def simple_synthesis(value):
        """Python can automatically convert a bit vector to int."""
        if value is not None:
            # Synthesized value needs no taint
            return SpliceInt(value, trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None


def printable_ascii_chars():
    """
    Returns an order string of printable ASCII
    characters we use from 0x20 (space) to 0x7E (~).
    """
    chars = str()
    for i in range(32, 127):
        chars += chr(i)
    return chars


class StrSynthesizer(Synthesizer):
    """Synthesize a string value, subclass from Synthesizer."""
    # All default possible characters in a synthesized string (printable ASCII)
    DEFAULT_ASCII_CHARS = printable_ascii_chars()
    # The maximum possible length of a synthesized string
    DEFAULT_MAX_CHAR_LENGTH = 50

    def __init__(self, charset=None):
        super().__init__(String("var"))
        if not charset:
            # Create a default character set
            # (always add upper-case chars first)
            charset = self.DEFAULT_ASCII_CHARS
        self._charset = charset                                             # String representation
        self._chars = Union([Re(StringVal(c)) for c in self._charset])      # Z3 union representation

    @property
    def value(self):
        """
        Return synthesized variable values (Z3 type) if
        the model can be satisfied; otherwise returns None.
        This property overrides base class value property
        because eq_constraint() might add new Z3 variables
        to the solver, so we cannot simply inherit from base.
        This function either returns a single Z3 String-typed
        value or a list of Z3 Int-typed value [x0, x1...],
        where x0 is the byte value of the first character,
        x1 is the byte value of the second character, etc.
        """
        if self.is_satisfied():
            m = dict()                      # Store variable name (str) -> Z3 value
            model = self.solver.model()
            for var in model:
                m[var.name()] = model[var]
            if "var" in m:                  # The model contains only our String variable
                return m["var"]
            else:                           # The model contains Int variables
                # Returns an ordered (starting from x0) list of Int values
                return [m['x%s' % i] for i in range(self.DEFAULT_MAX_CHAR_LENGTH)]
        else:
            return None

    def lt_constraint(self, value, **kwargs):
        """
        Override base class lt_constraint(). We find the first character
        in value that has a smaller character and replace it with a smaller
        character picked by Z3. Every character before that would be the same
        as value and every character after that, if exists, is picked by Z3.
        If every character in value is the smallest character in charset, we
        try to remove the last character in value and use a shorter string.
        If there is no string smaller than value, an empty string is returned.
        The constraint is a regular expression template added to the solver.
        If value is an empty string, the synthesis will always fail!
        e.g., (assume 'A' is the smallest in the character set):
        * "Jack" -> "[A-I]*"
        * "Adam" -> "A[A-Za-c]*" (the first "A" must be in template)
        * "AA" -> "A" (a shorter string)
        * "A" -> "" (there can be no smaller value, so empty string).

        An optional offset parameter can be provided, but this is mostly
        useful for bounded synthesis. If provided, characters in position
        0 to offset would be the same in synthesized string as in value
        (if offset < the length of the value). Offset is by default 0.
        """
        if not value:
            # For an empty string value, we add
            # False so synthesis always return 'unsat'.
            self.solver.add(False)
        else:
            template = self._lt_constraint(value, **kwargs)
            self.solver.add(InRe(self.var, template))

    def le_constraint(self, value, **kwargs):
        """
        The same rules as in lt_constraint() except that
        the synthesized string can be the same as value.
        """
        lt_template = self._lt_constraint(value, **kwargs)
        eq_template = Re(StringVal(value))
        self.solver.add(Or(InRe(self.var, lt_template), InRe(self.var, eq_template)))

    def _lt_constraint(self, value, **kwargs):
        """
        Helper function for lt_constraint(). Returns the template
        to synthesize a string (or ValueError). See lt_constraint()
        for more detailed description. User should always call
        lt_constraint() as the public API, not this function.
        'value' should never be an empty string in this function.
        """
        # Create a regular expression template for synthesis
        bound_length = len(value)
        offset = 0
        if "offset" in kwargs:
            offset = kwargs["offset"]
        # If bound_char is the smallest possible in charset
        # Go to the next character until we are no longer able to
        # because we are at the last character of the bound string
        while offset < bound_length:
            bound_char = value[offset]
            bound_pos = self._charset.find(bound_char)
            if bound_pos < 0:
                raise ValueError("upper-bound string '{upper}' contains a character "
                                 "'{character}' that is not found in the charset "
                                 "'{charset}'.".format(upper=value,
                                                       character=bound_char,
                                                       charset=self._charset))
            elif bound_pos == 0:
                offset += 1
            else:
                break
        if offset >= bound_length:
            # The last resort is to remove the last character
            # If value has only one character, then empty string
            # is the only possible answer
            synthesized_char = value[:bound_length-1]
            # In case synthesized_char is an empty string, we need
            # two arguments for Concat, which means we need to add
            # another empty string.
            empty_char = Re(StringVal(""))
            template = Concat(Re(StringVal(synthesized_char)), empty_char)
        else:
            possible_charset = self._charset[:bound_pos]
            char = Union([Re(StringVal(c)) for c in possible_charset])
            template = Concat(Re(StringVal(value[:offset])), char, Star(self._chars))
        # Our synthesized string should match the template
        return template

    def gt_constraint(self, value, **kwargs):
        """
        Override base class gt_constraint(). We find the first character
        in value that has a larger character and replace it by Z3 with
        a larger character. Every character before that would be the same
        as value and every character after that, if exists, is picked by Z3.
        If every character in value is the largest character in charset, we
        try to add at the end of value a new character and use a longer string.
        The constraint is a regular expression template added to the solver.
        e.g. (assume 'z' is the largest in the character set):
        * "Jack" -> "[K-Za-z][A-Za-z]*"
        * "" -> "[A-Za-z]+"
        * "z" -> "z[A-Za-z]+" (the first "z" must be in template).

        An optional offset parameter can be provided, but this is mostly
        useful for bounded synthesis. If provided, characters in position
        0 to offset would be the same in synthesized string as in value
        (if offset < the length of the value). Offset is by default 0.
        """
        template = self._gt_constraint(value, **kwargs)
        self.solver.add(InRe(self.var, template))

    def ge_constraint(self, value, **kwargs):
        """
        The same rules as in gt_constraint() except that
        the synthesized string can be the same as value.
        """
        gt_template = self._gt_constraint(value, **kwargs)
        eq_template = Re(StringVal(value))
        self.solver.add(Or(InRe(self.var, gt_template), InRe(self.var, eq_template)))

    def _gt_constraint(self, value, **kwargs):
        """
        Helper function for gt_constraint(). Returns the template
        to synthesize a string (or ValueError). See gt_constraint()
        for more detailed description. User should always call
        gt_constraint() as the public API, not this function.
        """
        bound_length = len(value)
        if bound_length == 0:
            # If value is an empty string, any non-empty string will do
            empty_char = Re(StringVal(""))
            template = Concat(empty_char, Plus(self._chars))
        else:
            offset = 0
            if "offset" in kwargs:
                offset = kwargs["offset"]
            # If bound_char is the biggest possible in charset,
            # go to the next character until we are no longer able to
            # because we are at the last character of the bound string
            while offset < bound_length:
                # The "offset" character of our synthesized string should
                # be larger than that of the lower bound (if possible)
                bound_char = value[offset]
                # Find the position of bound_char in charset
                bound_pos = self._charset.find(bound_char)
                if bound_pos < 0:
                    # If not found, charset is not given correctly.
                    return ValueError("lower-bound string '{lower}' contains a character "
                                      "'{character}' that is not found in the charset "
                                      "'{charset}'.".format(lower=value,
                                                            character=bound_char,
                                                            charset=self._charset))
                elif bound_pos >= len(self._charset) - 1:
                    offset += 1
                else:
                    break
            if offset >= bound_length:
                # We cannot find any usable character in bound string
                # This is OK because we can add a new character at
                # the end of our synthesized string anyways.
                # So the first part of our synthesized string looks
                # just like the bound string.
                ######################################################
                # Note that for performance we simply append the
                # smallest character to the end of the string. Instead
                # of allowing Z3 to pick what and how many characters
                # to append becauase it typically will add the largest
                # character and future synthesis will just continue to
                # add more characters, making synthesis taking longer.
                # (this is what Z3 does given the commented statement
                # below, which may result in worse performance.)
                # FIXME: This is hacky. We should find a better way.
                # template = Concat(Re(StringVal(value[:bound_length])), Plus(self._chars))              # can be slow
                template = Concat(Re(StringVal(value[:bound_length])), Re(StringVal(self._charset[0])))  # fast
                ######################################################
            else:
                ######################################################
                # We can find a larger character, for performance we
                # restrict the possible choice and how a larger string
                # is constructed.
                # FIXME: This is hacky. We should find a better way.
                possible_charset = self._charset[bound_pos+1:]                # can be slow
                # possible_charset = self._charset[bound_pos + 1:bound_pos + 2]   # fast

                char = Union([Re(StringVal(c)) for c in possible_charset])

                template = Concat(Re(StringVal(value[:offset])), char, Star(self._chars)) # can be slow
                # template = Concat(Re(StringVal(value[:offset])), char)                      # fast
                ######################################################
        # Our synthesized string should match the template
        return template

    def eq_constraint(self, func, value, **kwargs):
        """
        The synthesized string is represented by a list of bytes (integers of ASCII)
        and the func used must take a list of integers as its first positional parameter.
        """
        # We use Z3's list comprehension to create a list of Z3 Int() variables
        chars = [Int('x%s' % i) for i in range(self.DEFAULT_MAX_CHAR_LENGTH)]
        for char in chars:
            # 0 is the NULL character
            # 32 is the smallest printable ASCII value
            # 126 is the largest printable ASCII value
            self.solver.add(Or(char == 0, And(char >= 32, char <= 126)))
        # The character string must be well-formed, therefore, if
        # a character is set to be NULL (0), then the character in
        # front of it must be NULL as well.
        for i in range(len(chars) - 1):
            self.solver.add(If(chars[i+1] == 0, chars[i] == 0, True))
        self.solver.add(func(chars, **kwargs) == value)

    def ne_constraint(self, value, **kwargs):
        """Not equal is simply lt OR gt."""
        lt_template = self._lt_constraint(value, **kwargs)
        gt_template = self._gt_constraint(value, **kwargs)
        self.solver.add(Or(InRe(self.var, lt_template), InRe(self.var, gt_template)))

    def bounded_constraints(self, upper_bound, lower_bound, include_upper=False, include_lower=False, **kwargs):
        """
        We cannot simply add lt_constraint() and gt_constraint() without
        specifying a common offset. Otherwise, it is possible that the template
        generated by lt_constraint() becomes incompatible with the template
        generated by gt_constraint() (so no string can be synthesized) even if it
        is lexicographically possible to synthesize a string between the two bounds.
        """
        upper_bound_length = len(upper_bound)
        lower_bound_length = len(lower_bound)
        bound_length = min(upper_bound_length, lower_bound_length)
        pos = 0
        while pos < bound_length:
            if upper_bound[pos] == lower_bound[pos]:
                pos += 1
            else:
                break
        # Handle the case where bounded constaints is impossible.
        if pos == bound_length and upper_bound_length == lower_bound_length:
            self.solver.add(False)
            return
        # Handle a special case where at the offset the upper_bound
        # character is exactly one above the lower_bound character.
        # If there are still more characters after the offset, we can
        # still synthesize a valid string that is within the bounds,
        # but it will not work when we combine le_constraint() (or
        # lt_constraint()) and ge_constraint() (or gt_constraint()).
        # Example: '987-12' (upper) and '987-08' (lower). Instead,
        # we just need to change the offset and do a lower bound.
        if pos < bound_length and ord(lower_bound[pos]) + 1 == ord(upper_bound[pos]):
            if include_lower:
                self.ge_constraint(lower_bound, offset=pos+1)
            else:
                self.gt_constraint(lower_bound, offset=pos+1)
            return
        if include_upper and include_lower:
            self.le_constraint(upper_bound, offset=pos)
            self.ge_constraint(lower_bound, offset=pos)
        elif include_upper:
            self.le_constraint(upper_bound, offset=pos)
            self.gt_constraint(lower_bound, offset=pos)
        elif include_lower:
            self.lt_constraint(upper_bound, offset=pos)
            self.ge_constraint(lower_bound, offset=pos)
        else:
            self.lt_constraint(upper_bound, offset=pos)
            self.gt_constraint(lower_bound, offset=pos)

    def xeq_constraint(self, value, fixed_length, upper_bound=None, lower_bound=None):
        """
        This is a special constraint where the synthesized value S must be smaller than
        the upper bound value U (if exists), larger than the lower bound value L (if exists),
        *and* have the same first fixed_length L characters as value V. That is,
        L <= S <= U && S[:L] == V[:L]
        Note that for this constraint to be solvable, we must have:
        L <= V <= U

        Although this method is created specifically for sstable in MiniLevelDB, we do not
        necessarily need to have this special constraint method. We can always combine
        existing constraint methods to create the same final constraint.
        """
        # NOTE ================================================
        # The following line of code is used specificially for
        # SpliceUserString to convert it to SpliceStr. This is
        # necessary because, unlike SpliceStr, SpliceUserString
        # is not inherited from str, so many str operations
        # that are called later in the logic do not work unless
        # we convert them to SpliceStr. The str() method on
        # SpliceUserString will call its __str__ and do the job.
        value = str(value)
        if upper_bound:
            upper_bound = str(upper_bound)
        if lower_bound:
            lower_bound = str(lower_bound)
        # ======================================================

        if fixed_length == 0:
            if upper_bound and lower_bound:
                self.bounded_constraints(upper_bound, lower_bound)
            elif upper_bound:
                self.lt_constraint(upper_bound)
            elif lower_bound:
                self.gt_constraint(lower_bound)
        else:
            fixed_value = value[:fixed_length]
            has_lt, has_gt = False, False
            if upper_bound and len(upper_bound) >= fixed_length and fixed_value == upper_bound[:fixed_length]:
                has_lt = True
            if lower_bound and len(lower_bound) >= fixed_length and fixed_value == lower_bound[:fixed_length]:
                has_gt = True

            if has_lt and has_gt:
                # Need to handle special cases described in bounded_constraints
                if ord(lower_bound[fixed_length]) + 1 == ord(upper_bound[fixed_length]):
                    self.gt_constraint(lower_bound, offset=fixed_length + 1)
                else:
                    self.lt_constraint(upper_bound, offset=fixed_length)
                    self.gt_constraint(lower_bound, offset=fixed_length)
            elif has_lt:
                self.lt_constraint(upper_bound, offset=fixed_length)
            elif has_gt:
                self.gt_constraint(lower_bound, offset=fixed_length)

            template = Concat(Re(StringVal(fixed_value)), Plus(self._chars))
            self.solver.add(InRe(self.var, template))

    @staticmethod
    def to_python(value):
        if value is not None:
            if isinstance(value, list):
                # Reconstruct a string from a list of Z3 Int ASCII values
                reconstruct_str = str()
                for i in range(StrSynthesizer.DEFAULT_MAX_CHAR_LENGTH):
                    # Only use non-null characters
                    if value[i].as_long() > 0:
                        # chr converts integer to ASCII character
                        reconstruct_str += chr(value[i].as_long())
                # Synthesized value needs no taint
                return SpliceStr(reconstruct_str, trusted=False, synthesized=True, taints=empty_taint())
            else:
                # Synthesized value needs no taint
                return SpliceStr(value.as_string(), trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None

    @staticmethod
    def simple_synthesis(value):
        if value is not None:
            # Synthesized value needs no taint
            return SpliceStr(value, trusted=False, synthesized=True, taints=empty_taint())
        else:
            return None


class DatetimeSynthesizer(FloatSynthesizer):
    """Synthesize a datetime object, subclass from FloatSynthesizer."""
    @staticmethod
    def to_float(value):
        """Convert value (a datetime object) to float."""
        return value.timestamp()

    @staticmethod
    def to_python(value):
        """Convert value (a float object) back to a
        datetime object and return an untrusted value."""
        if value is not None:
            fraction_value = value.as_fraction()
            float_value = float(fraction_value.numerator) / float(fraction_value.denominator)
            dt = datetime.fromtimestamp(float_value)
            # Reconstruct an UntrustedDatetime object from a datetime
            # object requires an indirection (you cannot just pass in
            # datetime value to UntrustedDatetime().
            year = dt.year
            month = dt.month
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            second = dt.second
            microsecond = dt.microsecond
            # Synthesized value needs no taint
            return SpliceDatetime(year=year,
                                  month=month,
                                  day=day,
                                  hour=hour,
                                  minute=minute,
                                  second=second,
                                  microsecond=microsecond,
                                  trusted=False,
                                  synthesized=True,
                                  taints=empty_taint())
        else:
            return None

    @staticmethod
    def simple_synthesis(value):
        if value is not None:
            return DatetimeSynthesizer.to_python(DatetimeSynthesizer.to_float(value))
        else:
            return None


def init_synthesizer(value, vectorized=False):
    """
    Base on the type of value, we determine which synthesizer to use.
    If value is represented by bit vector, then we always init a
    BitVecSynthesizer regardless of the type of the value.
    """
    # TODO: We can probably automate this process in __init__.py
    if vectorized:
        return BitVecSynthesizer()
    elif isinstance(value, SpliceInt):       # Note that int is included
        return IntSynthesizer()
    elif isinstance(value, SpliceStr) or isinstance(value, SpliceUserString):       # Note that str is included
        return StrSynthesizer()
    elif isinstance(value, SpliceFloat):     # Note that float is included
        return FloatSynthesizer()
    #####################################################
    # TODO: Add more casting here for new untrusted types
    elif isinstance(value, SpliceDatetime):
        return DatetimeSynthesizer()
    #####################################################
    else:
        raise NotImplementedError("No corresponding synthesizer is found for type "
                                  "{type}. Consider vectorization.".format(type=type(value)))


def init_synthesizer_on_type(v_type, vectorized=False):
    """
    Base on the given type, we determine which synthesizer to use.
    If value is represented by bit vector, then we always init a
    BitVecSynthesizer regardless of the type of the value.
    """
    # TODO: We can probably automate this process in __init__.py
    if vectorized:
        return BitVecSynthesizer()
    elif v_type is SpliceInt:                # Note that int is included
        return IntSynthesizer()
    elif v_type is SpliceStr or v_type is SpliceUserString:                # Note that str is included
        return StrSynthesizer()
    elif v_type is SpliceFloat:              # Note that float is included
        return FloatSynthesizer()
    #####################################################
    # TODO: Add more casting here for new untrusted types
    elif v_type is SpliceDatetime:
        return DatetimeSynthesizer()
    #####################################################
    else:
        raise NotImplementedError("No corresponding synthesizer is found for type "
                                  "{type}. Consider vectorization.".format(type=v_type))


def int_synthesizer_test():
    synthesizer = IntSynthesizer()
    int_val = synthesizer.bounded_synthesis(upper_bound=92, lower_bound=7)
    assert int_val > 7, "{val} should be larger than 7, but it is not.".format(val=int_val)
    assert int_val < 92, "{val} should be smaller than than 92, but it is not.".format(val=int_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint(34)
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val < 34, "{val} should be smaller than than 34, but it is not.".format(val=int_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint([34, 45, -3])
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val < -3, "{val} should be smaller than than -3, but it is not.".format(val=int_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint(21)
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val > 7, "{val} should be larger than 21, but it is not.".format(val=int_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint([21, 100, -45])
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val > 100, "{val} should be larger than 100, but it is not.".format(val=int_val)

    # Define a simple function that can take Z3's Int type
    def calc(x, *, y):
        """* is needed so that y is a keyed argument!"""
        return x + y * y

    synthesizer.reset_constraints()
    synthesizer.eq_constraint(calc, 40, y=5)  # y is a keyed argument
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val == 15, "{val} should be equal to 15, but it is not.".format(val=int_val)
    synthesizer.reset_constraints()
    synthesizer.ne_constraint(40)
    int_val = synthesizer.to_python(synthesizer.value)
    assert int_val != 40, "{val} should not be equal to 40, but it is.".format(val=int_val)


def float_synthesizer_test():
    synthesizer = FloatSynthesizer()
    float_val = synthesizer.bounded_synthesis(upper_bound=92.6, lower_bound=33.8)
    assert float_val > 33.8, "{val} should be larger than 33.8, but it is not.".format(val=float_val)
    assert float_val < 92.6, "{val} should be smaller than than 92.6, but it is not.".format(val=float_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint(34.5)
    float_val = synthesizer.to_python(synthesizer.value)
    assert float_val < 34.5, "{val} should be smaller than than 34.5, but it is not.".format(val=float_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint(21.45)
    float_val = synthesizer.to_python(synthesizer.value)
    assert float_val > 21.45, "{val} should be larger than 21.45, but it is not.".format(val=float_val)
    synthesizer.reset_constraints()


def str_synthesizer_test():
    synthesizer = StrSynthesizer()
    synthesizer.lt_constraint("A")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val < "A", "{val} should be smaller than 'A', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint("AA")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val < "AA", "{val} should be smaller than 'AA', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint("Jack")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val < "Jack", "{val} should be smaller than than 'Jack', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint("Adam")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val < "Adam", "{val} should be smaller than 'Adam', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint("")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val is None, "{val} should be None, but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint("z")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val > "z", "{val} should be larger than 'z', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint("")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val > "", "{val} should be larger than '', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint("Jack")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val > "Jack", "{val} should be larger than 'Jack', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.gt_constraint("zza")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val > "zza", "{val} should be larger than 'zza', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.le_constraint("")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val <= "", "{val} should be smaller than or equal to '', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.le_constraint("A")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val <= "A", "{val} should be smaller than or equal to 'A', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    synthesizer.ge_constraint("zza")
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val >= "zza", "{val} should be larger than or equal to 'zza', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    str_val = synthesizer.bounded_synthesis(upper_bound="zzzB", lower_bound="zzz")
    assert str_val < "zzzB", "{val} should be smaller than 'zzzB', but it is not.".format(val=str_val)
    assert str_val > "zzz", "{val} should be larger than 'zzz', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    str_val = synthesizer.bounded_synthesis(upper_bound="Luke", lower_bound="Blair")
    assert str_val < "Luke", "{val} should be smaller than 'Luke', but it is not.".format(val=str_val)
    assert str_val > "Blair", "{val} should be larger than 'Blair', but it is not.".format(val=str_val)
    synthesizer.reset_constraints()
    untrusted_str = SpliceStr("Luke")
    synthesizer.eq_constraint(SpliceStr.custom_hash, untrusted_str.__hash__())
    str_val = synthesizer.to_python(synthesizer.value)
    assert str_val.__hash__() == untrusted_str.__hash__(), "{synthesized_val} should have the same hashed value " \
                                                           "as {val}".format(synthesized_val=str_val,
                                                                             val=untrusted_str)
    assert str_val.synthesized, "{val} should be synthesized.".format(val=str_val)


def bitvec_synthesizer_test():
    synthesizer = BitVecSynthesizer()
    synthesizer.gt_constraint(43)  # BitVec supports base class >
    bitvec_val = synthesizer.to_python(synthesizer.value)
    assert bitvec_val > 43, "{val} should be larger than 43, but it is not.".format(val=bitvec_val)
    synthesizer.reset_constraints()
    synthesizer.lt_constraint(25)  # BitVec supports base class <
    bitvec_val = synthesizer.to_python(synthesizer.value)
    assert bitvec_val < 25, "{val} should be smaller than 25, but it is not.".format(val=bitvec_val)
    synthesizer.reset_constraints()
    synthesizer.bounded_synthesis(upper_bound=40, lower_bound=25)
    bitvec_val = synthesizer.to_python(synthesizer.value)
    assert bitvec_val > 25, "{val} should be larger than 25, but it is not.".format(val=bitvec_val)
    assert bitvec_val < 40, "{val} should be smaller than 40, but it is not.".format(val=bitvec_val)

    # Define a hash function
    def shr32(v, *, n):
        """v must be of Z3's BitVec type to support >> and <<."""
        return (v >> n) & ((1 << (32 - n)) - 1)

    synthesizer.reset_constraints()
    synthesizer.eq_constraint(shr32, 0x3E345C, n=2)
    bitvec_val = synthesizer.to_python(synthesizer.value)
    assert shr32(bitvec_val, n=2) == 0x3E345C


if __name__ == "__main__":
    int_synthesizer_test()
    float_synthesizer_test()
    str_synthesizer_test()
    bitvec_synthesizer_test()
