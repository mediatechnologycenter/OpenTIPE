#!/bin/sh

# Copyright 2022 ETH Zurich, Media Technology Center

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# First we create a Javascript expression that creates an object containing the env variables
# and stores it in window.configs.
echo "Creating JSON_STRING"
JSON_STRING="window.configs = {"

# In the following loop, we split the env file by newline
IFS=$'\n'

# Iterate over all environment variables
for item in $(env); do
  value=${item#*=}
  name=${item%%=*}

  # We care only about env variables that start with the prefix "VUE_APP"
  case "$name" in "VUE_APP"*)
    # Append the variable name and value to the JSON_STRING
  	JSON_STRING="$JSON_STRING \"$name\": \"$value\","
  esac
done

# Finalize the Javascript expression
JSON_STRING="$JSON_STRING }"

echo "Done:"
echo $JSON_STRING

# Now we replace the placeholder in index.html with the Javascript expression (JSON_STRING) that
# we just created. Once the frontend starts, the browser will evaluate this expression and thus
# store our env variables in a window.configs object.
echo "Writing the JSON_STRING to index.html"
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i "" "s@// CONFIGURATIONS_PLACEHOLDER@${JSON_STRING}@" /usr/share/nginx/html/index.html
else
  sed -i "s@// CONFIGURATIONS_PLACEHOLDER@${JSON_STRING}@" /usr/share/nginx/html/index.html
fi
