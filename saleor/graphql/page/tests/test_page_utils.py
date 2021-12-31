from ...page.utils import get_countries_list

TEST_COUNTRIES_WITH_SHIPPING_ZONE = [
    ("PL", "Poland"),
    ("US", "United States of America"),
]


def test_get_countries_list(shipping_zones):
    countries_list_all = get_countries_list()
    countries_list_false = get_countries_list(False)
    countries_list_true = get_countries_list(in_shipping_zones=True)
    assert set(countries_list_true + countries_list_false) == {
        country for country in countries_list_all
    }
    assert countries_list_true == TEST_COUNTRIES_WITH_SHIPPING_ZONE
    assert not any(country in countries_list_true for country in countries_list_false)
