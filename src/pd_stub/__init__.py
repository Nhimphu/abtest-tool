class BoolSeries(list):
    def all(self):
        return all(self)
    def any(self):
        return any(self)
    def sum(self):
        return sum(self)


class Series(list):
    def isna(self):
        return BoolSeries([x is None for x in self])
    def fillna(self, value):
        return Series([value if x is None else x for x in self])
    def dropna(self):
        return Series([x for x in self if x is not None])
    def unique(self):
        seen = []
        for x in self:
            if x not in seen:
                seen.append(x)
        return seen


class DataFrame:
    def __init__(self, data):
        self._data = {k: list(v) for k, v in data.items()}
        self.columns = list(self._data.keys())

    def __len__(self):
        if not self.columns:
            return 0
        first_col = self.columns[0]
        return len(self._data[first_col])

    def __getitem__(self, key):
        return Series(self._data[key])

    def __setitem__(self, key, value):
        self._data[key] = list(value)
        if key not in self.columns:
            self.columns.append(key)

    def drop(self, columns=None):
        columns = columns or []
        new_data = {k: v for k, v in self._data.items() if k not in columns}
        return DataFrame(new_data)

    def dropna(self, subset):
        col = subset[0]
        mask = [val is None for val in self._data[col]]
        new_data = {
            k: [v for i, v in enumerate(vals) if not mask[i]]
            for k, vals in self._data.items()
        }
        return DataFrame(new_data)

    def isna(self):
        return {k: Series(v).isna() for k, v in self._data.items()}

