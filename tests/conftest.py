import pytest


@pytest.fixture
def dict_change_logger():
    from tests.dict_change_logger import DictChangeLogger
    return DictChangeLogger()
