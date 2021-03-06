# ~*~ coding: utf-8 ~*~
"""
String-related functions and classes.
"""
from numbers import Integral
from random import choice, randint
import re
import string

from taipan._compat import IS_PY3, ifilter, imap, xrange
from taipan.collections import ensure_iterable, is_iterable, is_mapping
from taipan.collections.tuples import is_pair
from taipan.functional import ensure_keyword_args


__all__ = [
    'BaseString', 'UnicodeString', 'is_string', 'ensure_string',
    'Regex', 'is_regex', 'ensure_regex',
    'trim',
    'split', 'join',
    'camel_case',
    'replace', 'Replacer', 'ReplacementError',
    'random',
]


#: Base string class used by this Python interpreter.
#:
#: For every string class X, the ``isubclass(X, BaseString)`` is always true.
#: (This includes the :class:`BaseString` itself.)
BaseString = str if IS_PY3 else basestring

#: Unicode string class used by this Python interpreter.
UnicodeString = str if IS_PY3 else unicode

#: Regular expression class.
Regex = type(re.compile(''))


# Kind checks

def is_string(s):
    """Checks whether given object ``s`` is a string of characters.
    :return: ``True`` if ``s`` is a string, ``False`` otherwise
    """
    return isinstance(s, BaseString)


def is_regex(r):
    """Checks whether given object ``r`` is a compiled regular expression.
    :return: ``True`` is ``r`` is a regular expression object,
             ``False`` otherwise
    """
    return isinstance(r, Regex)


# Assertions

def ensure_string(s):
    """Checks whether ``s`` is a string of characters.
    :return: ``s`` if it is a string of characters
    :raise TypeError: When ``s` is not a string of characters
    """
    if not is_string(s):
        raise TypeError("expected a string, got %s" % type(s).__name__)
    return s


def ensure_regex(r):
    """Checks whether ``r`` is a compiled regular expression.
    :return: ``r`` if it is a regular expression object
    :raise TypeError: When ``s`` is not a regular expression object
    """
    if not is_regex(r):
        raise TypeError(
            "expected a regular expression, got %s" % type(r).__name__)
    return r


# String manipulation

def trim(s, prefix=None, suffix=None, strict=False):
    """Trim a string, removing given prefix or suffix.

    :param s: String to trim
    :param prefix: Prefix to remove from ``s``
    :param suffix: Suffix to remove from ``s``
    :param strict: Whether the prefix or suffix must be present in ``s``.
                   By default, if the infix is not found, function will simply
                   return the string passed.

    Either ``prefix`` or ``suffix`` must be provided, but not both
    (which would be ambiguous as to what to remove first).

    :raise ValueError: If ``strict`` is True and required prefix or suffix
                       was not found

    Examples::

        trim('foobar', prefix='foo')  # 'bar'
        trim('foobar', suffix='bar')  # 'foo'
        trim('foobar', prefix='baz', strict=True)  # exception

    .. versionadded:: 0.0.4
    """
    ensure_string(s)

    has_prefix = prefix is not None
    has_suffix = suffix is not None
    if has_prefix == has_suffix:
        raise ValueError(
            "exactly one of either prefix or suffix must be provided")

    if has_prefix:
        ensure_string(prefix)
        if s.startswith(prefix):
            return s[len(prefix):]
        elif strict:
            raise ValueError(
                "string %r does not start with expected prefix %r" % (
                    s, prefix))

    if has_suffix:
        ensure_string(suffix)
        if s.endswith(suffix):
            return s[:-len(suffix)] if suffix else s
        elif strict:
            raise ValueError(
                "string %r does not end with expected suffix %r" % (
                    s, suffix))

    return s


# Splitting and joining

def split(s, by=None, maxsplit=None):
    """Split a string based on given delimiter(s).
    Delimiters can be either strings or compiled regular expression objects.

    :param s: String to split
    :param by: A delimiter, or iterable thereof.
    :param maxsplit: Maximum number of splits to perform.
                     ``None`` means no limit,
                     while 0 does not perform a split at all.

    :return: List of words in the string ``s``
             that were separated by delimiter(s)

    :raise ValueError: If the separator is an empty string or regex
    """
    ensure_string(s)

    # TODO(xion): Consider introducing a case for ``split('')``
    # to make it return ``['']`` rather than default ``[]`` thru ``str.split``.
    # It's the so-called "whitespace split" that normally eliminates
    # empty strings from result. However, ``split(s)`` for any other ``s``
    # always returns ``[s]`` so these two approaches are at odds here.
    # (Possibly refer to split functions in other languages for comparison).

    # string delimiter are handled by appropriate standard function
    if by is None or is_string(by):
        return s.split(by) if maxsplit is None else s.split(by, maxsplit)

    # regex delimiters have certain special cases handled explicitly below,
    # so that we do the same things that ``str.split`` does
    if is_regex(by):
        if not by.pattern:
            return s.split('')  # will fail with proper exception & message
        if maxsplit == 0:
            return [s]
        return by.split(s, maxsplit=maxsplit or 0)

    # multiple delimiters are handled by regex that matches them all
    if is_iterable(by):
        if not by:
            raise ValueError("empty separator list")
        by = list(imap(ensure_string, by))
        if not s:
            return ['']  # quickly eliminate trivial case
        or_ = s.__class__('|')
        regex = join(or_, imap(re.escape, by))
        return split(s, by=re.compile(regex), maxsplit=maxsplit)

    raise TypeError("invalid separator")


def join(delimiter, iterable, **kwargs):
    """Returns a string which is a concatenation of strings in ``iterable``,
    separated by given ``delimiter``.

    :param delimiter: Delimiter to put between strings
    :param iterable: Iterable to join

    Optional keyword arguments control the exact joining strategy:

    :param errors:
        What to do with erroneous non-strings in the input.
        Possible values include:

            * ``'ignore'`` (or ``None``)
            * ``'cast'`` (or ``False``) -- convert non-strings to strings
            * ``'raise'`` (or ``True``) -- raise exception for any non-strings
            * ``'replace'`` -- replace non-strings with alternative value

    :param with_: Replacement used when ``errors == 'replace'``.
                  This can be a string, or a callable taking erroneous value
                  and returning a string replacement.

    .. versionadded:: 0.0.3
       Allow to specify error handling policy through ``errors`` parameter
    """
    ensure_string(delimiter)
    ensure_iterable(iterable)

    ensure_keyword_args(kwargs, optional=('errors', 'with_'))
    errors = kwargs.get('errors', True)

    if errors in ('raise', True):
        iterable = imap(ensure_string, iterable)
    elif errors in ('ignore', None):
        iterable = ifilter(is_string, iterable)
    elif errors in ('cast', False):
        iterable = imap(delimiter.__class__, iterable)
    elif errors == 'replace':
        if 'with_' not in kwargs:
            raise ValueError("'replace' error policy requires specifying "
                             "replacement through with_=")

        with_ = kwargs['with_']
        if is_string(with_):
            replacement = lambda x: with_
        elif callable(with_):
            replacement = with_
        else:
            raise TypeError("error replacement must be a string or function, "
                            "got %s" % type(with_).__name__)

        iterable = (x if is_string(x) else ensure_string(replacement(x))
                    for x in iterable)
    else:
        raise TypeError(
            "%r is not a valid error handling policy for join()" % (errors,))

    return delimiter.join(iterable)


# Case conversion

# TODO(xion): expand into a full-featured API for converting between different
# type of case formats, comparable to Guava's CaseFormat:
# http://code.google.com/p/guava-libraries/wiki/StringsExplained#CaseFormat

def camel_case(arg, capitalize=None):
    """Converts given text with whitespaces between words
    into equivalent camel-cased one.

    :param capitalize: Whether result will have first letter upper case (True),
                       lower case (False), or left as is (None, default).

    :return: String turned into camel-case "equivalent"
    """
    ensure_string(arg)
    if not arg:
        return arg

    words = split(arg)
    first_word = words[0] if len(words) > 0 else None

    words = [word.capitalize() for word in words]
    if first_word is not None:
        if capitalize is True:
            first_word = first_word.capitalize()
        elif capitalize is False:
            first_word = first_word[0].lower() + first_word[1:]
        words[0] = first_word

    return join(arg.__class__(), words)


# String replacement

def replace(needle, with_=None, in_=None):
    """Replace occurrences of string(s) with other string(s) in (a) string(s).

    Unlike the built in :meth:`str.replace` method, this function provides
    clean API that clearly distinguishes the "needle" (string to replace),
    the replacement string, and the target string to perform replacement in
    (the "haystack").

    Additionally, a simultaneous replacement of several needles is possible.
    Note that this is different from performing multiple separate replacements
    one after another.

    Examples::

        replace('foo', with_='bar', in_=some_text)
        replace('foo', with_='bar').in_(other_text)
        replace('foo').with_('bar').in_(another_text)
        replace(['foo', 'bar']).with_('baz').in_(perhaps_a_long_text)
        replace({'foo': 'bar', 'baz': 'qud'}).in_(even_longer_text)

    :param needle: String to replace, iterable thereof,
                   or a mapping from needles to corresponding replacements
    :param with_: Replacement string, if ``needle`` was not a mapping
    :param in_: Optional string to perform replacement in

    :return: If all parameters were provided, result is the final string
             after performing a specified replacement.
             Otherwise, a :class:`Replacer` object is returned, allowing
             e.g. to perform the same replacements in many haystacks.
    """
    if needle is None:
        raise TypeError("replacement needle cannot be None")
    if not needle:
        raise ValueError("replacement needle cannot be empty")

    if is_string(needle):
        replacer = Replacer((needle,))
    else:
        ensure_iterable(needle)
        if not is_mapping(needle):
            if all(imap(is_pair, needle)):
                needle = dict(needle)
            elif not all(imap(is_string, needle)):
                raise TypeError("invalid replacement needle")
        replacer = Replacer(needle)

    if with_ is not None:
        ensure_string(with_)
        replacer = replacer.with_(with_)

    if in_ is not None:
        ensure_string(in_)
        return replacer.in_(in_)

    return replacer


class ReplacementError(ValueError):
    """Exception raised when string replacement error occurrs."""


class Replacer(object):
    """Replaces occurrences of string(s) with some other string(s),
    within given string(s).

    This class handles both simple, single-pass replacements,
    as well as multiple replacement pair mappings.

    .. note::

        This class is not intended for direct use by client code.
        Use the provided :func:`replace` function instead.
    """
    def __init__(self, replacements):
        """Constructor.

        :param replacements: Iterable of needles, or mapping of replacements.

                             If this is not a mapping, a :meth:`with_` method
                             must be called to provide target replacement(s)
                             before :meth:`in_` is called
        """
        self._replacements = ensure_iterable(replacements)

    def with_(self, replacement):
        """Provide replacement for string "needles".

        :param replacement: Target replacement for needles given in constructor
        :return: The :class:`Replacement` object

        :raise TypeError: If ``replacement`` is not a string
        :raise ReplacementError: If replacement has been already given
        """
        ensure_string(replacement)
        if is_mapping(self._replacements):
            raise ReplacementError("string replacements already provided")

        self._replacements = dict.fromkeys(self._replacements, replacement)
        return self

    def in_(self, haystack):
        """Perform replacement in given string.

        :param haystack: String to perform replacements in

        :return: ``haystack`` after the replacements

        :raise TypeError: If ``haystack`` if not a string
        :raise ReplacementError: If no replacement(s) have been provided yet
        """
        from taipan.collections import dicts

        ensure_string(haystack)
        if not is_mapping(self._replacements):
            raise ReplacementError("string replacements not provided")

        # handle special cases
        if not self._replacements:
            return haystack
        if len(self._replacements) == 1:
            return haystack.replace(*dicts.peekitem(self._replacements))

        # construct a regex matching any of the needles in the order
        # of descending length (to prevent issues if they contain each other)
        or_ = haystack.__class__('|')
        regex = join(or_, imap(
            re.escape, sorted(self._replacements, key=len, reverse=True)))

        # do the substituion, looking up the replacement for every match
        do_replace = lambda match: self._replacements[match.group()]
        return re.sub(regex, do_replace, haystack)


# Other

def random(length, chars=None):
    """Generates a random string.

    :param length: Length of the string to generate.
                   This can be a numbe or a pair: ``(min_length, max_length)``
    :param chars: String of characters to choose from
    """
    if chars is None:
        chars = string.ascii_letters + string.digits
    else:
        ensure_string(chars)
        if not chars:
            raise ValueError("character set must not be empty")

    if is_pair(length):
        length = randint(*length)
    elif isinstance(length, Integral):
        if not length > 0:
            raise ValueError(
                "random string length must be positive (got %r)" % (length,))
    else:
        raise TypeError("random string length must be an integer; "
                        "got '%s'" % type(length).__name__)

    return join(chars.__class__(), (choice(chars) for _ in xrange(length)))
