rm docs/source/modules/* 
sphinx-apidoc -o docs/source/modules/ .
cd docs
make html
