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

from roam import r, MISSING

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

assert r(data).a.b[2].split('/')[-1].strip() == 'string'

assert r(data).a.b[2].split('/')[-1].strip() == 'string'

assert r(data).x.y[999].bloogle('/')[-999].blarg() is MISSING

assert r(data).x.y[999].bloogle('/')[-999].blarg() == MISSING
