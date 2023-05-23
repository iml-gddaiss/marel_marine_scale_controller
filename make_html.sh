#!/bin/bash

#if [ "$1" = "fr" ]
#then
#  README_FILE="README.fr.md"
#  USER_GUIDE_FILE="user_guide_fr.html"
#  echo "Processing French files"
#else
#  README_FILE="README.md"
#  USER_GUIDE_FILE="user_guide_en.html"
#  echo "Processing English files"
#fi

README_FILE="README.md"
USER_GUIDE_FILE="user_guide_en.html"

pandoc --standalone \
  --from markdown+implicit_figures \
  --to html5 \
  --metadata title="Marel Scale Controller" \
  --metadata author="jerome.guay@dfo.mpo.gc.ca" \
  --metadata date="May 2023" \
  --highlight-style=tango \
  -V colorlinks=True \
  -V linkcolor=red \
  -V urlcolor=blue \
  --output="$USER_GUIDE_FILE" \
  "$README_FILE"

# pandoc --standalone --from markdown+implicit_figures --to html5 --metadata title="Dcs5 Controller" --metadata author="jerome.guay@dfo.mpo.gc.ca" --metadata date="May 2023" --highlight-style=tango -V colorlinks=True -V linkcolor=red -V urlcolor=blue --toc --output=user_guide_fr.html README.fr.md
