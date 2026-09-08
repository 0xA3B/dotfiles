#!/usr/bin/env bash
# Claude Code status line script (Starship-inspired)
# Reads JSON from stdin and formats a custom status line

# ANSI colors
RESET=$'\033[0m'
BOLD=$'\033[1m'
DIM=$'\033[2m'
CYAN=$'\033[36m'
MAGENTA=$'\033[35m'
BLUE=$'\033[34m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
ORANGE=$'\033[38;5;208m'

# Read stdin once and extract everything in a single jq call.
# Emit one field per line and preserve empty fields without requiring Bash 4's mapfile.
input=$(cat)
fields=()
while IFS= read -r field; do
  fields+=("$field")
done < <(printf '%s' "$input" | jq -r '
  .workspace.project_dir // "",
  .model.id // "",
  .model.display_name // "",
  .effort.level // "",
  .context_window.current_usage.input_tokens // 0,
  .context_window.current_usage.cache_creation_input_tokens // 0,
  .context_window.current_usage.cache_read_input_tokens // 0,
  .context_window.context_window_size // 0,
  .context_window.summarized_conversation_turns // 0,
  .cost.total_duration_ms // 0,
  .cost.total_cost_usd // 0,
  .cost.total_lines_added // 0,
  .cost.total_lines_removed // 0,
  .vim.mode // ""
')
project_dir=${fields[0]}
model_id=${fields[1]}
model_display=${fields[2]}
effort_level=${fields[3]}
current_input=${fields[4]}
cache_creation=${fields[5]}
cache_read=${fields[6]}
ctx_size=${fields[7]}
summarized_turns=${fields[8]}
duration_ms=${fields[9]}
cost_usd=${fields[10]}
lines_added=${fields[11]}
lines_removed=${fields[12]}
vim_mode=${fields[13]}

project_name=$(basename "$project_dir")

# Git info (branch + dirty status)
git_display=""
if [ -d "$project_dir/.git" ] || git -C "$project_dir" rev-parse --git-dir >/dev/null 2>&1; then
  git_branch=$(git -C "$project_dir" symbolic-ref --short HEAD 2>/dev/null || git -C "$project_dir" rev-parse --short HEAD 2>/dev/null)
  if [ -n "$git_branch" ]; then
    git_dirty=""
    dirty_color=""
    if ! git -C "$project_dir" diff --quiet 2>/dev/null || ! git -C "$project_dir" diff --cached --quiet 2>/dev/null; then
      git_dirty="*"
      dirty_color="$YELLOW"
    fi
    if [ -n "$(git -C "$project_dir" ls-files --others --exclude-standard 2>/dev/null)" ]; then
      git_dirty="${git_dirty}+"
      dirty_color="$YELLOW"
    fi
    git_display=" ${MAGENTA}${git_branch}${RESET}${dirty_color}${git_dirty}${RESET}"
  fi
fi

# Map provider-specific model IDs back to friendly names when aliases are available.
model_name=""
case "$model_id" in
"$ANTHROPIC_DEFAULT_OPUS_MODEL") model_name="$ANTHROPIC_DEFAULT_OPUS_MODEL_NAME" ;;
"$ANTHROPIC_DEFAULT_SONNET_MODEL") model_name="$ANTHROPIC_DEFAULT_SONNET_MODEL_NAME" ;;
"$ANTHROPIC_DEFAULT_HAIKU_MODEL") model_name="$ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME" ;;
esac
if [ -z "$model_name" ]; then
  model_name="${model_display:-$model_id}"
fi
model_alias=$(echo "$model_name" | sed 's/^Claude //')

# Effort level (only present when the model supports it)
effort_display=""
if [ -n "$effort_level" ]; then
  effort_display=" ${DIM}(${effort_level})${RESET}"
fi

# Context window usage with threshold coloring
context_display=""
if [ "$ctx_size" -gt 0 ]; then
  current_tokens=$((current_input + cache_creation + cache_read))
  pct=$((current_tokens * 100 / ctx_size))
  if [ "$pct" -ge 90 ]; then
    ctx_color="$RED"
  elif [ "$pct" -ge 75 ]; then
    ctx_color="$ORANGE"
  elif [ "$pct" -ge 50 ]; then
    ctx_color="$YELLOW"
  else
    ctx_color="$GREEN"
  fi
  summary_marker=""
  if [ "$summarized_turns" -gt 0 ]; then
    summary_marker="~"
  fi
  context_display="${ctx_color}${pct}%${summary_marker}${RESET}"
fi

# Session duration
session_display=""
if [ "$duration_ms" -gt 0 ]; then
  elapsed=$((duration_ms / 1000))
  hours=$((elapsed / 3600))
  minutes=$(((elapsed % 3600) / 60))
  if [ "$hours" -gt 0 ]; then
    session_display="${DIM}${hours}h${minutes}m${RESET}"
  else
    session_display="${DIM}${minutes}m${RESET}"
  fi
fi

# Cost
cost_display=""
if [ "$cost_usd" != "0" ]; then
  cost_display="${DIM}$(printf '$%.2f' "$cost_usd")${RESET}"
fi

# Lines changed (green added / red removed)
lines_display=""
if [ "$lines_added" -gt 0 ] || [ "$lines_removed" -gt 0 ]; then
  lines_display="${GREEN}+${lines_added}${RESET}/${RED}-${lines_removed}${RESET}"
fi

# Vim mode
vim_display=""
if [ -n "$vim_mode" ]; then
  vim_display=" ${YELLOW}[${vim_mode}]${RESET}"
fi

# Assemble: project branch model ctx% duration cost lines [vim]
segments="${BOLD}${CYAN}${project_name}${RESET}${git_display}  ${BLUE}${model_alias}${RESET}${effort_display}"

[ -n "$context_display" ] && segments="$segments  $context_display"
[ -n "$session_display" ] && segments="$segments  $session_display"
[ -n "$cost_display" ] && segments="$segments  $cost_display"
[ -n "$lines_display" ] && segments="$segments  $lines_display"
[ -n "$vim_display" ] && segments="$segments$vim_display"

printf "%s" "$segments"
