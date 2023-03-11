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
// eslint-disable-next-line import/no-extraneous-dependencies
import { User } from '@firebase/auth';
import { JSONContent } from '@tiptap/core';

interface DictionaryEntries {
  [key: string]: string;
}

interface Mark {
  type: string;
  attrs?: Record<string, any>;
  [key: string]: any;
}

enum TextSegmentEditType {
  edited = 'edited',
  accepted = 'accepted',
  rejected = 'rejected',
  created = 'created',
  deleted = 'deleted',
}

interface TextSegmentEdit {
  type: TextSegmentEditType;
  before: string;
  after: string;
}

interface Translatable {
  _id: string;
  srcText: string;
}

enum LanguageCode {
  German = 'de',
  French = 'fr',
  English = 'en',
}

type TranslationRequestBody = {
  _id: string;
  srcLang: LanguageCode;
  trgLang: LanguageCode;
  textSegments: {
    _id: string;
    srcText: string;
    mtText?: string;
    apeText?: string;
  }[];
  userDict: DictionaryEntries;
  selectedDicts: string[];
};

type TranslationResponseBody = {
  _id: string;
  srcLang: LanguageCode;
  trgLang: LanguageCode;
  textSegments: {
    _id: string;
    srcText: string;
    mtText?: string;
    apeText?: string;
  }[];
};

type SendPostEditRequestBody = {
  _id: string;
  srcLang: LanguageCode;
  trgLang: LanguageCode;
  textSegments: {
    _id: string;
    srcText: string;
    mtText: string;
    apeText: string;
    hpeText: string;
    apeAccepted: Boolean;
  }[];
  userDict: DictionaryEntries;
  selectedDicts: string[];
};

interface TranslationResult {
  _id: string;
  srcText: string;
  mtText: string;
  apeText: string;
}

interface TextSegmentStructureElement {
  value: string;
  highlight: boolean;
}

interface TextSegment extends Translatable {
  _id: string;
  // Untranslated text
  srcText: string;

  // Machine Translation text
  mtText: string;
  mtTextStructure: TextSegmentStructureElement[];

  // Suggestion from the APE model
  apeText: string;
  apeTextStructure: TextSegmentStructureElement[];

  // The displayed text of the text segment (after all edits).
  hpeText: string;

  // Whether a suggestion should be displayed.
  // This is false once the user edits the text segment.
  suggestionIsActive: boolean;

  // The steps that were taken to get to the final text.
  edits: TextSegmentEdit[];
}

interface MarkIds {
  textSegmentId: string;
}

interface JSONContentStructure extends JSONContent {
  textSegmentId?: string;
  content?: JSONContentStructure[];
}

interface StoreState {
  dataVersion: number;
  originalEditorContent: JSONContent | null;
  originalStructure: JSONContentStructure | null;
  originalTextSegments: Translatable[] | null;
  textSegmentsFromApi: TranslationResult[] | null;
  augmentedTextSegments: TextSegment[] | null;
  initialAugmentedTextSegments: TextSegment[] | null;
  augmentedStructure: JSONContentStructure | null;
  isInTransaction: boolean;
  user: User | null;
  translationSessionId: string;
  srcLang: LanguageCode;
  trgLang: LanguageCode;
  dictionaries: {
    // Keys are of the form de-en, where de is the source and en the target language
    [key: string]: {
      userDictRaw: string;
      userDictJSON: DictionaryEntries;
      selectedDicts: string[];
      availableDicts: string[];
    };
  };
  usingTheApplicationForTheFirstTime: Boolean;
}

type PartialStoreState = Partial<StoreState>;

enum EnvironmentVariable {
  backendURL = 'VUE_APP_BACKEND_URL',
  enableAuthInDev = 'VUE_APP_ENABLE_AUTHENTICATION_IN_DEVELOPMENT',
  enableAuthInProd = 'VUE_APP_ENABLE_AUTHENTICATION_IN_PRODUCTION',
  enableFakeApi = 'VUE_APP_ENABLE_FAKE_API',
  logLevel = 'VUE_APP_LOG_LEVEL',
  characterLimit = 'VUE_APP_CHARACTER_LIMIT',
  enableCharacterLimit = 'VUE_APP_ENABLE_CHARACTER_LIMIT',
  enableSpellcheck = 'VUE_APP_ENABLE_SPELLCHECK',
  fakeApiDelay = 'VUE_APP_FAKE_API_DELAY',
  allowMultipleDictSelection = 'VUE_APP_ALLOW_MULTIPLE_DICTIONARY_SELECTION',
  maxSuggestionRatio = 'VUE_APP_MAX_SUGGESTION_RATIO',
  sendAllTextSegments = 'VUE_APP_SEND_ALL_TEXT_SEGMENTS',
  environment = 'VUE_APP_ENVIRONMENT',
  availableLanguagePairs = 'VUE_APP_AVAILABLE_LANGUAGE_PAIRS',
  devFirebaseConfig = 'VUE_APP_DEV_FIREBASE_CONFIG',
  prodFirebaseConfig = 'VUE_APP_PROD_FIREBASE_CONFIG'
}

enum NotificationMessageType {
  success,
  alert,
  error,
}

type LanguagePairKey<A extends string, B extends string> = `${A}-${B}`;

export {
  NotificationMessageType,
  EnvironmentVariable,
  TranslationRequestBody,
  TranslationResponseBody,
  SendPostEditRequestBody,
  MarkIds,
  TextSegment,
  Translatable,
  TranslationResult,
  Mark,
  JSONContentStructure,
  StoreState,
  PartialStoreState,
  TextSegmentStructureElement,
  LanguageCode,
  TextSegmentEditType,
  DictionaryEntries,
  LanguagePairKey,
};
