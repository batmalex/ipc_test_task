#!/bin/bash

# Start the first process
/usr/local/bin/python3.8  ./manager.py

/bin/bash -c "sleep 5"

/usr/local/bin/python3.8 ./fetcher.py


# Exit with status of process that exited first
# exit $?