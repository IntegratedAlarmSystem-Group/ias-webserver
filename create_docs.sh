#!/bin/bash

rm sphinx/source/modules/*
sphinx-apidoc -o sphinx/source/modules/ .
cd sphinx
make html
cp -r build/html/* ../docs/
