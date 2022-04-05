#!/bin/sh
python setup.py sdist bdist_wheel
twine upload dist/*
rm -rf build dist bib_lookup.egg-info
