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

assert r(data).a._ == data['a']

assert r(data).x._ is MISSING

assert r(data)['a']._ == data['a']

assert r(data)['x']._ is MISSING

assert r(data).a.b._ == data['a']['b']

assert r(data).a.x._ is MISSING

assert r(data)['a'].b._ == data['a']['b']

assert r(data)['a'].x._ is MISSING

assert r(data).a.b[0]._ == data['a']['b'][0]

assert r(data).a.b[-1]._ == data['a']['b'][-1]

assert r(data).a.b[9]._ is MISSING

assert r(data).a.b._0._ == data['a']['b'][0]

assert r(data).a.b._1._ == data['a']['b'][1]

assert r(data).a.b._9._ is MISSING

assert r(data).a.b._0()._ is MISSING

assert r(data).a.b._0.c()._ == data['a']['b'][0]['c']()

assert r(data).a.b._0.d(999)._ == data['a']['b'][0]['d'](999)

assert r(data).a.b._0.d(999).f._ is MISSING

assert r(data).x.y.z._1._2._3('this')('that')._ is MISSING

assert r(data).a != MISSING

assert r(data).x == MISSING

assert r(data).x._ is MISSING

assert r(data).x._ == MISSING

assert r(data).a

assert not r(data).x

assert r(data).a._

assert not r(data).x._

assert r(data).a.b._0.d(999)

assert not r(data).a.b._0.d(0)

assert r(data).a.b[2].split('/')[-1].strip() == 'string'

assert r(data).a.b[2].split('/')[-1].strip()._ == 'string'

assert r(data).x.y[999].bloogle('/')[-999].blarg() == MISSING

assert r(data).x.y[999].bloogle('/')[-999].blarg()._ is MISSING

assert r(data).x.y[999].bloogle('/')[-999].blarg()._ == MISSING
