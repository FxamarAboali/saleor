from typing import Optional

from django_countries import countries

from ...shipping.models import ShippingZone


def get_countries_list(in_shipping_zones: Optional[bool] = None):
    """Return list of countries."""
    countries_list = [country for country in countries]
    if in_shipping_zones is not None:

        covered_countries = set()
        for zone in ShippingZone.objects.all():
            covered_countries.update({country.code for country in zone.countries})

        if in_shipping_zones:
            countries_list = [
                country for country in countries_list if country[0] in covered_countries
            ]

        if not in_shipping_zones:
            countries_list = [
                country
                for country in countries_list
                if country[0] not in covered_countries
            ]

    return countries_list
