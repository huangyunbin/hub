#!/bin/bash
# 一键同步：金山文档 → HTML → GitHub Pages
# 用法: bash sync.sh

cd "$(dirname "$0")"
python3 sync.py
