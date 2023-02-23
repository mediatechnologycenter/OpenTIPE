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
import { isInDevelopmentMode } from './environmentUtil';
import options from './options';
import { LanguagePairKey } from './types';

/**
 * @param str A string
 * @returns An array of sentences in str and the whitespace that divides them.
 */
function splitStringIntoSentencesAndWhitespace(str: string) {
  const matchedString = str.replace(
    /([.|:|!|?]+)(["|“|”|‘|’|'|«|»|「|」|(|)|{|}|[|\]]*)([.|:|!|?]*)([\s|\n|\r|\n]+)/gm,
    '$1$2$3|$4|',
  );

  return matchedString.split('|').filter((s) => s.length > 0);
}

/**
 * Removes all whitespace characters at the end of a string.
 * @returns The cleaned string.
 */
function removeTrailingWhitespace(str: string) {
  return str.replace(/(\s|\n|\r|\n)*$/gm, '');
}

// Returns true if string is empty.
function stringContainsOnlyWhitespace(str: string) {
  return !str.replace(/(\s|\n|\r|\n)*/g, '').length;
}

function getLastElementInArray<A>(arr: A[]) {
  return arr.length === 0 ? undefined : arr[arr.length - 1];
}

function getDeepCopyOfObject<A>(obj: A): A {
  return JSON.parse(JSON.stringify(obj));
}

function posMod(n: number, m: number) {
  const remain = n % m;
  return Math.floor(remain >= 0 ? remain : remain + m);
}

function authenticationIsEnabled() {
  return (
    (isInDevelopmentMode() && options.enableAuthInDevelopment)
    || (!isInDevelopmentMode() && options.enableAuthInProduction)
  );
}

function getLanguagePairKey<T1 extends string, T2 extends string>(
  sourceLangCode: T1,
  targetLangCode: T2,
) {
  return `${sourceLangCode}-${targetLangCode}` as LanguagePairKey<T1, T2>;
}

/**
 * This function is intended to be used like this: arr.filter(onlyUniqueValues)
 * If used like this, it will filter out all duplicated values in arr.
 */
function onlyUniqueValues<A, B extends Array<A>>(
  value: A,
  index: number,
  self: B,
) {
  return self.indexOf(value) === index;
}

export {
  posMod,
  splitStringIntoSentencesAndWhitespace,
  removeTrailingWhitespace,
  getDeepCopyOfObject,
  stringContainsOnlyWhitespace,
  getLastElementInArray,
  authenticationIsEnabled,
  getLanguagePairKey,
  onlyUniqueValues,
};
