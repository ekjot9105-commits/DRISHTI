"""Offline evaluation harness for the DRISHTI detector registry.

Self-contained: this package reads the detectors, the settings and the clips,
and writes only into backend/eval/ output files. It never mutates a detector,
a service, an API or data/settings.json.
"""
