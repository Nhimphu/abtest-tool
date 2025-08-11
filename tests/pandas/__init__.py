"""Minimal pandas stub for testing."""
from __future__ import annotations

from typing import Any, Iterable, Iterator, Tuple


def unique(seq: Iterable[Any]) -> list[Any]:
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


class Series(list):
    def __eq__(self, other):
        return [x == other for x in self]
    def sum(self) -> float:
        return float(__builtins__["sum"](self))

    def count(self) -> int:
        return len([x for x in self if x is not None])

    def mean(self) -> float:
        return __builtins__["sum"](self) / self.count() if self.count() else 0.0

    def var(self, ddof: int = 1) -> float:
        n = self.count()
        if n - ddof <= 0:
            return 0.0
        mean = self.mean()
        return __builtins__["sum"]((x - mean) ** 2 for x in self) / (n - ddof)

    def to_numpy(self):
        return list(self)

    def notna(self) -> list[bool]:
        return Series([x is not None for x in self])

    def isna(self) -> "Series":
        return Series([x is None for x in self])

    def dropna(self) -> "Series":
        return Series([x for x in self if x is not None])

    def unique(self) -> list[Any]:
        return unique(self)

    def fillna(self, value: Any) -> "Series":
        return Series([value if x is None else x for x in self])

    def all(self) -> bool:
        return all(self)

    def __and__(self, other: Iterable[Any]):
        return Series([bool(a) and bool(b) for a, b in zip(self, other)])

    def any(self) -> bool:
        return any(self)


class _Loc:
    def __init__(self, df: "DataFrame"):
        self._df = df

    def __getitem__(self, key: Tuple[list[bool], str]) -> Series:
        mask, col = key
        data = self._df._data[col]
        return Series([v for v, m in zip(data, mask) if m])


class DataFrame:
    def __init__(self, data: dict[str, Iterable[Any]] | "DataFrame"):
        if isinstance(data, DataFrame):
            self._data = {k: list(v) for k, v in data._data.items()}
        else:
            self._data = {k: list(v) for k, v in data.items()}
        self.loc = _Loc(self)

    @property
    def columns(self):
        return list(self._data.keys())

    def __getitem__(self, key: str) -> Series:
        return Series(self._data[key])

    def __len__(self) -> int:
        if not self._data:
            return 0
        return len(next(iter(self._data.values())))

    def copy(self) -> "DataFrame":
        return DataFrame(self._data)

    def drop(self, columns: Iterable[str]) -> "DataFrame":
        return DataFrame({k: v for k, v in self._data.items() if k not in set(columns)})

    def dropna(self, subset: Iterable[str]) -> "DataFrame":
        cols = list(subset)
        mask = [all(self._data[c][i] is not None for c in cols) for i in range(len(self))]
        return DataFrame({k: [v for v, m in zip(col, mask) if m] for k, col in self._data.items()})

    def sort_values(self, col: str) -> "DataFrame":
        order = sorted(range(len(self._data[col])), key=lambda i: self._data[col][i])
        return DataFrame({k: [col[i] for i in order] for k, col in self._data.items()})

    def groupby(self, col: str) -> Iterator[Tuple[Any, "DataFrame"]]:
        groups: dict[Any, list[int]] = {}
        values = self._data[col]
        for idx, val in enumerate(values):
            groups.setdefault(val, []).append(idx)
        for val, idxs in groups.items():
            subset = {k: [self._data[k][i] for i in idxs] for k in self._data}
            yield val, DataFrame(subset)


class _Types:
    @staticmethod
    def is_datetime64_any_dtype(_):
        return True


class _API:
    types = _Types()


api = _API()
