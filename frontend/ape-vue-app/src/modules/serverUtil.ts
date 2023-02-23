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
import { User } from '@firebase/auth';
import { LoremIpsum } from 'lorem-ipsum';
import options from './options';
import {
  DictionaryEntries,
  LanguageCode,
  SendPostEditRequestBody,
  TextSegment,
  TextSegmentEditType,
  Translatable,
  TranslationRequestBody,
  TranslationResponseBody,
  TranslationResult,
} from './types';

/**
 * Randomly removes suggestions if there are too many.
 */
function suggestionLimiter(
  tr: TranslationResult[],
  maxSuggestionRatio: number,
) {
  const results = [...tr];
  if (maxSuggestionRatio >= 1 || maxSuggestionRatio < 0) return results;

  const numTextSegments = results.length;
  // Count the number of present suggestions.
  let numPresentSuggestions = 0;
  results.forEach((r) => {
    if (r.mtText !== r.apeText) {
      numPresentSuggestions += 1;
    }
  });

  // If there are no suggestions we are done.
  if (numPresentSuggestions === 0) {
    return results;
  }

  // How many suggestions there should be according to the max suggestion ratio.
  const targetSuggestionNum = numTextSegments * maxSuggestionRatio;

  if (numPresentSuggestions > targetSuggestionNum) {
    const numToRemove = numPresentSuggestions - targetSuggestionNum;
    const removalProbability = numToRemove / numPresentSuggestions;

    // Remove each suggestion with the calculated probability.
    results.forEach((r) => {
      if (r.mtText !== r.apeText && Math.random() <= removalProbability) {
        // eslint-disable-next-line no-param-reassign
        r.apeText = r.mtText;
      }
    });
  }

  return results;
}

async function requestFakeTranslationData(textSegments: Translatable[]) {
  const result: TranslationResult[] = [];
  const lorem = new LoremIpsum();

  textSegments.forEach((element) => {
    const prefix = element.srcText[0] === ' ' ? element.srcText[0] : '';
    const mt = `${prefix}${lorem.generateSentences(1)}`;
    let pe;

    if (Math.random() < options.maxSuggestionRatio) {
      pe = `${prefix}${lorem.generateSentences(1)}`;
    } else {
      pe = mt;
    }

    result.push({
      _id: element._id,
      srcText: element.srcText,
      mtText: mt,
      apeText: pe,
    });
  });

  return new Promise<TranslationResult[]>((resolve) => {
    setTimeout(() => {
      resolve(result);
    }, options.fakeApiDelay);
  });
}

async function getUserToken(user: User | null) {
  let userToken = '';

  if (user !== null) {
    userToken = await user.getIdToken();
  }

  return userToken;
}

async function requestRealTranslationData(
  textSegments: Translatable[],
  srcLang: LanguageCode,
  trgLang: LanguageCode,
  translationSessionId: string,
  user: User | null,
  userDict: DictionaryEntries,
  selectedDicts: string[],
): Promise<TranslationResult[]> {
  const userToken = await getUserToken(user);

  const body: TranslationRequestBody = {
    _id: translationSessionId,
    srcLang,
    trgLang,
    textSegments,
    userDict,
    selectedDicts,
  };

  const response = await fetch(`${options.baseUrlApi}/translate`, {
    method: 'POST',
    headers: {
      Accept: '*/*',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${userToken}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(response.statusText);
  }

  const responseBody: TranslationResponseBody = await response.json();

  return responseBody.textSegments.map((ts) => {
    if (ts.mtText === undefined) {
      throw new Error(
        `The server returned no translation for the text segment with id "${ts._id}": "${ts.srcText}"`,
      );
    }
    if (ts.apeText === undefined) {
      throw new Error(
        `The server returned no post-edit for the text segment with id "${ts._id}": "${ts.srcText}"`,
      );
    }
    return ts as TranslationResult;
  });
}

async function requestTranslationData(
  textSegments: Translatable[],
  srcLang: LanguageCode,
  trgLang: LanguageCode,
  translationSessionId: string,
  user: User | null,
  userDict: DictionaryEntries,
  selectedDicts: string[],
) {
  return options.useFakeApi
    ? requestFakeTranslationData(textSegments)
    : suggestionLimiter(
      await requestRealTranslationData(
        textSegments,
        srcLang,
        trgLang,
        translationSessionId,
        user,
        userDict,
        selectedDicts,
      ),
      options.maxSuggestionRatio,
    );
}

async function sendPostEditData(
  textSegments: TextSegment[],
  srcLang: LanguageCode,
  trgLang: LanguageCode,
  translationSessionId: string,
  user: User | null,
  selectedDicts: string[],
  userDict: DictionaryEntries,
) {
  const userToken = await getUserToken(user);
  const body: SendPostEditRequestBody = {
    _id: translationSessionId,
    srcLang,
    trgLang,
    textSegments: textSegments.map((ts) => ({
      ...ts,
      // Accepted iff the suggestion was accepted at some point in the edit history.
      apeAccepted:
        ts.edits.filter((edit) => edit.type === TextSegmentEditType.accepted)
          .length > 0,
    })),
    selectedDicts,
    userDict,
  };

  const response = await fetch(`${options.baseUrlApi}/post-edition`, {
    method: 'POST',
    headers: {
      Accept: '*/*',
      'Content-Type': 'application/json',
      Authorization: `Bearer ${userToken}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(response.statusText);
  }
}

export { requestTranslationData, sendPostEditData, getUserToken };
