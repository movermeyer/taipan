"""
Additional asserts to supplement the :class:`TestCase` class.
"""
from taipan._compat import imap
from taipan.collections import is_countable, is_iterable
from taipan.lang import ABSENT
from taipan.strings import BaseString, is_string


__all__ = ['AssertsMixin']


class AssertsMixin(object):
    """Mixin providing additional assert methods."""

    def assertZero(self, argument, msg=None):
        """Assert that ``argument`` is equal to zero."""
        if msg is None:
            msg = "%r is not equal to zero" % (argument,)
        self.assertEqual(0, argument, msg=msg)

    def assertEmpty(self, argument, msg=None):
        """Assert that ``argument`` is an empty collection."""
        if is_countable(argument):
            nonempty = len(argument) > 0
        else:
            if not is_iterable(argument):
                self.__fail(msg, "%r is not an iterable" % (argument,))

            nonempty = False
            for _ in argument:
                nonempty = True
                break

        if nonempty:
            self.__fail(msg, "%r is not empty" % (argument,))

    def assertNotEmpty(self, argument, msg=None):
        """Assert that ``argument`` is not an empty collection."""
        if is_countable(argument):
            empty = len(argument) == 0
        else:
            if not is_iterable(argument):
                self.__fail(msg, "%r is not an iterable" % (argument,))

            empty = True
            for _ in argument:
                empty = False
                break

        if empty:
            self.__fail(msg, "%r is empty" % (argument,))

    def assertStartsWith(self, prefix, string, msg=None):
        """Assert that ``string`` starts with given ``prefix``."""
        self.__fail_unless_strings(prefix)
        self.assertIsInstance(string, BaseString)
        if not string.startswith(prefix):
            self.__fail(msg, "%r does not start with %r" % (string, prefix))

    def assertEndsWith(self, suffix, string, msg=None):
        """Assert that ``string`` ends with given ``suffix``."""
        self.__fail_unless_strings(suffix)
        self.assertIsInstance(string, BaseString)
        if not string.endswith(suffix):
            self.__fail(msg, "%r does not end with %r" % (string, suffix))

    def assertIsSubclass(self, class_, superclass, msg=None):
        """Assert that ``class_`` inherits from given ``superclass``.
        .. versionadded:: 0.0.3
        """
        for c in (class_, superclass):
            if not isinstance(c, type):
                self.fail("%r is not a class" % (c,))
        if not issubclass(class_, superclass):
            self.__fail(
                msg, "%r is not a subclass of %r" % (class_, superclass))

    def assertHasAttr(self, attr, obj, msg=None):
        """Assert that ``obj``\ ect has given ``attr``\ ibute."""
        self.assertIsInstance(attr, BaseString)
        if not attr:
            self.fail("attribute name is empty")

        if not hasattr(obj, attr):
            self.__fail(msg, "%r does not have attribute %r" % (obj, attr))

    def assertThat(self, predicate, argument=ABSENT, msg=None):
        """Assert that a ``predicate`` applies to given ``argument``.

        Example::

            self.assertThat(is_pair, some_tuple)
        """
        if not callable(predicate):
            self.fail("%r is not a callable predicate" % (predicate,))

        satisfied = predicate() if argument is ABSENT else predicate(argument)

        if not satisfied:
            argument_part = ("" if argument is ABSENT
                             else " for %r" % (argument,))
            self.__fail(msg, "predicate not satisfied%s" % (argument_part,))

    def assertAll(self, arg, iterable=ABSENT, msg=None):
        """Assert that all elements of an iterable are truthy
        or satisfy given predicate.

        :param arg: Predicate, or iterable of elements to check for truthiness
        :param iterable: Iterable of predicate arguments
                         (if predicate was given)

        Examples::

            # check if all elements satisfy a predicate
            self.assertAll(is_valid, iterable)

            # check if all elements are already truthy
            self.assertAll(iterable_of_maybe_truthies)
        """
        if callable(arg):
            self.__fail_unless_iterable(iterable)

            predicate = arg
            for i, elem in enumerate(iterable):
                if not predicate(elem):
                    self.__fail(
                        msg, "predicate not satisfied for element #%d: %r" % (
                            i, elem))
        else:
            self.__fail_unless_iterable(arg)

            # shift arguments to the left
            if msg is None and iterable is not ABSENT:
                msg = iterable
            iterable = arg

            for i, elem in enumerate(iterable):
                if not elem:
                    self.__fail(msg, "falsy element #%d: %r" % (i, elem))

    def assertAny(self, arg, iterable=ABSENT, msg=None):
        """Assert that at least one element of an iterable is truthy
        or satisfies given predicate.

        :param arg: Predicate, or iterable of elements to check for truthiness
        :param iterable: Iterable of predicate arguments
                         (if predicate was given)

        Examples::

            # check if any element satisfies a predicate
            self.assertAny(is_valid, iterable)

            # check if any element is already truthy
            self.assertAny(iterable_of_maybe_truthies)
        """
        if callable(arg):
            self.__fail_unless_iterable(iterable)
            if not any(imap(arg, iterable)):
                self.__fail(msg, "predicate not satisfied for any element")
        else:
            self.__fail_unless_iterable(arg)

            # shift arguments to the left
            if msg is None and iterable is not ABSENT:
                msg = iterable

            if not any(arg):
                self.__fail(msg, "no truthy elements found")

    def assertNoop(self, function, argument, msg=None):
        """Assert that ``function`` returns given ``argument`` verbatim
        when applied to it.

        Example::

            self.assertNoop(str.upper, "WAT")
        """
        if not callable(function):
            self.fail("%r is not a callable" % (function,))

        result = function(argument)
        if result != argument:
            self.__fail(
                msg, "result %r of function %r differs from argument %r" % (
                    result, function, argument))

    def assertResultsEqual(self, func1, func2, msg=None):
        """Assert that both functions evaluate to the same result."""
        self.__fail_unless_callable(func1)
        self.__fail_unless_callable(func2)

        self.assertEqual(func1(), func2(), msg=msg)

    # Utility functions

    def __fail(self, custom_msg, standard_msg):
        self.fail(self._formatMessage(custom_msg, standard_msg))

    def __fail_unless_iterable(self, arg):
        if not is_iterable(arg):
            self.fail("%r is not an iterable" % (arg,))

    def __fail_unless_callable(self, arg):
        if not callable(arg):
            self.fail("%r is not a callable" % (arg,))

    def __fail_unless_strings(self, arg):
        """Fail the test unless argument is a string or iterable thereof."""
        if not is_string(arg):
            if not (is_iterable(arg) and all(imap(is_string, arg))):
                self.fail("%r is not a string or iterable of strings" % (arg,))
