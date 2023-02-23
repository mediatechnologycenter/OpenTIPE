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
import { v4 as uuid } from 'uuid';
import {
  reactive, watch, InjectionKey,
} from 'vue';
import { getDeepCopyOfObject, getLanguagePairKey } from '../modules/otherUtil';
import {
  LanguageCode,
  LanguagePairKey,
  PartialStoreState,
  StoreState,
  TextSegment,
  TextSegmentEditType,
  Translatable,
} from '@/modules/types';
import { getHighlights } from '@/modules/suggestionUtil';
import options from '@/modules/options';
import { parseUserDictRaw } from '@/modules/dictUtil';

function getLocalStorage() {
  const localStorageState = localStorage.getItem('state');
  if (!localStorageState) return null;
  return JSON.parse(localStorageState);
}

async function setLocalStorage(state: StoreState) {
  localStorage.setItem('state', JSON.stringify(state));
}

function replaceStateWithSavedValues(state: StoreState) {
  const localStorageStore = getLocalStorage();

  if (
    localStorageStore
    && localStorageStore.dataVersion !== null
    && localStorageStore.dataVersion === state.dataVersion
  ) {
    Object.assign(state, localStorageStore);
  }
}

const initialState: StoreState = {
  // The data in local storage will only be used if the data version matches.
  dataVersion: 22,

  originalEditorContent: { type: 'doc' },

  // The initial structure of the editor content
  originalStructure: null,

  // Text segments before the translation
  originalTextSegments: null,

  // Text segments after the translation
  textSegmentsFromApi: null,

  // Translated text segments with some post processing without any edits
  initialAugmentedTextSegments: null,

  // Translated text segments with some post processing and with all edits
  augmentedTextSegments: null,

  // The structure of the editor content after possible changes
  augmentedStructure: null,

  // The id of the current session
  translationSessionId: '',

  // Languages used in the translation
  srcLang: LanguageCode.German,
  trgLang: LanguageCode.English,

  // This object holds all information about dictionaries for each available language pair
  dictionaries: {},

  // Firebase user object
  user: null,

  // Meta information that prevents stores to the local storage of an intermediate state
  isInTransaction: false,

  // This is used to decide whether the user should be nudged to click on the first suggestion
  usingTheApplicationForTheFirstTime: true,
};

/**
 * This will populate or update the dictionary object in the state.
 * Selected dictionaries that are no longer available will be unselected.
 * Empty fields will be populated.
 * Dictionary options of no longer supported language pairs will not be deleted.
 */
function updateDictionaryOptions(state: StoreState) {
  options.availableLanguagePairs.forEach((langPair) => {
    const langPairKey = getLanguagePairKey(langPair.from, langPair.to);

    const dictObject = state.dictionaries[langPairKey] || {};

    dictObject.availableDicts = langPair.availableDicts || [];
    dictObject.selectedDicts = dictObject.selectedDicts?.filter((d) => dictObject.availableDicts.includes(d)) || [];
    dictObject.userDictJSON = dictObject.userDictJSON || {};
    dictObject.userDictRaw = dictObject.userDictRaw || '';

    state.dictionaries[langPairKey] = dictObject;
  });
}

const state = reactive<StoreState>(initialState);
replaceStateWithSavedValues(state);
updateDictionaryOptions(state);

// Printing and saving the state when it changes
watch(
  state,
  (s) => {
    if (!s.isInTransaction) {
      setLocalStorage(s);
    }
  },
  { deep: true },
);

const methods = {
  // Change to support multiple suggestions.
  /**
   * Apply the currently active suggestion in the passed text segment.
   * @param textSegment The text segment in which the active suggestion is to be applied.
   */
  applySuggestion: async (textSegment: TextSegment) => {
    if (!state.augmentedTextSegments) {
      throw new Error(
        'Cannot apply suggestion if there are no augmentedTextSegments.',
      );
    }

    const { _id } = textSegment;

    state.augmentedTextSegments.forEach((ts) => {
      if (ts._id === _id) {
        const {
          apeText,
          suggestionIsActive,
        } = ts;

        if (!suggestionIsActive) {
          throw new Error(
            'Cannot apply suggestion when suggestion is inactive.',
          );
        }

        const before = ts.hpeText;
        const after = apeText;
        // eslint-disable-next-line no-param-reassign
        ts.hpeText = after;
        // eslint-disable-next-line no-param-reassign
        ts.suggestionIsActive = false;
        ts.edits.push({
          type: TextSegmentEditType.accepted,
          before,
          after,
        });
      }

      return ts;
    });
  },

  /**
   * Discard the active suggestion in the passed text segment.
   * @param textSegment The text segment in which the active suggestion is to be discarded.
   */
  discardSuggestion: async (textSegment: TextSegment) => {
    if (!state.augmentedTextSegments) {
      throw new Error(
        'Cannot reject suggestion if there are no augmentedTextSegments.',
      );
    }

    const { _id } = textSegment;

    state.augmentedTextSegments.forEach((ts) => {
      if (ts._id === _id) {
        const {
          suggestionIsActive,
          mtText,
          hpeText,
        } = ts;

        if (!suggestionIsActive) {
          throw new Error('Cannot reject inactive suggestion.');
        }

        const before = hpeText;
        const after = mtText;
        // eslint-disable-next-line no-param-reassign
        ts.hpeText = after;
        // eslint-disable-next-line no-param-reassign
        ts.suggestionIsActive = false;
        ts.edits.push({
          type: TextSegmentEditType.rejected,
          before,
          after,
        });
      }

      return ts;
    });
  },
  applyEdits: async (newTextSegments: Translatable[]) => {
    if (!state.augmentedTextSegments) {
      throw new Error(
        'Cannot apply edits if there are no augmentedTextSegments.',
      );
    }

    newTextSegments.forEach(async (nts) => {
      if (!state.augmentedTextSegments) {
        throw new Error(
          'Cannot apply edits if there are no augmentedTextSegments.',
        );
      }

      const {
        _id,
        srcText,
      } = nts;
      const existingTextSegment = state.augmentedTextSegments.find(
        (s) => s._id === _id,
      );

      if (!existingTextSegment) {
        // New textSegment was found.

        const ts: TextSegment = {
          _id: nts._id,
          srcText: '',
          mtText: '',
          mtTextStructure: [],
          apeTextStructure: [],
          hpeText: nts.srcText,
          edits: [
            {
              type: TextSegmentEditType.created,
              before: '',
              after: nts.srcText,
            },
          ],
          apeText: '',
          suggestionIsActive: false,
        };

        state.augmentedTextSegments.push(ts);
      } else if (
        // Existing textSegment was found.
        srcText !== existingTextSegment.hpeText
      ) {
        const before = existingTextSegment.hpeText;
        const after = srcText;
        existingTextSegment.hpeText = after;
        existingTextSegment.suggestionIsActive = false;
        existingTextSegment.edits.push({
          type: TextSegmentEditType.edited,
          before,
          after,
        });
      }
    });

    state.augmentedTextSegments.forEach((existingTextSegment) => {
      const newTextSegment = newTextSegments.find(
        (s) => s._id === existingTextSegment._id,
      );
      if (!newTextSegment) {
        // Text segment was deleted.

        existingTextSegment.edits.push({
          type: TextSegmentEditType.deleted,
          before: existingTextSegment.hpeText,
          after: '',
        });
        // eslint-disable-next-line no-param-reassign
        existingTextSegment.hpeText = '';
        // eslint-disable-next-line no-param-reassign
        existingTextSegment.suggestionIsActive = false;
      }
    });
  },
  replaceState(newState: StoreState) {
    Object.assign(state, newState);
  },
  updateState(partialState: PartialStoreState, keepTransaction = false) {
    state.isInTransaction = true;
    const { originalEditorContent } = partialState;
    if (originalEditorContent) {
      // We need to reset these properties if the original text changes
      // We can't just replace the current state with the entire initial state because this would
      // log the user out.
      const {
        originalStructure,
        originalTextSegments,
        textSegmentsFromApi,
        augmentedTextSegments,
        initialAugmentedTextSegments,
        augmentedStructure,
        translationSessionId,
      } = initialState;

      Object.assign(state, {
        originalStructure,
        originalTextSegments,
        textSegmentsFromApi,
        augmentedTextSegments,
        initialAugmentedTextSegments,
        augmentedStructure,
        translationSessionId,
      });

      // We also need to set a new translationSessionId if the original text is changed
      state.translationSessionId = uuid();

      state.originalEditorContent = originalEditorContent;
    }

    const { originalStructure } = partialState;
    if (originalStructure) {
      state.originalStructure = originalStructure;
      state.augmentedStructure = originalStructure;
    }

    const { originalTextSegments } = partialState;
    if (originalTextSegments) {
      state.originalTextSegments = originalTextSegments;
    }

    const { textSegmentsFromApi } = partialState;
    if (textSegmentsFromApi) {
      state.textSegmentsFromApi = textSegmentsFromApi;
      // This needs to be changed if the api changes.
      state.augmentedTextSegments = getDeepCopyOfObject(
        textSegmentsFromApi.map((ts): TextSegment => {
          const hasActiveSuggestion = ts.mtText !== ts.apeText;
          const structure = getHighlights(ts.mtText, ts.apeText);

          return {
            _id: ts._id,
            srcText: ts.srcText,
            mtText: ts.mtText,
            mtTextStructure: structure.fromHighlights,
            apeTextStructure: structure.toHighlights,
            hpeText: ts.mtText,
            suggestionIsActive: hasActiveSuggestion,
            apeText: ts.apeText,
            edits: [],
          };
        }),
      );
      state.initialAugmentedTextSegments = getDeepCopyOfObject(
        state.augmentedTextSegments,
      );
    }

    const { augmentedStructure } = partialState;
    if (augmentedStructure) {
      state.augmentedStructure = augmentedStructure;
    }

    const { user } = partialState;
    if (user !== undefined) {
      state.user = user;
    }

    const { srcLang } = partialState;
    if (srcLang !== undefined) {
      state.srcLang = srcLang;
    }

    const { trgLang } = partialState;
    if (trgLang !== undefined) {
      state.trgLang = trgLang;
    }

    const { usingTheApplicationForTheFirstTime } = partialState;
    if (usingTheApplicationForTheFirstTime !== undefined) {
      state.usingTheApplicationForTheFirstTime = usingTheApplicationForTheFirstTime;
    }

    state.isInTransaction = keepTransaction;
  },

  updateUserDictRaw: (
    langPairKey: LanguagePairKey<LanguageCode, LanguageCode>,
    userDictRaw: string,
  ) => {
    const langDictionaries = state.dictionaries[langPairKey];
    if (!langDictionaries) {
      throw Error(
        `Dictionaries object for language pair ${langPairKey} could not be found`,
      );
    }
    langDictionaries.userDictRaw = userDictRaw;
    langDictionaries.userDictJSON = parseUserDictRaw(userDictRaw);
  },

  updateSelectedDicts: (
    langPairKey: LanguagePairKey<LanguageCode, LanguageCode>,
    selectedDicts: string[],
  ) => {
    const langDictionaries = state.dictionaries[langPairKey];
    if (!langDictionaries) {
      throw Error(
        `Dictionaries object for language pair ${langPairKey} could not be found`,
      );
    }
    langDictionaries.selectedDicts = selectedDicts;
  },
};

const store = {
  state,
  methods,
};

const storeKey: InjectionKey<typeof store> = Symbol('store');

export { store, storeKey };
