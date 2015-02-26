import utils

import pytest

@pytest.fixture(scope='function')
def recorded_calls():
    return utils.RecordedCalls()
