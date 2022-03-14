#!/bin/bash

# Start the first process
python3 ./manager.py &

# Wait a bit
/bin/bash -c "sleep 5"

# Start second process
python3 ./fetcher.py &
