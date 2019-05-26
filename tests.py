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

from roam import r, MISSING, Roamer

assert not MISSING

assert r(data).a() == data['a']

assert r(data).x() is MISSING

assert r(data).x == MISSING

assert r(data).x() == MISSING

assert r(data)['a']() == data['a']

assert r(data)['x']() is MISSING

assert r(data).a.b() == data['a']['b']

assert r(data).a.x() is MISSING

assert r(data)['a'].b() == data['a']['b']

assert r(data)['a'].x() is MISSING

assert r(data).a.b[0]() == data['a']['b'][0]

assert r(data).a.b[-1]() == data['a']['b'][-1]

assert r(data).a.b[9]() is MISSING

assert r(data).a.b._0() == data['a']['b'][0]

assert r(data).a.b._1() == data['a']['b'][1]

assert r(data).a.b._9() is MISSING

assert r(data)['a'].b._0.items() == data['a']['b'][0].items()

assert r(data)['a'].b._0.keys() == data['a']['b'][0].keys()

assert list(r(data)['a'].b._0.values()) == list(data['a']['b'][0].values())

assert r(data).a.b._0.c() == data['a']['b'][0]['c']()

assert r(data).a.b._0.d(999) == data['a']['b'][0]['d'](999)

assert r(data).a != MISSING

assert r(data).x == MISSING

assert r(data).x() is MISSING

assert r(data).x() == MISSING

assert r(data).a

assert not r(data).x

assert r(data).a()

assert not r(data).x()

assert r(data).a.b._0.d(999)

assert not r(data).a.b._0.d(0)

assert type(r(data).a.b[2].split('/')) is list

assert type(r(data).a.b[2].split('/', _roam=True)) is Roamer

assert type(r(data).a.b[2].split('/', _roam=True)()) is list

assert r(data).x.y[999].bloogle('/', _roam=True)[-999].blarg() is MISSING

assert r(data).a.b(_invoke=len) == 3

assert type(r(data).a.b(_invoke=len, _roam=True)) is Roamer

assert r(data).a.b(_invoke=len, _roam=True) == 3
