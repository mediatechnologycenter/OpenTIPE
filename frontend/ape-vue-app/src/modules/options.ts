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
import { browserLocalPersistence } from '@firebase/auth';
import log, { LogLevelDesc } from 'loglevel';
import { getEnvVarOrFallback } from './environmentUtil';
import { EnvironmentVariable, LanguageCode } from './types';

log.setLevel(
  getEnvVarOrFallback<LogLevelDesc>(EnvironmentVariable.logLevel, 'TRACE'),
);

const devFirebaseConfig = {
  apiKey: '',
  appId: '',
  messagingSenderId: '',
  projectId: '',
  authDomain: '',
  storageBucket: '',
};

const prodFirebaseConfig = {
  apiKey: '',
  appId: '',
  messagingSenderId: '',
  projectId: '',
  authDomain: '',
  storageBucket: '',
};

const options = {
  /**
   * GENERAL OPTIONS -------------------------------------------------------------------------------
   */

  // Generate a fake machine translation and fake suggestions instead of contacting the backend.
  useFakeApi: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.enableFakeApi,
    true,
  ),

  // This can be used to simulate that the translation takes some time. Value in milliseconds.
  fakeApiDelay: getEnvVarOrFallback<number>(
    EnvironmentVariable.fakeApiDelay,
    500,
  ),

  // In percent divided by 100
  maxSuggestionRatio: getEnvVarOrFallback<number>(
    EnvironmentVariable.maxSuggestionRatio,
    0.2,
  ),

  baseUrlApi: getEnvVarOrFallback<string>(EnvironmentVariable.backendURL, ''),

  // Controls the character limit for the translation.
  enableCharacterLimit: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.enableCharacterLimit,
    true,
  ),

  characterLimit: getEnvVarOrFallback<number>(
    EnvironmentVariable.characterLimit,
    10000,
  ),

  saveAllTextSegments: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.sendAllTextSegments,
    true,
  ),

  /**
   * LANGUAGE OPTIONS ------------------------------------------------------------------------------
   */

  availableLanguagePairs: [
    {
      from: LanguageCode.German,
      to: LanguageCode.English,
      allowUserDict: true,
      availableDicts: [],
    },
    // {
    //  from: LanguageCode.German,
    //  to: LanguageCode.French,
    //  allowUserDict: true,
    //  availableDicts: [],
    // },
  ] as {
    from: LanguageCode;
    to: LanguageCode;
    allowUserDict: Boolean;
    availableDicts: string[];
  }[],

  // If this is selected, the user can select multiple dictionaries at the same time.
  // Otherwise, they can only select one dictionary per translation.
  allowMultipleDictSelection: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.allowMultipleDictSelection,
    true,
  ),

  enableSpellcheck: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.enableSpellcheck,
    true,
  ),

  /**
   * AUTHENTICATION OPTIONS ------------------------------------------------------------------------
   */

  environment: getEnvVarOrFallback<string>(
    EnvironmentVariable.environment,
    'dev',
  ).toLowerCase(),

  firebaseConfig: getEnvVarOrFallback<string>(EnvironmentVariable.environment, 'dev').toLowerCase() === 'prod' ? prodFirebaseConfig : devFirebaseConfig,

  enableAuthInDevelopment: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.enableAuthInDev,
    false,
  ),

  enableAuthInProduction: getEnvVarOrFallback<boolean>(
    EnvironmentVariable.enableAuthInProd,
    false,
  ),

  // Controls when the user will be logged out automatically
  loginPersistence: browserLocalPersistence,
};

export default options;
