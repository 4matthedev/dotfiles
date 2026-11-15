#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

# opencode
export PATH=/home/turker/.opencode/bin:$PATH

# Prism ML llama.cpp
export PATH=/home/turker/.local/share/prism-llama/llama-prism-b12128-d7b2896:/home/turker/.local/bin:$PATH
export LLAMA_ARG_MODELS_DIR=/home/turker/models
