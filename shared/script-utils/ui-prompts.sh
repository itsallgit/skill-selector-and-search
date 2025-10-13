#!/bin/bash

# =============================================================================
# UI Prompt Utilities
# =============================================================================
# Provides user interaction prompts and confirmation dialogs.

# Source required utilities (only if not already sourced)
if ! type print_status &>/dev/null; then
    UTILS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$UTILS_DIR/logging.sh"
fi

# Prompt user for yes/no confirmation
# Usage: prompt_yes_no "Question?" "Y" (returns 0 for yes, 1 for no)
prompt_yes_no() {
    local question="$1"
    local default="${2:-N}"  # Default to N if not specified
    local prompt_text
    
    if [ "$default" = "Y" ] || [ "$default" = "y" ]; then
        prompt_text="(Y/n)"
    else
        prompt_text="(y/N)"
    fi
    
    read -p "$question $prompt_text: " -n 1 -r
    echo
    
    if [ -z "$REPLY" ]; then
        # User pressed enter without typing
        [[ "$default" =~ ^[Yy]$ ]] && return 0 || return 1
    fi
    
    [[ $REPLY =~ ^[Yy]$ ]] && return 0 || return 1
}

# Prompt for text input with validation
# Usage: result=$(prompt_text "Enter name:" "default_value" "non-empty")
prompt_text() {
    local question="$1"
    local default="$2"
    local validation="${3:-none}"  # none, non-empty, etc.
    local input
    
    while true; do
        if [ -n "$default" ]; then
            read -p "$question [$default]: " input
            input="${input:-$default}"
        else
            read -p "$question: " input
        fi
        
        # Remove leading/trailing whitespace
        input="$(echo -n "$input" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        
        case "$validation" in
            non-empty)
                if [ -z "$input" ]; then
                    print_warning "Input cannot be empty."
                    continue
                fi
                ;;
        esac
        
        echo "$input"
        return 0
    done
}

# Prompt for selection from a list
# Usage: selected=$(prompt_selection "Choose option:" "opt1" "opt2" "opt3")
prompt_selection() {
    local question="$1"
    shift
    local options=("$@")
    local selection
    
    echo "$question"
    for i in "${!options[@]}"; do
        echo "  [$((i+1))] ${options[$i]}"
    done
    
    while true; do
        read -p "Enter selection [1-${#options[@]}]: " selection
        
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#options[@]}" ]; then
            echo "${options[$((selection-1))]}"
            return 0
        else
            print_warning "Invalid selection. Please enter a number between 1 and ${#options[@]}."
        fi
    done
}

# Prompt for dangerous confirmation (requires typing a word)
# Usage: prompt_dangerous_confirmation "DELETE" "delete the bucket" (returns 0 if confirmed)
prompt_dangerous_confirmation() {
    local confirmation_word="$1"
    local action_description="$2"
    
    print_confirm "This action will $action_description and CANNOT be undone!"
    read -p "Type '$confirmation_word' to confirm: " confirmation
    
    if [ "$confirmation" = "$confirmation_word" ]; then
        return 0
    else
        print_warning "Confirmation cancelled."
        return 1
    fi
}
