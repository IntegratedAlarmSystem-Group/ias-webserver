#!/bin/bash

rm sphinx/source/modules/*
sphinx-apidoc -o sphinx/source/modules/ . ./*migrations*  # skip migrations
cd sphinx/source/modules

AUTO_MODULES_FILE="modules.rst"
TEMP_FILE="modules.tmp"
c=1
while read line; do
  if [[ $c -gt 2 ]]; then  # keep first lines
    if [[ $line = ".. toctree::" ]]; then
      echo "$line" >> $TEMP_FILE
      echo -e "\t:glob:" >> $TEMP_FILE  # add option after the toc tree line
    else
      # identify non empty lines and lines without options
      if [[ ! -z "${line// }" ]] && [[ ! $line =~ .*:.* ]]; then
          echo -e "\t$line*" >> $TEMP_FILE
      else
        echo -e "\t$line" >> $TEMP_FILE
      fi
    fi
  else
    echo "$line" >> $TEMP_FILE
  fi
  c=$[$c+1]
done < $AUTO_MODULES_FILE
cat $TEMP_FILE > $AUTO_MODULES_FILE
rm $TEMP_FILE

cd ../../
cd sphinx
make html
cp -r build/html/* ../docs/
