from lib.embeddings import batched


def test_batched():

    # Normal use case
    result = list(batched("ABCDEFG", 3))
    assert result == [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]

    # Edge case: one character string
    result = list(batched("A", 3))
    assert result == [('A',)]

    # Edge case: empty string
    result = list(batched("", 3))
    assert result == []

    # Only one batch
    result = list(batched("ABC", 3))
    assert result == [('A', 'B', 'C')]

    # n larger than the size of the string
    result = list(batched("ABC", 5))
    assert result == [('A', 'B', 'C')]

    # Error case: n is zero
    try:
        result = list(batched("ABC", 0))
    except ValueError as e:
        assert str(e) == "n must be at least one"

    # Error case: n is negative
    try:
        result = list(batched("ABC", -1))
    except ValueError as e:
        assert str(e) == "n must be at least one"
