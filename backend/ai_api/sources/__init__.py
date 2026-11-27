"""Source layer of the AI API: one HTTP client and the sources that use it.

`http.py` is the only place that talks to the network. `fesofi.py` identifies a
series and reads its catalogue facts, `filatelia.py` prices a code in the shop and
`search_prices.py` reads asking prices from the allowed-site search, opening the
listing when the snippet is not enough. `base.py` is the `Observation` they speak.
"""
