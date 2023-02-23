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
import options from './options';
import { getLanguagePairKey } from './otherUtil';
import { LanguageCode, LanguagePairKey } from './types';

function validateUserDictLine(line: string, lineNumber: number) {
  if (line.length === 0) {
    throw new Error(`Line ${lineNumber} is empty.`);
  }
  const numEqual = line.split('').filter((c) => c === '=').length;
  if (numEqual !== 1) {
    throw new Error(
      `Each line must contain exactly one equal sign. In line ${
        lineNumber + 1
      }, there are ${numEqual} equal signs.`,
    );
  }

  const elements = line.split('=');
  if (elements.length !== 2 || elements[0] === '' || elements[1] === '') {
    throw new Error(`Line ${lineNumber + 1} is invalid`);
  }

  const matches = line.match(/([\p{L}-]|[-=])*/gu);
  let illegalCharacters = line;
  // eslint-disable-next-line no-unused-expressions
  matches?.forEach((match) => {
    illegalCharacters = illegalCharacters.replaceAll(match, '');
  });

  if (illegalCharacters.length > 0) {
    throw new Error(
      `Line ${
        lineNumber + 1
      } contains invalid characters: ${illegalCharacters}`,
    );
  }
}

function validateUserDict(val: string) {
  const lines = val.split('\n');
  lines.forEach((line, i) => {
    if (line.length === 0) {
      return;
    }
    validateUserDictLine(line, i);
  });
}

function parseUserDictRaw(input: string) {
  const result: { [key: string]: string } = {};
  input.split('\n').forEach((line) => {
    try {
      validateUserDictLine(line, 0);
      const lineElements = line.split('=');
      const key = lineElements[0];
      const value = lineElements[1];
      result[key] = value;
    } catch {
      // In case of an error, we do nothing. Only valid lines will be converted into JSON.
    }
  });
  return result;
}

function userDictShouldBeDisplayed(
  languagePairKey: LanguagePairKey<LanguageCode, LanguageCode>,
) {
  return !!options.availableLanguagePairs.filter(
    (x) => getLanguagePairKey(x.from, x.to) === languagePairKey,
  )[0]?.allowUserDict;
}

export { userDictShouldBeDisplayed, validateUserDict, parseUserDictRaw };
