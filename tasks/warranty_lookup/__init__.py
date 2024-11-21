from manufacturers import manufacturers

from tasks.warranty_lookup.carrier import get_carrier_warranty
from tasks.warranty_lookup.trane import get_trane_warranty
from tasks.warranty_lookup.york import get_york_warranty
# from tasks.warranty_lookup.lennox import get_lennox_warranty
from tasks.warranty_lookup.rheem import get_rheem_warranty
from tasks.warranty_lookup.bradford_white import get_bradford_white_warranty

warranty_lookups_by_manufacturer_id = {
    manufacturers['Carrier']: get_carrier_warranty,
    manufacturers['Trane']: get_trane_warranty,
    manufacturers['York']: get_york_warranty,
    # manufacturers['Lennox']: get_lennox_warranty,
    manufacturers['Rheem']: get_rheem_warranty,
    manufacturers['Bradford White']: get_bradford_white_warranty
}
