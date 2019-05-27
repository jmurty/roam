from roam import r, MISSING, Roamer


# Amended subset of GitHub user data for 'jmurty' from
# https://api.github.com/users/jmurty/repos
data = [
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

data0 = data[0]


class TestRoam:
    def test_missing_singleton(self):
        # `MISSING` is falsey
        assert not MISSING

    def test_getattr_traversal(self):
        assert r(data0).license == data0["license"]

        assert r(data0).license.name == data0["license"]["name"]

        assert r(data0).license.name  # Truthy

    def test_attr_traversal_missing(self):
        assert r(data0).x == MISSING

        assert r(data0).license.x == MISSING

        assert not r(data0).license.x  # Falsey

    def test_getitem_traversal(self):
        assert r(data0)["license"] == data0["license"]

        assert r(data0)["license"]["name"] == data0["license"]["name"]

        assert r(data0).license.name[0] == data0["license"]["name"][0]

        assert r(data0).license.name[-1] == data0["license"]["name"][-1]

        assert r(data0).license.name[-1]  # Truthy

    def test_getitem_traversal_missing(self):
        assert r(data0)["x"] == MISSING

        assert r(data0)["license"]["x"] == MISSING

        assert r(data0)["license"]["name"]["x"] == MISSING

        assert not r(data0)["license"]["name"]["x"]  # Falsey

    def test_getattr_and_getitem_traversal(self):
        assert r(data0).license["name"] == data0["license"]["name"]

        assert r(data0)["license"].name == data0["license"]["name"]

        assert r(data0)["license"].name[1] == data0["license"]["name"][1]

    def test_getattr_and_getitem_traversal_missing(self):
        assert r(data0).license["x"] == MISSING

        assert r(data0)["license"].x == MISSING

    def test_slice_traversal(self):
        assert r(data)[:] == data[:]

        assert r(data)[1:] == data[1:]

    def test_slice_traversal_missing(self):
        assert len(data) == 2

        assert r(data)[3] == MISSING

        assert r(data)[3:] == []

        assert r(data)[2:4] == data[2:4]

    def test_pseudo_index_getitem_traversal(self):
        assert r(data0).license.name._0 == data0["license"]["name"][0]

        assert r(data0).license.name._1 == data0["license"]["name"][1]

    def test_pseudo_index_getitem_traversal_missing(self):
        assert r(data0).license.name._99 == MISSING

    def test_call_returns_item(self):
        assert r(data0).license.name() is data0["license"]["name"]

        assert r(data0)["license"]["name"]() is data0["license"]["name"]

    def test_call_returns_item_missing(self):
        assert r(data0).x() == MISSING
        assert r(data0)["x"]() is MISSING

        assert r(data0).license.x() == MISSING
        assert r(data0)["name"].x() is MISSING

    def test_call_delegates_to_and_returns_item(self):
        # Delegate to methods on `dict` item
        assert r(data0)["license"].items() == data0["license"].items()
        assert r(data0).license.keys() == data0["license"].keys()
        assert list(r(data0).license.values()) == list(data0["license"].values())

        # Delegate to methods on `str` item
        assert r(data0).license.url.split("/") == [
            "https:",
            "",
            "api.github.com",
            "licenses",
            "apache-2.0",
        ]
        assert type(r(data0).license.url.split("/")) is list

        # Delegate to callable item within traversal
        assert r(data0).owner.fn("Hi") == "Hi"
        assert r(data0).owner.fn(999) == 999

    def test_call_with_roam_option(self):
        assert isinstance(r(data0).license.items(_roam=True), Roamer)
        assert r(data0).license.items(_roam=True) == data0["license"].items()

    def test_call_on_missing_with_roam_option(self):
        assert isinstance(r(data0).x.items(_roam=True), Roamer)
        assert r(data0).x.items(_roam=True) == MISSING

    def test_call_with_invoke_option(self):
        assert r(data0).owner.login(_invoke=len) == 6

    def test_call_with_invoke_and_roam_options(self):
        assert isinstance(r(data0).owner(_invoke=len, _roam=True), Roamer)
        assert r(data0).owner(_invoke=len, _roam=True) == 4
