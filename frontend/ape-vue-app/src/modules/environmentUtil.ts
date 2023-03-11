// Copyright 2022 ETH Zurich, Media Technology Center

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//   http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import { warn } from 'loglevel';
import { EnvironmentVariable } from './types';

/**
 * Get the environment variable with the specified key.
 * As a first preference, variables from the frontend.env will be returned.
 * As a second preference, variables from the node process env will be returned.
 * @param key The key under which the environment variable is stored.
 * @returns The value as a string or null if it cannot be found.
 */
function getEnvVar(key: EnvironmentVariable) {
  const val = (window as any)?.configs?.[key] || process.env[key];
  if (val !== undefined && val !== null) {
    return String(val);
  }
  warn(`The environment variable ${key} could not be found!`);
  return null;
}

/**
 * Tries to return the environment variable with the specified key according to the
 * preference specified in the function getEnvVar.
 * This function will convert the value to the specified type.
 * If this variable cannot be found, the fallback will be returned.
 * @param key
 * @param fallback
 * @returns The found environment variable or the specified fallback.
 * @throws If the type is unsupported.
 */
function getEnvVarOrFallback<ExpectedType>(
  key: EnvironmentVariable,
  fallback: ExpectedType | undefined,
) {
  const val = getEnvVar(key);
  if (val === null || val === undefined) {
    const msgBaseText = `Environment variable ${key} is undefined.`;
    if (fallback === undefined) {
      throw new Error(`${msgBaseText} Also, no fallback is defined.`);
    }
    console.warn(`${msgBaseText} Using fallback instead: ${fallback}`);
    return fallback;
  }
  try {
    // Parsing is required if an object is stored in the variable.
    return JSON.parse(val) as any as ExpectedType;
  } catch (error) {
    // If parsing fails, it is an atomic value (a string).
    return val as any as ExpectedType;
  }
}

function isInDevelopmentMode() {
  const mode = getEnvVarOrFallback(EnvironmentVariable.environment, 'none' as string);
  if (mode === 'none') {
    throw new Error('The environment variable "VUE_APP_ENVIRONMENT" must be defined in frontend.env.');
  }
  return mode === 'DEV';
}

export { getEnvVar, getEnvVarOrFallback, isInDevelopmentMode };
