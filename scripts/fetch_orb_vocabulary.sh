#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root even if script is called via symlink
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VOC_URL="${1:-https://raw.githubusercontent.com/UZ-SLAMLab/ORB_SLAM3/master/Vocabulary/ORBvoc.txt.tar.gz}"
TMP_DIR="$(mktemp -d)"
SRC_VOC_PATH="${REPO_ROOT}/perception_ws/src/slam_example/config/ORBvoc.txt"
ORB_DIR="${REPO_ROOT}/perception_ws/ORB_SLAM3/Vocabulary"

cleanup() {
    rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

mkdir -p "${REPO_ROOT}/perception_ws/src/slam_example/config"
mkdir -p "${ORB_DIR}"

already_valid=0
if [[ -s "${SRC_VOC_PATH}" ]]; then
    if head -n1 "${SRC_VOC_PATH}" | grep -q "git-lfs"; then
        echo "Existing ORBvoc.txt is a Git LFS pointer. Downloading full vocabulary..."
    else
        echo "Existing ORBvoc.txt looks valid. Reusing it (pass FORCE=1 to redownload)."
        already_valid=1
    fi
fi

if [[ "${FORCE:-0}" == "1" ]]; then
    echo "FORCE=1 detected. Redownloading vocabulary."
    already_valid=0
fi

if [[ "$already_valid" -eq 0 ]]; then
    ARCHIVE="${TMP_DIR}/ORBvoc.txt.tar.gz"
    echo "Downloading ORB vocabulary from ${VOC_URL}..."
    curl -L "${VOC_URL}" -o "${ARCHIVE}"
    echo "Extracting vocabulary..."
    tar -xzf "${ARCHIVE}" -C "${TMP_DIR}"
    mv "${TMP_DIR}/ORBvoc.txt" "${SRC_VOC_PATH}"
fi

cp "${SRC_VOC_PATH}" "${ORB_DIR}/ORBvoc.txt"

cat <<EOF
✅ ORB vocabulary ready.
 - Source config: ${SRC_VOC_PATH}
 - ORB_SLAM3 dir: ${ORB_DIR}/ORBvoc.txt
If you already built Docker images before running this script, rebuild them or
copy the file into running containers to pick up the vocabulary.
EOF
