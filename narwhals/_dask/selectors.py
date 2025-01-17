from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import NoReturn

from narwhals._dask.expr import DaskExpr
from narwhals.utils import import_dtypes_module

if TYPE_CHECKING:
    try:
        import dask.dataframe.dask_expr as dx
    except ModuleNotFoundError:
        import dask_expr as dx

    from collections.abc import Collection
    from collections.abc import Container
    from datetime import timezone

    from typing_extensions import Self

    from narwhals._dask.dataframe import DaskLazyFrame
    from narwhals.dtypes import DType
    from narwhals.typing import TimeUnit
    from narwhals.utils import Version


class DaskSelectorNamespace:
    def __init__(
        self: Self, *, backend_version: tuple[int, ...], version: Version
    ) -> None:
        self._backend_version = backend_version
        self._version = version

    def by_dtype(self: Self, dtypes: Container[DType | type[DType]]) -> DaskSelector:
        def func(df: DaskLazyFrame) -> list[Any]:
            return [
                df._native_frame[col] for col in df.columns if df.schema[col] in dtypes
            ]

        return DaskSelector(
            func,
            depth=0,
            function_name="type_selector",
            root_names=None,
            output_names=None,
            backend_version=self._backend_version,
            returns_scalar=False,
            version=self._version,
            kwargs={},
        )

    def numeric(self: Self) -> DaskSelector:
        dtypes = import_dtypes_module(self._version)
        return self.by_dtype(
            [
                dtypes.Int64,
                dtypes.Int32,
                dtypes.Int16,
                dtypes.Int8,
                dtypes.UInt64,
                dtypes.UInt32,
                dtypes.UInt16,
                dtypes.UInt8,
                dtypes.Float64,
                dtypes.Float32,
            ],
        )

    def categorical(self: Self) -> DaskSelector:
        dtypes = import_dtypes_module(self._version)
        return self.by_dtype([dtypes.Categorical])

    def string(self: Self) -> DaskSelector:
        dtypes = import_dtypes_module(self._version)
        return self.by_dtype([dtypes.String])

    def boolean(self: Self) -> DaskSelector:
        dtypes = import_dtypes_module(self._version)
        return self.by_dtype([dtypes.Boolean])

    def all(self: Self) -> DaskSelector:
        def func(df: DaskLazyFrame) -> list[Any]:
            return [df._native_frame[col] for col in df.columns]

        return DaskSelector(
            func,
            depth=0,
            function_name="type_selector",
            root_names=None,
            output_names=None,
            backend_version=self._backend_version,
            returns_scalar=False,
            version=self._version,
            kwargs={},
        )

    def datetime(
        self: Self,
        time_unit: TimeUnit | Collection[TimeUnit] | None,
        time_zone: str | timezone | Collection[str | timezone | None] | None,
    ) -> DaskSelector:
        from narwhals.utils import _parse_datetime_selector_to_datetimes

        datetime_dtypes = _parse_datetime_selector_to_datetimes(
            time_unit=time_unit, time_zone=time_zone, version=self._version
        )
        return self.by_dtype(datetime_dtypes)


class DaskSelector(DaskExpr):
    def __repr__(self: Self) -> str:  # pragma: no cover
        return (
            f"DaskSelector("
            f"depth={self._depth}, "
            f"function_name={self._function_name}, "
            f"root_names={self._root_names}, "
            f"output_names={self._output_names}"
        )

    def _to_expr(self: Self) -> DaskExpr:
        return DaskExpr(
            self._call,
            depth=self._depth,
            function_name=self._function_name,
            root_names=self._root_names,
            output_names=self._output_names,
            backend_version=self._backend_version,
            returns_scalar=self._returns_scalar,
            version=self._version,
            kwargs={},
        )

    def __sub__(self: Self, other: DaskSelector | Any) -> DaskSelector | Any:
        if isinstance(other, DaskSelector):

            def call(df: DaskLazyFrame) -> list[Any]:
                lhs = self._call(df)
                rhs = other._call(df)
                return [x for x in lhs if x.name not in {x.name for x in rhs}]

            return DaskSelector(
                call,
                depth=0,
                function_name="type_selector",
                root_names=None,
                output_names=None,
                backend_version=self._backend_version,
                returns_scalar=self._returns_scalar,
                version=self._version,
                kwargs={},
            )
        else:
            return self._to_expr() - other

    def __or__(self: Self, other: DaskSelector | Any) -> DaskSelector | Any:
        if isinstance(other, DaskSelector):

            def call(df: DaskLazyFrame) -> list[dx.Series]:
                lhs = self._call(df)
                rhs = other._call(df)
                return [*(x for x in lhs if x.name not in {x.name for x in rhs}), *rhs]

            return DaskSelector(
                call,
                depth=0,
                function_name="type_selector",
                root_names=None,
                output_names=None,
                backend_version=self._backend_version,
                returns_scalar=self._returns_scalar,
                version=self._version,
                kwargs={},
            )
        else:
            return self._to_expr() | other

    def __and__(self: Self, other: DaskSelector | Any) -> DaskSelector | Any:
        if isinstance(other, DaskSelector):

            def call(df: DaskLazyFrame) -> list[Any]:
                lhs = self._call(df)
                rhs = other._call(df)
                return [x for x in lhs if x.name in {x.name for x in rhs}]

            return DaskSelector(
                call,
                depth=0,
                function_name="type_selector",
                root_names=None,
                output_names=None,
                backend_version=self._backend_version,
                returns_scalar=self._returns_scalar,
                version=self._version,
                kwargs={},
            )
        else:
            return self._to_expr() & other

    def __invert__(self: Self) -> DaskSelector:
        return (
            DaskSelectorNamespace(
                backend_version=self._backend_version, version=self._version
            ).all()
            - self
        )

    def __rsub__(self: Self, other: Any) -> NoReturn:
        raise NotImplementedError

    def __rand__(self: Self, other: Any) -> NoReturn:
        raise NotImplementedError

    def __ror__(self: Self, other: Any) -> NoReturn:
        raise NotImplementedError
