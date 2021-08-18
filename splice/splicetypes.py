"""Splice classes."""
import socket
import _socket
import subprocess
import io
import os
import asyncio

from decimal import Decimal
from datetime import datetime, date, time, timedelta
from collections import UserString
from contextlib import contextmanager

from .splice import SpliceMixin, SpliceAttrMixin
from .identity import empty_taint, taint_id_from_addr


class SpliceInt(SpliceMixin, int):
    """
    Subclass Python trusted int class and SpliceMixin.
    Note that "trusted" and "synthesized" are *keyed*
    parameters. Construct a trusted int value by default.
    """
    @staticmethod
    def default_hash(input_integer):
        """
        Default hash function if no hash
        function is provided by the user.
        """
        return input_integer % (2 ** 63 - 1)

    custom_hash = default_hash

    @classmethod
    def set_hash(cls, new_hash_func):
        """
        Allows a developer to provide a custom hash
        function. The hash function must take an integer
        and returns an integer. Hash function must be
        Z3 friendly.
        """
        cls.custom_hash = new_hash_func

    def __hash__(self):
        """
        Override hash function to use either our default
        hash or the user-provided hash function. This function
        calls the helper function _untrusted_hash_() so that
        __hash__() output can be decorated.
        """
        return self._splice_hash_()

    def _splice_hash_(self):
        """Called by __hash__() but return a decorated value."""
        return type(self).custom_hash(self)

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return cls(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def unsplicify(self):
        return super().__int__()


class SpliceFloat(SpliceMixin, float):
    """Subclass Python trusted float class and SpliceMixin."""
    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return cls(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def unsplicify(self):
        return super().__float__()


class SpliceStr(SpliceMixin, str):
    """Subclass Python trusted str class and SpliceMixin."""
    @staticmethod
    def default_hash(input_bytes):
        """
        Default hash function if no hash
        function is provided by the user.
        """
        h = 0
        for byte in input_bytes:
            h = h * 31 + byte
        return h

    custom_hash = default_hash

    @classmethod
    def set_hash(cls, new_hash_func):
        """
        Allows a developer to provide a custom hash
        function. The hash function must take a list of
        bytes and returns an integer; each byte should
        represent one character in string (in ASCII).
        Hash function must be Z3 friendly.
        """
        cls.custom_hash = new_hash_func

    # def __hash__(self):
    #     """
    #     Override str hash function to use either
    #     the default or the user-provided hash function.
    #     This function calls the helper function
    #     _untrusted_hash_() so that __hash__() output
    #     can be decorated.
    #     """
    #     return self._splice_hash_()
    #
    # def _splice_hash_(self):
    #     """Called by __hash__() but return a decorated value."""
    #     chars = bytes(self, 'ascii')
    #     return type(self).custom_hash(chars)

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return cls(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def __radd__(self, other):
        """Define __radd__ so a str literal + an untrusted str returns an untrusted str."""
        trusted = self.trusted
        synthesized = self.synthesized
        if isinstance(other, SpliceMixin):
            synthesized |= other.synthesized
            trusted |= other.trusted
        return SpliceStr(other.__add__(self), trusted=trusted, synthesized=synthesized)

    def __iter__(self):
        """Define __iter__ so the iterator returns a splice-aware value."""
        for x in super().__iter__():
            yield SpliceMixin.to_splice(x, self.trusted, self.synthesized, self.taints, self.constraints)

    def unsplicify(self):
        return super().__str__()


class SpliceBytes(SpliceMixin, bytes):
    """Subclass Python builtin bytes class and SpliceMixin."""
    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return SpliceBytes(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def __iter__(self):
        """Define __iter__ so the iterator returns a splice-aware value."""
        for x in super().__iter__():
            yield SpliceMixin.to_splice(x, self.trusted, self.synthesized, self.taints, self.constraints)

    def unsplicify(self):
        return bytes(self)


class SpliceBytearray(SpliceMixin, bytearray):
    """Subclass Python builtin bytearray class and SpliceMixin."""
    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return SpliceBytearray(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def __iter__(self):
        """Define __iter__ so the iterator returns a splice-aware value."""
        for x in super().__iter__():
            yield SpliceMixin.to_splice(x, self.trusted, self.synthesized, self.taints, self.constraints)

    def unsplicify(self):
        return bytearray(self)


class SpliceDecimal(SpliceMixin, Decimal):
    """Subclass Python decimal module's Decimal class and SpliceMixin."""
    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        return SpliceDecimal(value, trusted=trusted, synthesized=synthesized, taints=taints, constraints=constraints)

    def unsplicify(self):
        return Decimal(self)


class SpliceDatetime(SpliceMixin, datetime):
    """
    Subclass Python datetime module's datetime class and SpliceMixin.
    This is an example to showcase it's easy to create a splice-aware
    class from an existing Python class.
    """

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        year = value.year
        month = value.month
        day = value.day
        hour = value.hour
        minute = value.minute
        second = value.second
        microsecond = value.microsecond
        return SpliceDatetime(year=year,
                              month=month,
                              day=day,
                              hour=hour,
                              minute=minute,
                              second=second,
                              microsecond=microsecond,
                              trusted=trusted,
                              synthesized=synthesized,
                              taints=taints,
                              constraints=constraints)

    def unsplicify(self):
        return datetime(year=self.year, month=self.month, day=self.day,
                        hour=self.hour, minute=self.minute, second=self.second,
                        microsecond=self.microsecond)


class SpliceDate(SpliceMixin, date):
    """Subclass Python datetime module's data class and SpliceMixin."""

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        year = value.year
        month = value.month
        day = value.day
        return SpliceDate(year=year,
                          month=month,
                          day=day,
                          trusted=trusted,
                          synthesized=synthesized,
                          taints=taints,
                          constraints=constraints)

    def unsplicify(self):
        return date(year=self.year, month=self.month, day=self.day)


class SpliceTime(SpliceMixin, time):
    """Subclass Python datetime module's time class and SpliceMixin."""

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        hour = value.hour
        minute = value.minute
        second = value.second
        microsecond = value.microsecond
        tzinfo = value.tzinfo
        fold = value.fold
        return SpliceTime(hour=hour,
                          minute=minute,
                          second=second,
                          microsecond=microsecond,
                          tzinfo=tzinfo,
                          fold=fold,
                          trusted=trusted,
                          synthesized=synthesized,
                          taints=taints,
                          constraints=constraints)

    def unsplicify(self):
        return time(hour=self.hour, minute=self.minute, second=self.second,
                    microsecond=self.microsecond, tzinfo=self.tzinfo, fold=self.fold)


class SpliceTimedelta(SpliceMixin, timedelta):
    """Subclass Python datetime module's time class and SpliceMixin."""

    @classmethod
    def splicify(cls, value, trusted, synthesized, taints, constraints):
        """
        Note that only days, seconds and microseconds are stored internally.
        Ref: https://docs.python.org/2/library/datetime.html#timedelta-objects
        """
        days = value.days
        seconds = value.seconds
        microseconds = value.microseconds
        return SpliceTimedelta(days=days,
                               seconds=seconds,
                               microseconds=microseconds,
                               trusted=trusted,
                               synthesized=synthesized,
                               taints=taints,
                               constraints=constraints)

    def unsplicify(self):
        return timedelta(days=self.days, seconds=self.seconds, microseconds=self.microseconds)


class SpliceUserString(UserString):
    # TODO: To complete instrumentation for all
    #  methods defined in UserString.
    def __init__(self, seq):
        if isinstance(seq, SpliceUserString):
            self.taints = seq.taints
            self.synthesized = seq.synthesized
            self.trusted = seq.trusted
            self.data = seq.data[:]
            self._constraints = seq.constraints
        else:
            self.data = str(seq)
            if isinstance(seq, SpliceMixin):
                self.taints = [seq.taints] * len(self.data)
                self.synthesized = [seq.synthesized] * len(self.data)
                self.trusted = [seq.trusted] * len(self.data)
                self._constraints = seq.constraints
                self.data = self.data.unsplicify()
            else:
                self.taints = [empty_taint()] * len(self.data)
                self.synthesized = [False] * len(self.data)
                self.trusted = [True] * len(self.data)
                self._constraints = []

    def __str__(self):
        # REQUIRE: Redefine constraints
        return SpliceStr(self.data, taints=self._sum_taints(), synthesized=self._sum_synthesized(),
                         trusted=self._sum_trusted(), constraints=[])

    def __len__(self):
        return SpliceInt(len(self.data), taints=self._sum_taints(),
                         synthesized=self._sum_synthesized(), trusted=self._sum_trusted(), constraints=[])

    def __getitem__(self, index):
        # REQUIRE: Redefine constraints
        s = self.__class__(self.data[index])
        s.taints = self.taints[index]
        s.synthesized = self.synthesized[index]
        s.trusted = self.trusted[index]
        s._constraints = []
        return s

    def __add__(self, other):
        # REQUIRE: Redefine constraints
        if isinstance(other, SpliceUserString):
            s = self.__class__(self.data + other.data)
            s.taints = self.taints + other.taints
            s.synthesized = self.synthesized + other.synthesized
            s.trusted = self.trusted + other.trusted
            s._constraints = []
            return s
        else:
            other = str(other)
            if isinstance(other, SpliceMixin):
                s = self.__class__(self.data + other.unsplicify())
                s.taints = self.taints + [other.taints] * len(other)
                s.synthesized = self.synthesized + [other.synthesized] * len(other)
                s.trusted = self.trusted + [other.trusted] * len(other)
                s._constraints = []
                return s
            else:
                s = self.__class__(self.data + other)
                s.taints = self.taints + [empty_taint()] * len(other)
                s.synthesized = self.synthesized + [False] * len(other)
                s.trusted = self.trusted + [True] * len(other)
                s._constraints = []
                return s

    def __radd__(self, other):
        # REQUIRE: Redefine constraints
        # TODO: SpliceStr + SpliceUserString will call SpliceStr's __add__,
        #  but SpliceStr's __add__ cannot handle SpliceUserString. To fix
        #  this, however, we need to modify SpliceMixin.
        if isinstance(other, SpliceUserString):
            s = self.__class__(other.data + self.data)
            s.taints = other.taints + self.taints
            s.synthesized = other.synthesized + self.synthesized
            s.trusted = other.trusted + self.trusted
            s._constraints = []
            return s
        else:
            other = str(other)
            if isinstance(other, SpliceMixin):
                s = self.__class__(other.unsplicify() + self.data)
                s.taints = [other.taints] * len(other) + self.taints
                s.synthesized = [other.synthesized] * len(other) + self.synthesized
                s.trusted = [other.trusted] * len(other) + self.trusted
                s._constraints = []
                return s
            else:
                s = self.__class__(other + self.data)
                s.taints = [empty_taint()] * len(other) + self.taints
                s.synthesized = [False] * len(other) + self.synthesized
                s.trusted = [True] * len(other) + self.trusted
                s._constraints = []
                return s

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, constraints):
        if constraints == []:
            self._constraints = []
            return
        if not constraints:
            pass
        elif callable(constraints):
            self._constraints.append(constraints)
        else:
            # A set of callback functions can be provided.
            try:
                cb_iterator = iter(constraints)
            except TypeError:
                raise TypeError("If you want to attach constraints to this Splice object,"
                                "you can either provide a single callable or a collection"
                                "of callables that return maps of concrete constraints.")
            for c in cb_iterator:
                if callable(c):
                    self._constraints.append(c)
                else:
                    raise TypeError("Each constraint must be a callable that returns a map"
                                    "of concrete constraints for Z3 to synthesize.")

    def _sum_taints(self):
        """Helper function to "or" (|) all taints together."""
        taints = empty_taint()
        for taint in self.taints:
            taints |= taint
        return taints

    def _sum_synthesized(self):
        """Helper function to "or" (|) all synthesis flags together."""
        synthesized = False
        # If one character is synthesized, the entire str is synthesized
        for synthsis in self.synthesized:
            synthesized |= synthsis
        return synthesized

    def _sum_trusted(self):
        """Helper function to "and" (&) all trusted flags together."""
        trusted = True
        for trust in self.trusted:
            trusted &= trust
        return trusted


class SpliceSocket(socket.socket, SpliceAttrMixin):
    def __init__(self, *args, taints=None, trusted=True, synthesized=False, **kwargs):
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SpliceSocket object.")
        super().__init__(*args, **kwargs)
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized

    @classmethod
    def copy(cls, sock):
        """
        Copy a valid socket and return a new SpliceSocket
        that is the same as the input socket, except that the
        new SpliceSocket can be tainted.

        Ref: https://stackoverflow.com/questions/45207430/extending-socket-socket-with-a-new-attribute
        """
        fd = _socket.dup(sock.fileno())
        copy = cls(sock.family, sock.type, sock.proto, fileno=fd)
        copy.settimeout(sock.gettimeout())
        return copy

    def accept(self, fn=None):
        """accept(...) -> (socket object, address info)

        This method is similar to socket.socket accept().
        Wait for an incoming connection.  Return a new socket
        representing the connection, and the address of the client.
        For IP sockets, the address info is a pair (hostaddr, port).
        The difference is that, SpliceSocket takes an optional
        fn, which must be a function that takes the address info
        and returns a valid, unique taint mapped to that address.
        The new socket returned is a SpliceSocket.
        """
        conn, addr = super().accept()
        conn = SpliceSocket.copy(conn)
        if fn is None:
            fn = taint_id_from_addr
        conn.taints = fn(addr)
        return conn, addr

    def fileno(self):
        """
        Return the file descriptor of the socket, and the returned
        file descriptor has the same taint information as the socket.
        """
        fno = super().fileno()
        return SpliceInt(fno, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)

    def recv(self, buffersize):
        """Call socket.socket recv but taint the received bytes."""
        data = super().recv(buffersize)
        # Even if a socket is trusted, what is received from a socket is *always* untrusted.
        return SpliceMixin.to_splice(data, trusted=False, synthesized=self.synthesized,
                                     taints=self.taints, constraints=[])

    @contextmanager
    def splice(self):
        """
        A context manager that performs Splice deletion during exit. This gives us a chance
        to do something with the object before it is permanently destroyed by Splice. At
        the point where the generator yields, the block nested in the with statement is executed.
        The generator is then resumed after the block is exited, at which point Splice performs
        deletion (resource clean-up). If an unhandled exception occurs in the block, while it is
        reraised inside the generator at the point where the yield occurred, the generator does
        *not* reraise that exception nor will it log the exception (because we want to make sure
        that nothing can interrupt us from deleting the object).

        We define Splice context managers for all high-level system objects that have more
        complex but known semantics and therefore require special handling. This allows us to
        keep the heap walk code clean when performing Splice deletion.

        Ref: https://docs.python.org/3/library/contextlib.html#module-contextlib
        """
        try:
            yield self
        except:
            # We can optionally do something here if we want to handle some specific exceptions,
            # but in general, there is really nothing we need to do before Splice deletion.
            pass
        finally:
            self.close()
            self.taints = empty_taint()
            self.trusted = False
            self.synthesized = True


class SpliceFileIO(io.FileIO, SpliceAttrMixin):
    def __init__(self, name, mode='r', closefd=True, opener=None, *,
                 taints=None, trusted=True, synthesized=False):
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SpliceFileIO object.")
        super().__init__(name, mode=mode, closefd=closefd, opener=opener)
        # Set up taints and flags for io.FileIO
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized
        self.name = SpliceMixin.to_splice(name, taints=self.taints, synthesized=self.synthesized,
                                          trusted=self.trusted, constraints=[])

    def fileno(self):
        """
        Return the file descriptor of the SpliceFileIO, and the returned
        file descriptor has the same taint information as the SpliceFileIO.
        """
        fno = super().fileno()
        return SpliceInt(fno, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)

    @contextmanager
    def splice(self):
        """See comments above in SpliceSocket.
        """
        try:
            yield self
        except:
            pass
        finally:
            self.close()
            self.taints = empty_taint()
            self.trusted = False
            self.synthesized = True


class SpliceBufferedReader(io.BufferedReader, SpliceAttrMixin):
    def __init__(self, raw, buffer_size=io.DEFAULT_BUFFER_SIZE,
                 *, taints=None, trusted=True, synthesized=False):
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SpliceBufferedReader object.")
        super().__init__(raw, buffer_size)
        # Set up taints and flags for io.BufferedReader
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized
        # The name attribute should inherit taints and flags from the BufferedReader object
        # However, it is not a writable object, so we cannot reassign a Splice object like this:
        # self.name = SpliceMixin.to_splice(self.name, ...)
        # Instead, we override the __getattribute__ method with one that returns the name key
        # of the object's attribute dictionary when the name attribute is requested. Ref:
        # https://stackoverflow.com/questions/60622854/how-to-instantiate-an-io-textiowrapper-object-with-a-name-attribute

    def __getattribute__(self, name):
        if name == 'name':
            name = super().__getattribute__(name)
            if self.synthesized:
                # If SpliceBufferedReader is synthesized, we return a synthesized int value
                return SpliceInt(-1, taints=empty_taint(), synthesized=self.synthesized, trusted=self.trusted)
            return SpliceMixin.to_splice(name, taints=self.taints, synthesized=self.synthesized,
                                         trusted=self.trusted, constraints=[])
        return super().__getattribute__(name)

    def fileno(self):
        """
        Return the file descriptor of the SpliceBufferedReader, and the returned
        file descriptor has the same taint information as the SpliceBufferedReader.
        """
        fno = super().fileno()
        return SpliceInt(fno, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)

    @contextmanager
    def splice(self):
        """See comments above in SpliceSocket.
        """
        try:
            yield self
        except:
            pass
        finally:
            self.close()
            self.taints = empty_taint()
            self.trusted = False
            self.synthesized = True


class SpliceBufferedWriter(io.BufferedWriter, SpliceAttrMixin):
    def __init__(self, raw, buffer_size=io.DEFAULT_BUFFER_SIZE,
                 *, taints=None, trusted=True, synthesized=False):
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SpliceBufferedWriter object.")
        super().__init__(raw, buffer_size)
        # Set up taints and flags for io.BufferedWriter
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized
        # The name attribute should inherit taints and flags from the SpliceBufferedWriter object
        # However, it is not a writable object (See comment in SpliceBufferedReader).

    def __getattribute__(self, name):
        if name == 'name':
            name = super().__getattribute__(name)
            if self.synthesized:
                # If SpliceBufferedWriter is synthesized, we return a synthesized int value
                return SpliceInt(-1, taints=empty_taint(), synthesized=self.synthesized, trusted=self.trusted)
            return SpliceMixin.to_splice(name, taints=self.taints, synthesized=self.synthesized,
                                         trusted=self.trusted, constraints=[])
        return super().__getattribute__(name)

    def fileno(self):
        """
        Return the file descriptor of the SpliceBufferedWriter, and the returned
        file descriptor has the same taint information as the SpliceBufferedWriter.
        """
        fno = super().fileno()
        return SpliceInt(fno, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)

    @contextmanager
    def splice(self):
        """See comments above in SpliceSocket.
        """
        try:
            yield self
        except:
            pass
        finally:
            self.close()
            self.taints = empty_taint()
            self.trusted = False
            self.synthesized = True


class SplicePopen(subprocess.Popen, SpliceAttrMixin):
    def __init__(self, args, bufsize=-1, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=True,
                 shell=False, cwd=None, env=None, universal_newlines=None,
                 startupinfo=None, creationflags=0,
                 restore_signals=True, start_new_session=False,
                 pass_fds=(), *, encoding=None, errors=None,
                 # Splice-specific arguments should be passed in kwargs
                 **kwargs):
        """
        Arguments passed to the constructor are the same as subprocess.Popen.
        Ref: https://chromium.googlesource.com/chromiumos/chromite/+/0.11.241.B/lib/cros_subprocess.py
        """
        trusted = kwargs['trusted'] if 'trusted' in kwargs else True
        synthesized = kwargs['synthesized'] if 'synthesized' in kwargs else False
        taints = kwargs['taints'] if 'taints' in kwargs else empty_taint()
        dp_fn = kwargs['dp_fn'] if 'dp_fn' in kwargs else None
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SplicePopen object.")
        # IMPORTANT NOTE: MULTIPLE CHANGES IN POPEN CONSTRUCTOR DEPENDING ON PYTHON VERSIONS. FOR
        #                 EXAMPLE, SINCE VERSION 3.7, A NEW "TEXT" KEYWORD ARGUMENT IS INCLUDED,
        #                 BUT NOT IN EARLIER VERSIONS! WE DO NOT INCLUDE "TEXT" HERE FOR BACKWARD
        #                 COMPATIBILITY.
        super().__init__(args, bufsize=bufsize, executable=executable,
                         stdin=stdin, stdout=stdout, stderr=stderr,
                         preexec_fn=preexec_fn, close_fds=close_fds,
                         shell=shell, cwd=cwd, env=env, universal_newlines=universal_newlines,
                         startupinfo=startupinfo, creationflags=creationflags,
                         restore_signals=restore_signals, start_new_session=start_new_session,
                         pass_fds=pass_fds, encoding=encoding, errors=errors)
        # Set up taints and flags for Popen
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized
        self.dp_fn = dp_fn
        # Some of its attributes inherit taints and flags from the Popen object
        self.args = [SpliceStr(arg, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)
                     for arg in self.args]
        self.pid = SpliceInt(self.pid, taints=self.taints, trusted=self.trusted, synthesized=self.synthesized)
        # Reconstruct stdin/stdout/stderr for Splice
        if self.stdout is not None:
            # Case: PIPE
            if isinstance(self.stdout, io.BufferedReader):
                fd = os.dup(self.stdout.raw.fileno())
                # raw = io.FileIO(fd, 'rb')
                raw = SpliceFileIO(fd, 'rb')
                self.stdout = SpliceBufferedReader(raw, taints=self.taints,
                                                   trusted=self.trusted, synthesized=self.synthesized)
            elif isinstance(self.stdout, io.FileIO):
                fd = os.dup(self.stdout.fileno())
                self.stdout = SpliceFileIO(fd, 'rb', taints=self.taints,
                                           trusted=self.trusted, synthesized=self.synthesized)
        if self.stderr is not None:
            # Case: PIPE
            if isinstance(self.stderr, io.BufferedReader):
                fd = os.dup(self.stderr.raw.fileno())
                # raw = io.FileIO(fd, 'rb')
                raw = SpliceFileIO(fd, 'rb')
                self.stderr = SpliceBufferedReader(raw, taints=self.taints,
                                                   trusted=self.trusted, synthesized=self.synthesized)
            elif isinstance(self.stderr, io.FileIO):
                fd = os.dup(self.stderr.fileno())
                self.stderr = SpliceFileIO(fd, 'rb', taints=self.taints,
                                           trusted=self.trusted, synthesized=self.synthesized)
        if self.stdin is not None:
            # Case: PIPE
            if isinstance(self.stdin, io.BufferedWriter):
                fd = os.dup(self.stdin.raw.fileno())
                # raw = io.FileIO(fd, 'wb')
                raw = SpliceFileIO(fd, 'wb')
                self.stdin = SpliceBufferedWriter(raw, taints=self.taints,
                                                  trusted=self.trusted, synthesized=self.synthesized)
            elif isinstance(self.stdin, io.FileIO):
                fd = os.dup(self.stdin.fileno())
                self.stdin = SpliceFileIO(fd, 'wb', taints=self.taints,
                                          trusted=self.trusted, synthesized=self.synthesized)
        # Note that returncode is None until the process finishes, so no Splice wrapping necessary in __init__

    @contextmanager
    def splice(self):
        """See comments above in SpliceSocket.
        """
        try:
            yield self
        except:
            pass
        finally:
            self.kill()
            self.wait()
            # dp_fn is a function hook where developers can provide custom
            # function for post-processing as a form of defensive programming
            if self.dp_fn:
                self.dp_fn(self)
            self.taints = empty_taint()
            self.synthesized = True
            self.trusted = False
            self.pid = SpliceInt(-1, synthesized=True, trusted=False)
            # TODO: randomize returncode value instead of returning SIGKILL?
            self.returncode = SpliceInt(9, synthesized=True, trusted=False)
            # TODO: randomize args value instead of None?
            self.args = None


class SpliceTask(asyncio.Task, SpliceAttrMixin):
    """A coroutine wrapped in a Future. Same as asyncio.Task but tainted."""
    def __init__(self, coro, *, loop=None, name=None,
                 # Splice-specific arguments
                 taints=None, trusted=True, synthesized=False):
        if trusted and synthesized:
            raise AttributeError("Cannot initialize a trusted and synthesized SpliceTask object.")
        super().__init__(coro, loop=loop, name=name)
        # Set up taints and flags for Task
        if taints is None:
            self._taints = empty_taint()
        else:
            self._taints = taints
        self._trusted = trusted
        self._synthesized = synthesized

    @contextmanager
    def splice(self):
        """See comments above in SpliceSocket.
        """
        try:
            yield self
        except:
            pass
        finally:
            self.cancel()
            self.taints = empty_taint()
            self.synthesized = True
            self.trusted = False


if __name__ == "__main__":
    pass
