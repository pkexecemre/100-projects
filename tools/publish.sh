#!/bin/sh
# Final gate + publish to GitHub. Run only when all 100 projects are present.
set -eu
cd "$(dirname -- "$0")/.."

python3 tools/check.py
python3 tools/run_tests.py --timeout 30
python3 tools/build_index.py

git add -A
git commit -m "100 projects: CLI tools, web toys, terminal games and utilities"

if git remote get-url origin >/dev/null 2>&1; then
    git push -u origin main
else
    gh repo create pkexecemre/100-projects --public --source=. --remote=origin --push \
        --description "100 small, self-contained Linux/CLI/web projects with smoke tests"
fi

gh repo edit pkexecemre/100-projects \
    --add-topic linux,cli,python,javascript,web,games,utilities,automation,monorepo \
    2>/dev/null || true
echo "published: https://github.com/pkexecemre/100-projects"
