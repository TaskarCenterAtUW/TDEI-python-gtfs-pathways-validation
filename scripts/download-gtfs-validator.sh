#!/bin/sh
# Downloads MobilityData's GTFS validator CLI (https://github.com/MobilityData/gtfs-validator)
# to <dir>/gtfs-validator-cli.jar, and checks it against the expected SHA-256.
# Used by the Dockerfile and CI; run it once for local development:
#   scripts/download-gtfs-validator.sh lib
set -eu

DIR="${1:-lib}"
VERSION="${GTFS_VALIDATOR_VERSION:-8.0.1}"

case "$VERSION" in
  8.0.1) SHA256=19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2 ;;
  *) echo "No checksum for gtfs-validator $VERSION; add one to $0" >&2; exit 1 ;;
esac

mkdir -p "$DIR"
JAR="$DIR/gtfs-validator-cli.jar"
URL="https://github.com/MobilityData/gtfs-validator/releases/download/v$VERSION/gtfs-validator-$VERSION-cli.jar"

if [ -f "$JAR" ] && echo "$SHA256  $JAR" | sha256sum -c - >/dev/null 2>&1; then
  echo "gtfs-validator $VERSION already in $JAR"
  exit 0
fi

curl -fsSL -o "$JAR" "$URL"
echo "$SHA256  $JAR" | sha256sum -c -
