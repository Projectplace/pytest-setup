import py
import pytest

pytest_plugins = 'pytester'

USER_CLASS = """
class BaseUser(object):
    def __init__(self, user_name, identifier):
        self._user_name = user_name
        self._identifier = identifier

    @property
    def user_name(self):
        return self._user_name

    @property
    def identifier(self):
        return self._identifier

    SIGNATURE = {'name': str}

    @classmethod
    def create(cls, name):
        return cls(name, name)

class User(BaseUser):
    def __init__(self, user_name, identifier):
        super(User, self).__init__(user_name, identifier)
        self._owner = Owner.create(user_name + "s Ownah")

    @property
    def default_representations(self):
        return [self._owner]

class Owner(BaseUser):
    def __init__(self, user_name, identifier):
        super(Owner, self).__init__(user_name, identifier)
"""


@pytest.fixture()
def repren(request, testdir):
    testdir.makepyfile(__init__="""""")
    testdir.makefile('.ini', pytest="""
        [pytest]
        representation_path = {}0/repr
    """.format(request.function.__name__))
    repr_dir = testdir.mkdir('repr')
    repr_dir.join('__init__.py').write(py.code.Source("""
        from .user import BaseUser, User, Owner
        """))
    repr_dir.join('user.py').write(py.code.Source(USER_CLASS))
    return testdir


def assert_outcomes(result, passed=1, skipped=0, deselected=0, failed=0,
                    xfailed=0, xpassed=0):
    outcomes = result.parseoutcomes()
    assert outcomes.get('passed', 0) == passed
    assert outcomes.get('skipped', 0) == skipped
    assert outcomes.get('deselected', 0) == deselected
    assert outcomes.get('failed', 0) == failed
    assert outcomes.get('xfailed', 0) == xfailed
    assert outcomes.get('xpassed', 0) == xpassed


def test_function_setup(repren):
    repren.makepyfile("""
        import pytest
        @pytest.mark.setup_data({'User': [{'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


def test_module_setup(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Bob'}]}]

        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier
    """)
    import os
    for root, _dir, _file in os.walk(os.getcwd()):
        print("root", root)
        print("dir", _dir)
        print("file", _file)
    result = repren.runpytest()
    assert_outcomes(result)


def test_multiple_func(repren):
    repren.makepyfile("""
        import pytest
        @pytest.mark.setup_data({'User': [{'name': 'Bob'}, {'name': 'Rob'}]})
        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier

            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


def test_multiple_module(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Bob'}, {'name': 'Rob'}]}]

        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier

            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


def test_combined(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Rob'}]}]

        @pytest.mark.setup_data({'User': [{'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier

            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


def test_func_scope(repren):
    repren.makepyfile("""
        import pytest
        @pytest.mark.setup_data({'User': [{'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier

        @pytest.mark.xfail()
        def test_xfail(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
    """)
    result = repren.runpytest()
    assert_outcomes(result, xfailed=1)


def test_module_scope(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Rob'}]}]

        def test_pass(test_db):
            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier

        def test_pass2(test_db):
            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result, passed=2)


@pytest.mark.xfail()
def test_no_duplicates_func(repren):
    repren.makepyfile("""
        import pytest
        @pytest.mark.setup_data({'User': [{'name': 'Bob'}, {'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Bob' in test_db.get('User', 'Bob').user_name
            assert 'Bob' in test_db.get('User', 'Bob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


@pytest.mark.xfail()
def test_no_duplicates_module(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Rob'}, {'name': 'Rob'}]}]

        def test_pass(test_db):
            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


@pytest.mark.xfail()
def test_no_duplicates_combined(repren):
    repren.makepyfile("""
        import pytest

        module_setup_data = [{'User': [{'name': 'Rob'}, {'name': 'Rob'}]}]

        @pytest.mark.setup_data({'User': [{'name': 'Bob'}, {'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Rob' in test_db.get('User', 'Rob').user_name
            assert 'Rob' in test_db.get('User', 'Rob').identifier
    """)
    result = repren.runpytest()
    assert_outcomes(result)


def test_default_repren(repren):
    repren.makepyfile("""
        import pytest

        @pytest.mark.setup_data({'User': [{'name': 'Bob'}]})
        def test_pass(test_db):
            assert 'Bobs Ownah' in test_db.get('Owner',
                'Bobs Ownah').user_name
            assert 'Bobs Ownah' in test_db.get('Owner',
                'Bobs Ownah').identifier
            assert test_db.get('Owner', 'Bobs Ownah') == \
            test_db.get('User', 'Bob')._owner
    """)
    result = repren.runpytest()
    assert_outcomes(result)
