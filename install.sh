#!/usr/bin/env bash
# Symlink the command onto the PATH and, optionally, print it on every new shell.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="${HOME}/.local/bin"
target="${bin_dir}/claude-usage"
marker="# claude-usage"

mkdir -p "$bin_dir"
ln -sfn "${repo}/claude-usage" "$target"
chmod +x "${repo}/claude-usage"
echo "linked ${target} -> ${repo}/claude-usage"

case ":${PATH}:" in
  *":${bin_dir}:"*) ;;
  *) echo "warning: ${bin_dir} is not on your PATH" ;;
esac

rc="${HOME}/.zshrc"
if [ -f "$rc" ] && grep -q "$marker" "$rc"; then
  echo "shell hook already present in ${rc}"
else
  cat >> "$rc" <<EOF

${marker}: plan usage on every new shell, served from cache
alias cu='claude-usage --fresh'
if [[ -o interactive ]] && command -v claude-usage >/dev/null; then
  claude-usage --cached
fi
EOF
  echo "added the shell hook to ${rc}"
fi

echo
"$target" --cached
