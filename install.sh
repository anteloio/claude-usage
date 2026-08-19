#!/usr/bin/env bash
# Symlink the command onto the PATH and, optionally, print it on every new shell.
#
# Works two ways:
#   ./install.sh                                          from a checkout
#   curl -fsSL .../install.sh | bash                      clones first, then installs
set -euo pipefail

repo_url="https://github.com/anteloio/claude-usage.git"
clone_dir="${CLAUDE_USAGE_DIR:-${HOME}/.local/share/claude-usage}"
bin_dir="${HOME}/.local/bin"
target="${bin_dir}/claude-usage"
marker="# claude-usage"

# Piped from curl there is no script on disk, so fetch the repo ourselves.
src=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ -z "$src" ] || [ ! -f "${src}/claude-usage" ]; then
  command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
  if [ -d "${clone_dir}/.git" ]; then
    git -C "$clone_dir" pull --ff-only --quiet
    echo "updated ${clone_dir}"
  else
    mkdir -p "$(dirname "$clone_dir")"
    git clone --quiet --depth 1 "$repo_url" "$clone_dir"
    echo "cloned into ${clone_dir}"
  fi
  src="$clone_dir"
fi

mkdir -p "$bin_dir"
ln -sfn "${src}/claude-usage" "$target"
chmod +x "${src}/claude-usage"
echo "linked ${target} -> ${src}/claude-usage"

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
