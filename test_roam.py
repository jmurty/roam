from roam import r, MISSING, Roamer

data = {
    'a': {
        'b': [
            {
                'c': lambda: 123,
                'd': lambda x: x,
            },
            'e',
            'This is / a test / string',
        ]
    }
}


class TestRoam:

    def test_missing_singleton(self):
        # `MISSING` is falsey
        assert not MISSING

    def test_getattr_traversal(self):
        assert r(data).a == data['a']

        assert r(data).a.b == data['a']['b']

        assert r(data).a.b  # Truthy

    def test_attr_traversal_missing(self):
        assert r(data).x == MISSING

        assert r(data).a.x == MISSING

        assert not r(data).a.x  # Falsey

    def test_getitem_traversal(self):
        assert r(data)['a'] == data['a']

        assert r(data)['a']['b'] == data['a']['b']

        assert r(data).a.b[0] == data['a']['b'][0]

        assert r(data).a.b[-1] == data['a']['b'][-1]

        assert r(data).a.b[-1]  # Truthy

    def test_getitem_traversal_missing(self):
        assert r(data)['x'] == MISSING

        assert r(data)['a']['x'] == MISSING

        assert r(data).a.b[9] == MISSING

        assert not r(data).a.b[9]  # Falsey

    def test_getattr_and_getitem_traversal(self):
        assert r(data).a['b'] == data['a']['b']

        assert r(data)['a'].b == data['a']['b']

        assert r(data)['a'].b[1] == data['a']['b'][1]

    def test_getattr_and_getitem_traversal_missing(self):
        assert r(data).a['x'] == MISSING

        assert r(data)['a'].x == MISSING

    def test_pseudo_index_getitem_traversal(self):
        assert r(data).a.b._0 == data['a']['b'][0]

        assert r(data).a.b._1 == data['a']['b'][1]

    def test_pseudo_index_getitem_traversal_missing(self):
        assert r(data).a.b._9 == MISSING

    def test_call_returns_item(self):
        assert r(data).a.b() is data['a']['b']

        assert r(data)['a']['b']() is data['a']['b']

    def test_call_returns_item_missing(self):
        assert r(data).x() == MISSING
        assert r(data)['x']() is MISSING

        assert r(data).a.x() == MISSING
        assert r(data)['b'].x() is MISSING

    def test_call_delegates_to_and_returns_item(self):
        # Delegate to methods on `dict` item
        assert r(data)['a'].items() == data['a'].items()
        assert r(data).a['b'][0].keys() == data['a']['b'][0].keys()
        assert list(r(data).a.b._0.values()) == list(data['a']['b'][0].values())

        # Delegate to methods on `str` item
        assert r(data).a.b[2].split('/') == ['This is ', ' a test ', ' string']
        assert type(r(data).a.b[2].split('/')) is list

        # Delegate to callable item within traversal
        assert r(data).a.b._0.c() == data['a']['b'][0]['c']()
        assert r(data).a.b._0.d(999) == data['a']['b'][0]['d'](999)

    def test_call_with_roam_option(self):
        assert isinstance(r(data).a.items(_roam=True), Roamer)
        assert r(data).a.items(_roam=True) == data['a'].items()

    def test_call_on_missing_with_roam_option(self):
        assert isinstance(r(data).x.items(_roam=True), Roamer)
        assert r(data).x.items(_roam=True) == MISSING

    def test_call_with_invoke_option(self):
        assert r(data).a.b(_invoke=len) == 3

    def test_call_with_invoke_and_roam_options(self):
        assert isinstance(r(data).a.b(_invoke=len, _roam=True), Roamer)
        assert r(data).a.b(_invoke=len, _roam=True) == 3
