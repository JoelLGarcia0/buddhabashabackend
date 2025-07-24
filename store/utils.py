# utils.py or wherever makes sense
from shippo import Shippo, components
from django.conf import settings

def fetch_rates_for_order(order, length, width, height, weight):
    shippo_sdk = Shippo(api_key_header=settings.SHIPPO_API_KEY)

    address = order.shipping_address or {}

    from_address = components.AddressCreateRequest(
        name="BuddhaBasha",
        street1="7917 sw 194th st F201",
        city="Miami",
        state="FL",
        zip="33196",
        country="US",
        email=settings.DEFAULT_FROM_EMAIL,
        phone="7865438351"
    )

    to_address = components.AddressCreateRequest(
        name=address.get("name", ""),
        street1=address.get("line1", ""),
        city=address.get("city", ""),
        state=address.get("state", ""),
        zip=address.get("postal_code", ""),
        country=address.get("country", "US"),
        email=order.email
    )

    parcel = components.ParcelCreateRequest(
        length=str(length),
        width=str(width),
        height=str(height),
        distance_unit=components.DistanceUnitEnum.IN,
        weight=str(weight),
        mass_unit=components.WeightUnitEnum.LB
    )

    shipment = shippo_sdk.shipments.create(
        components.ShipmentCreateRequest(
            address_from=from_address,
            address_to=to_address,
            parcels=[parcel],
            async_=False,
            carrier_accounts=["bad72a7e81a743afbf83c723ae1c0b88"]
        )
    )

    return shipment.rates, shipment.object_id
