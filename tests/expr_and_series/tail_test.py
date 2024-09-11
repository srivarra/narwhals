from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest

import narwhals as nw
from tests.utils import compare_dicts


@pytest.mark.parametrize("n", [2, -1])
def test_tail_expr(constructor: Any, n: int, request: Any) -> None:
    if ("polars" in str(constructor)) and n < 0:
        request.applymarker(pytest.mark.xfail)

    context = (
        pytest.raises(
            NotImplementedError,
            match="`Expr.tail` is not supported for Dask backend with multiple partitions.",
        )
        if "dask_lazy_p2" in str(constructor)
        else does_not_raise()
    )

    with context:
        df = nw.from_native(constructor({"a": [1, 2, 3]}))
        result = df.select(nw.col("a").tail(n))
        expected = {"a": [2, 3]}
        compare_dicts(result, expected)


@pytest.mark.parametrize("n", [2, -1])
def test_tail_series(constructor_eager: Any, n: int) -> None:
    s = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)["a"]
    result = {"a": s.tail(n)}
    expected = {"a": [2, 3]}
    compare_dicts(result, expected)
