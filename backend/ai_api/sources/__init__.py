"""Source layer of the AI API: one HTTP client, one adapter contract.

`http.py` is the only place that talks to the network, `base.py` is what an
adapter implements and `registry.py` maps a source name to it.
"""
