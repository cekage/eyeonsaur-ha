#!/usr/bin/env bash

BRANDPATH="../custom_components/eyeonsaur/brands"

rm -rf -- "${BRANDPATH}"/*.png
convert -background none logo_saur.svg -resize 256x256 "${BRANDPATH}"/icon.png
convert -background none logo_saur.svg -resize 512x512 "${BRANDPATH}"/'icon@2x.png'
pngcrush -ow "${BRANDPATH}"/icon.png
pngcrush -ow "${BRANDPATH}"/'icon@2x.png'