"""
Test case class with additional enhancements.
"""
from taipan._compat import IS_PY3, metaclass
from taipan.collections import dicts
from taipan.functional.functions import attr_func
from taipan.testing._unittest import TestCase as _TestCase
from taipan.testing.asserts import AssertsMixin
from taipan.testing.decorators import _StageMethod


__all__ = ['TestCase']


class TestCaseMetaclass(type):
    """Metaclass for :class:`TestCase`.

    Its purpose is to interpret the methods adorned with test stage decorators
    and construct the appropriate :func:`setUp`, etc. methods which invoke them
    in the right order.
    """
    CLASS_STAGES = ('setUpClass', 'tearDownClass')
    INSTANCE_STAGES = ('setUp', 'tearDown')

    def __new__(meta, name, bases, dict_):
        """Create the new subclass of :class:`TestCase`."""
        super_ = (bases[0] if bases else object).__mro__[0]

        # for every test stage, gather methods adorned with its decorator,
        # sort them by definition order and construct final stage method
        for stage in meta.CLASS_STAGES + meta.INSTANCE_STAGES:
            stage_method_wrappers = [
                mw for mw in dicts.itervalues(dict_)
                if isinstance(mw, _StageMethod) and mw.stage == stage
            ]
            if not stage_method_wrappers:
                continue  # no stage methods, may be custom setUp/tearDown/etc.

            # if setUp/tearDown/etc. method was defined AND corresponding
            # decorator used, then it's impossible to resolve proper runtime
            # order of those two approaches, so we report that as an error
            if stage in dict_:
                raise RuntimeError(
                    "ambiguous test stage: either define {stage}() method or "
                    "use @{stage} decorator".format(stage=stage))

            stage_method_wrappers.sort(key=attr_func('order'))
            methods = [mw.method for mw in stage_method_wrappers]
            dict_[stage] = meta._create_stage_method(stage, methods, super_)

        return super(TestCaseMetaclass, meta).__new__(meta, name, bases, dict_)

    @classmethod
    def _create_stage_method(meta, stage, methods, super_):
        """Create method for given test stage.

        :param stage: Test stage string identifier, e.g. ``'setUp'``
        :param methods: List of methods to be executed at that stage
        :param super_: Superclass to delegate to ``super`` calls to

        :return: Function that invokes all ``methods`` in given order.
        """
        def invoke_methods(target):
            for method in methods:
                method(target)

        is_setup = stage.startswith('setUp')
        is_teardown = stage.startswith('tearDown')

        if stage in meta.CLASS_STAGES:
            def class_method(cls):
                if is_setup:
                    getattr(super_, stage)()
                invoke_methods(cls)
                if is_teardown:
                    getattr(super_, stage)()

            class_method.__name__ = stage
            class_method = classmethod(class_method)
            return class_method

        if stage in meta.INSTANCE_STAGES:
            def instance_method(self):
                if is_setup:
                    getattr(super_, stage)(self)
                invoke_methods(self)
                if is_teardown:
                    getattr(super_, stage)(self)

            instance_method.__name__ = stage
            return instance_method

        raise ValueError("invalid test stage identifier: %r" % (stage,))


@metaclass(TestCaseMetaclass)
class TestCase(_TestCase, AssertsMixin):
    """Augmented test case class.

    Includes few additional, convenience assertion methods,
    as well as the capability to use test stage decorators,
    such as :func:`setUp` and :func:`tearDown`.
    """
    # Python 3 changes name of the following assert function,
    # so we provide backward and forward synonyms for compatibility
    if IS_PY3:
        assertItemsEqual = _TestCase.assertCountEqual
    else:
        assertCountEqual = _TestCase.assertItemsEqual
