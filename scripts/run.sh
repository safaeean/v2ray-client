#!/bin/bash

ROOT_PASSWORD=$(zenity --password --title="Request root password" --text="Please enter root password:")

if [ $? -ne 0 ]; then
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "$ROOT_PASSWORD" | sudo -S "$SCRIPT_DIR/$1" $2