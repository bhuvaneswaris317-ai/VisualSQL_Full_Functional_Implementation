import pytest
from query_validator import validate, InvalidQuery, valid_identifier
from benchmark import improvement

def test_valid(): assert validate("SELECT * FROM employees;").startswith("SELECT")
@pytest.mark.parametrize("q", ["", "  ", "DROP TABLE employees", "SELECT 1; DELETE FROM employees", "UPDATE employees SET salary=1"])
def test_rejected(q):
    with pytest.raises(InvalidQuery): validate(q)
def test_identifier():
    assert valid_identifier("user_x1")
    with pytest.raises(InvalidQuery): valid_identifier("a; DROP")
def test_improvement(): assert improvement(100, 25) == 75 and improvement(0, 5) == 0
