#!/bin/bash
# Read Java source from stdin, write to Main.java, compile and run.
# set -e means: if javac fails, the script exits immediately with javac's
# exit code, and its stderr is captured by executor.py.

set -e

mkdir -p /sandbox
cat > /sandbox/Main.java
javac /sandbox/Main.java
java -cp /sandbox Main
