#!/bin/sh

# Start supervisord
supervisord -c /etc/supervisord.conf &

# Tail the logs and copy them to the shared directory
tail -F /var/log/uvicorn_stdout.log /var/log/uvicorn_stderr.log /var/log/gradio_stdout.log /var/log/gradio_stderr.log | tee -a /mnt/c/GiveToGPT/uvicorn_stdout.log /mnt/c/GiveToGPT/uvicorn_stderr.log /mnt/c/GiveToGPT/gradio_stdout.log /mnt/c/GiveToGPT/gradio_stderr.log
