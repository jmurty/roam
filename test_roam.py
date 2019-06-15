import pytest

from roam import r, r_strict, MISSING, Roamer, RoamPathException


class DataTester:
    """ Class to convert dict data to object with attributes """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for n, v in kwargs.items():
            if n.startswith("_"):
                n = n[1:]
            setattr(self, n, v)

    def __dir__(self):
        return self.kwargs.keys()

    @property
    def as_dict(self):
        return self.kwargs


# Amended subset of GitHub user data for 'jmurty' from
# https://api.github.com/users/jmurty/repos
github_data = [
    {
        "name": "java-xmlbuilder",
        "full_name": "jmurty/java-xmlbuilder",
        "private": False,
        "owner": {
            "login": "jmurty",
            "url": "https://api.github.com/users/jmurty",
            "type": "User",
            "fn": lambda message: message,  # Added to test in-data callable
        },
        "description": "XML Builder is a utility that allows simple XML documents to be constructed using relatively sparse Java code",
        "fork": False,
        "url": "https://api.github.com/repos/jmurty/java-xmlbuilder",
        "created_at": "2014-03-05T22:48:04Z",
        "updated_at": "2019-04-29T14:03:24Z",
        "pushed_at": "2017-09-01T13:08:26Z",
        "homepage": None,
        "size": 164,
        "language": "Java",
        "archived": False,
        "disabled": False,
        "open_issues_count": 0,
        "license": {
            "key": "apache-2.0",
            "name": "Apache License 2.0",
            "spdx_id": "Apache-2.0",
            "url": "https://api.github.com/licenses/apache-2.0",
        },
        "forks": 15,
        "open_issues": 0,
        "watchers": 85,
        "default_branch": "master",
    },
    {
        "name": "xml4h",
        "full_name": "jmurty/xml4h",
        "private": False,
        "owner": {
            "login": "jmurty",
            "url": "https://api.github.com/users/jmurty",
            "type": "User",
        },
        "description": "XML for Humans in Python",
        "fork": False,
        "url": "https://api.github.com/repos/jmurty/xml4h",
        "created_at": "2012-08-14T13:49:43Z",
        "updated_at": "2018-09-21T16:15:44Z",
        "pushed_at": "2015-07-13T15:07:28Z",
        "homepage": "xml4h.readthedocs.org",
        "size": 663,
        "language": "Python",
        "archived": False,
        "disabled": False,
        "open_issues_count": 6,
        "license": {
            "key": "mit",
            "name": "MIT License",
            "spdx_id": "MIT",
            "url": "https://api.github.com/licenses/mit",
        },
        "forks": 2,
        "open_issues": 6,
        "watchers": 37,
        "default_branch": "master",
    },
]

github_data0 = github_data[0]


# Select data from https://en.wikipedia.org/wiki/Monty_Python_filmography
python_filmography = [
    DataTester(
        title="Monty Python's Flying Circus",
        type="tv",
        years=DataTester(_from=1975, to=1975),
        writers=[
            DataTester(name="Monty Python", group=True),
            DataTester(name="Neil Innes"),
            DataTester(name="Douglas Adams"),
        ],
    ),
    DataTester(
        title="Monty Python and the Holy Grail",
        type="movie",
        years=DataTester(_from=1969, to=1974),
        writers=[DataTester(name="Monty Python", group=True)],
    ),
]


class TestRoamer:
    def test_missing_has_rich_falsey_behaviour(self):
        assert not MISSING

        assert not MISSING

        assert len(MISSING) == 0

        for _ in MISSING:
            pytest.fail("Shouldn't be able to iterate over MISSING")

    def test_getattr_traversal(self):
        assert r(github_data0).license == github_data0["license"]

        assert r(github_data0).license.name == github_data0["license"]["name"]

        assert r(github_data0).license.name  # Truthy

    def test_attr_traversal_missing(self):
        assert r(github_data0).x == MISSING

        assert r(github_data0).license.x == MISSING

        assert not r(github_data0).license.x  # Falsey

        assert not r(github_data0).license.x.y  # Falsey

        # Confirm the underlying item is the MISSING singleton
        assert r(github_data0).license.x() is MISSING
        assert r(github_data0).license.x() == MISSING
        assert not r(github_data0).license.x()  # Falsey

    def test_getitem_traversal(self):
        assert r(github_data0)["license"] == github_data0["license"]

        assert r(github_data0)["license"]["name"] == github_data0["license"]["name"]

        assert r(github_data0).license.name[0] == github_data0["license"]["name"][0]

        assert r(github_data0).license.name[-1] == github_data0["license"]["name"][-1]

        assert r(github_data0).license.name[-1]  # Truthy

    def test_getitem_traversal_missing(self):
        assert r(github_data0)["x"] == MISSING

        assert r(github_data0)["license"]["x"] == MISSING

        assert r(github_data0)["license"]["name"]["x"] == MISSING

        assert not r(github_data0)["license"]["name"]["x"]  # Falsey

        assert not r(github_data0)["license"]["name"]["x"]["y"]  # Falsey

        # Confirm the underlying item is the MISSING singleton
        assert r(github_data0)["license"]["name"]["x"]() is MISSING
        assert r(github_data0)["license"]["name"]["x"]() == MISSING
        assert not r(github_data0)["license"]["name"]["x"]()  # Falsey

    def test_getattr_and_getitem_traversal(self):
        assert r(github_data0).license["name"] == github_data0["license"]["name"]

        assert r(github_data0)["license"].name == github_data0["license"]["name"]

        assert r(github_data0)["license"].name[1] == github_data0["license"]["name"][1]

    def test_getattr_and_getitem_traversal_missing(self):
        assert r(github_data0).license["x"] == MISSING

        assert r(github_data0)["license"].x == MISSING

        # Confirm the underlying item is the MISSING singleton
        assert r(github_data0).license["x"]() is MISSING
        assert r(github_data0)["license"].x() is MISSING

    def test_fail_fast(self):
        with pytest.raises(RoamPathException) as ex:
            r(github_data0, _raise=True).x
        assert (
            str(ex.value) == "<RoamPathException: missing step 1 .x for path <dict>.x>"
        )

        with pytest.raises(RoamPathException) as ex:
            r(github_data0, _raise=True).license["x"]
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 2 ['x'] for path <dict>.license['x'] at <dict>"
            " with keys ['key', 'name', 'spdx_id', 'url']>"
        )

        with pytest.raises(RoamPathException) as ex:
            r(github_data0, _raise=True)["license"].name.x
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .x for path <dict>['license'].name.x at <str>>"
        )

    def test_slice_traversal(self):
        assert r(github_data)[:] == github_data[:]

        assert r(github_data)[1:] == github_data[1:]

    def test_slice_traversal_missing(self):
        assert len(github_data) == 2

        assert r(github_data)[3] == MISSING
        assert r(github_data)[3]() is MISSING

        assert r(github_data)[3:] == []

        assert r(github_data)[2:4] == github_data[2:4]

    def test_call_returns_item(self):
        assert r(github_data0).license.name() is github_data0["license"]["name"]

        assert r(github_data0)["license"]["name"]() is github_data0["license"]["name"]

    def test_call_returns_item_missing(self):
        assert r(github_data0).x() == MISSING
        assert r(github_data0)["x"]() is MISSING

        assert r(github_data0).license.x() == MISSING
        assert r(github_data0)["name"].x() is MISSING

    def test_call_raise_on_item_missing(self):
        with pytest.raises(RoamPathException) as ex:
            r(github_data0).x(_raise=True)
        assert (
            str(ex.value) == "<RoamPathException: missing step 1 .x for path <dict>.x>"
        )

        with pytest.raises(RoamPathException) as ex:
            r(github_data0).license["name"].x(_raise=True)
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .x for path <dict>.license['name'].x at <str>>"
        )

        with pytest.raises(RoamPathException) as ex:
            r(github_data0, _raise=True).license["name"].x()
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .x for path <dict>.license['name'].x at <str>>"
        )

    def test_call_delegates_to_and_returns_item(self):
        # Delegate to methods on `dict` item
        assert r(github_data0)["license"]["items"]() == github_data0["license"].items()
        assert r(github_data0).license.keys() == github_data0["license"].keys()
        assert list(r(github_data0).license.values()) == list(
            github_data0["license"].values()
        )

        # Delegate to methods on `str` item
        assert r(github_data0).license.url.split("/") == [
            "https:",
            "",
            "api.github.com",
            "licenses",
            "apache-2.0",
        ]
        assert type(r(github_data0).license.url.split("/")) is list

        # Delegate to callable item within traversal
        assert r(github_data0).owner.fn("Hi") == "Hi"
        assert r(github_data0).owner.fn(999) == 999

    def test_call_with_roam_option(self):
        assert isinstance(r(github_data0).license.items(_roam=True), Roamer)
        assert (
            r(github_data0).license.items(_roam=True) == github_data0["license"].items()
        )

    def test_call_on_missing_with_roam_option(self):
        assert isinstance(r(github_data0).x.items(_roam=True), Roamer)
        assert r(github_data0).x.items(_roam=True) == MISSING

    def test_call_with_invoke_option(self):
        assert r(github_data0).owner.login(_invoke=len) == 6

    def test_call_with_invoke_and_roam_options(self):
        assert isinstance(r(github_data0).owner(_invoke=len, _roam=True), Roamer)
        assert r(github_data0).owner(_invoke=len, _roam=True) == 4

    def test_iterator_traversal(self):
        for i, item_roamer in enumerate(r(github_data)):
            assert isinstance(item_roamer, Roamer)
            assert item_roamer.name == github_data[i]["name"]

        assert [
            owner_fn("Hello world!") for owner_fn in r(github_data)[:].owner.fn
        ] == ["Hello world!"]

        assert [
            owner.fn("Hello world!") for owner in r(github_data)[:].owner if owner.fn
        ] == ["Hello world!"]

        assert [
            writer.name()
            for writer in r(python_filmography)[:].writers
            if not writer.group
        ] == ["Neil Innes", "Douglas Adams"]

        # Trying to iterating over non-iterable
        for _ in r(github_data0).size:
            pytest.fail("Shouldn't be able to iterate over int")

        for _ in r(github_data0).fork:
            pytest.fail("Shouldn't be able to iterate over bool")

    def test_iterator_traversal_missing(self):
        for _ in r(github_data0).x:
            pytest.fail("Shouldn't be able to iterate over MISSING")

        for _ in r(github_data0).license.name.x:
            pytest.fail("Shouldn't be able to iterate over MISSING")

        with pytest.raises(RoamPathException) as ex:
            r_strict(github_data0).license.name.x
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .x for path <dict>.license.name.x at <str>>"
        )

    def test_nested_iterable_traversal(self):
        assert r(github_data)[:]["owner"]["login"] == ("jmurty", "jmurty")

        assert r(python_filmography)[:]["title"] == (
            "Monty Python's Flying Circus",
            "Monty Python and the Holy Grail",
        )
        assert r(python_filmography)[:]["writers"]["name"] == (
            "Monty Python",
            "Neil Innes",
            "Douglas Adams",
            "Monty Python",
        )
        assert r(python_filmography)[:].writers.name == (
            "Monty Python",
            "Neil Innes",
            "Douglas Adams",
            "Monty Python",
        )

        # Check slices work within multi-item processing
        assert (
            r(python_filmography)[:].writers.name[:]
            == r(python_filmography)[:].writers.name
        )
        assert (
            r(python_filmography)[:]["writers"]["name"][:]
            == r(python_filmography)[:]["writers"]["name"]
        )
        assert r(python_filmography)[:].writers.name[1:-1] == (
            "Neil Innes",
            "Douglas Adams",
        )

        # Check integer lookpus work within multi-item processing
        assert r(python_filmography)[:]["writers"][1]["name"] == "Neil Innes"

        assert r(python_filmography)[:].writers[1].name == "Neil Innes"

    def test_nested_iterable_traversal_missing(self):
        # Referencing missing attr/keys results in an empty list
        assert r(python_filmography)[:].x == tuple()
        assert r(python_filmography)[:]["x"] == tuple()

        assert r(python_filmography)[:].title.x == tuple()
        assert r(python_filmography)[:]["title"]["x"] == tuple()

        # Referencing *sometimes* missing attr/keys results in partial list
        assert len(r(python_filmography)[:].writers) == 4
        assert r(python_filmography)[:].writers.group == (True, True)
        assert r(python_filmography)[:]["writers"]["group"] == (True, True)

        # Lookup missing n-th item in a nested collection
        assert r(python_filmography)[:].writers.group[2] == MISSING
        with pytest.raises(RoamPathException) as ex:
            r(python_filmography)[:].writers.group[2](_raise=True)
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 4 [2] for path <list>[:].writers.group[2] at <tuple> with length 2>"
        )

    def test_roamer_equality(self):
        assert r(python_filmography)[:].writers == r(python_filmography)[:].writers

    def test_roamer_len(self):
        # Standard length lookup of list
        assert len(r(python_filmography)) == 2

        # Report 1 for current item that doesn't actually support `len()` instead of `TypeError`
        assert len(r(python_filmography)[0]) == 1
        with pytest.raises(TypeError):
            len(python_filmography[0])

        # Report zero from MISSING item
        x = r(python_filmography).x
        assert len(x) == 0
        assert x == MISSING

    def test_path_reporting(self):
        assert (
            str(r(github_data0).license.name)
            == "<Roamer: <dict>.license.name => 'Apache License 2.0'>"
        )

        assert (
            str(r(github_data0)["license"]["name"])
            == "<Roamer: <dict>['license']['name'] => 'Apache License 2.0'>"
        )

        assert (
            str(r(github_data0)["license"].name)
            == "<Roamer: <dict>['license'].name => 'Apache License 2.0'>"
        )

        assert (
            str(r(python_filmography)[:].writers[2]["as_dict"])
            == "<Roamer: <list>[:].writers[2]['as_dict'] => {'name': 'Douglas Adams'}>"
        )

        assert (
            str(r(python_filmography)[:].writers[2]["name"])
            == "<Roamer: <list>[:].writers[2]['name'] => 'Douglas Adams'>"
        )

        assert (
            str(r(python_filmography)[:].writers[3]["name"])
            == "<Roamer: <list>[:].writers[3]['name'] => 'Monty Python'>"
        )

        assert (
            str(r(python_filmography)[:].writers[2]["age"])
            == "<Roamer: missing step 4 ['age'] for path <list>[:].writers[2]['age'] at <DataTester> with attrs [name] => <Roam.MISSING>>"
        )

        assert (
            str(r(github_data0).license["x"])
            == "<Roamer: missing step 2 ['x'] for path <dict>.license['x'] at <dict>"
            " with keys ['key', 'name', 'spdx_id', 'url'] => <Roam.MISSING>>"
        )

        assert (
            str(r(python_filmography)[0].writers.name)
            == "<Roamer: missing step 3 .name for path <list>[0].writers.name at <list> => <Roam.MISSING>>"
        )

    def test_path_survives_roamer_reuse(self):
        roamer = r(github_data)

        assert (
            str(roamer[0].license.name)
            == "<Roamer: <list>[0].license.name => 'Apache License 2.0'>"
        )

        assert (
            str(roamer[1]["license"].name)
            == "<Roamer: <list>[1]['license'].name => 'MIT License'>"
        )

        with pytest.raises(RoamPathException) as ex:
            roamer[1].license.x(_raise=True)
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .x for path <list>[1].license.x at <dict> with keys ['key', 'name', 'spdx_id', 'url']>"
        )

        with pytest.raises(RoamPathException) as ex:
            roamer[1].license["name"].x(_raise=True)
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 4 .x for path <list>[1].license['name'].x at <str>>"
        )

    def test_roamer_clone_via_init(self):
        r_license = r(github_data)[0].license

        assert r_license == {
            "key": "apache-2.0",
            "name": "Apache License 2.0",
            "spdx_id": "Apache-2.0",
            "url": "https://api.github.com/licenses/apache-2.0",
        }

        # Ensure clone is identical in all ways that matter
        r_clone = r(r_license)
        assert r_clone == r_license
        assert r_clone._r_item_ == r_license._r_item_
        assert r_clone._r_is_multi_item_ == r_license._r_is_multi_item_
        assert r_clone._r_raise_ == r_license._r_raise_ is False

        # Can override raise status in clone
        r_clone = r(r_license, _raise=True)
        assert r_clone._r_raise_ is True
        with pytest.raises(RoamPathException) as ex:
            r_clone.wrong
        assert (
            str(ex.value)
            == "<RoamPathException: missing step 3 .wrong for path <list>[0].license.wrong"
            " at <dict> with keys ['key', 'name', 'spdx_id', 'url']>"
        )
