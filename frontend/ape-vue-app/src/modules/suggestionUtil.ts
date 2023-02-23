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
import { Change, diffWords } from 'diff';
import { stringContainsOnlyWhitespace } from './otherUtil';
import { TextSegment, TextSegmentStructureElement } from './types';

/**
 * This id is used if no text segment is currently selected.
 */
const defaultTextSegmentId = '-1';

/**
 * Returns an id that is defined in any case.
 */
function getCleanId(id: any) {
  if (id === null || id === undefined) {
    return defaultTextSegmentId;
  }
  return String(id);
}

/**
 * @returns Whether the text segment has an active suggestion or not.
 */
function hasActiveSuggestion(textSegment: TextSegment) {
  return textSegment.suggestionIsActive;
}

/**
 * Gets the id of another text segment with an active suggestion.
 * @param currentTextSegment The currently selected textSegment.
 * @param textSegments All available textSegments.
 * @param direction Specifies in which direction it should the next text segment.
 * @returns The id of the next text segment with an active id in the specified direction. Returns -1
 * if something goes wrong.
 */
function getIdOfAdjacentTextSegmentWithActiveSuggestion(
  currentTextSegment: TextSegment,
  textSegments: TextSegment[],
  direction: 'forward' | 'backward',
) {
  const tsWithSuggestion = textSegments.filter(
    (ts) => ts.suggestionIsActive || ts._id === currentTextSegment._id,
  );
  const currentIndex = tsWithSuggestion.findIndex(
    (ts) => ts._id === currentTextSegment._id,
  );
  const newId = tsWithSuggestion[currentIndex + (direction === 'forward' ? 1 : -1)]?._id;
  return getCleanId(newId);
}

/**
 * @param textSegments Array of textSegments
 * @returns Array of textSegments with active suggestion.
 */
function getTextSegmentsWithActiveSuggestion(textSegments: TextSegment[]) {
  return textSegments.filter((s) => hasActiveSuggestion(s));
}

/**
 * Highlights whitespace when both adjacent words are highlighted.
 * @param arr An array with highlight information
 * @returns A cleaned version of arr: non-highlighted whitespace between two consecutive highlighted
 * text regions will be highlighted as well.
 */
function highlightWhitespaceBetweenHighlights(
  arr: TextSegmentStructureElement[],
) {
  const initialVal = {
    a: null as TextSegmentStructureElement | null,
    b: null as TextSegmentStructureElement | null,
    result: [] as TextSegmentStructureElement[],
  };

  function reducer(
    acc: typeof initialVal,
    c: TextSegmentStructureElement,
    i: number,
    // eslint-disable-next-line @typescript-eslint/no-shadow
    arr: TextSegmentStructureElement[],
  ) {
    // Buffer not full
    if (acc.a === null || acc.b === null) {
      acc.a = acc.b;
      acc.b = c;
    } else if (
      acc.a.highlight
      && !acc.b.highlight
      && c.highlight
      && stringContainsOnlyWhitespace(acc.b.value)
    ) {
      // We can merge the three items in this case.
      const newElement = {
        value: acc.a.value + acc.b.value + c.value,
        highlight: true,
      };

      acc.a = null;
      acc.b = newElement;
    } else {
      // We cannot merge the three items
      acc.result.push(acc.a);
      acc.a = acc.b;
      acc.b = c;
    }

    // Cleanup if it's the last element (add buffer elements to the result)
    if (i === arr.length - 1) {
      [acc.a, acc.b].forEach((el) => {
        if (el !== null) {
          acc.result.push(el);
        }
      });
    }

    return acc;
  }

  return arr.reduce(reducer, initialVal).result;
}

/**
 * @param from The original text
 * @param to The new text
 * @param strategy Either 'removed' or 'added'.
 * @param diff Array of changes (result of diffing algorithm)
 * @returns If strategy === 'removed', it will return the changes in the original text (which parts were removed).
 * If strategy === 'added', it will return the changes in the new text (which parts were added).
 */
function getHighlightsWithStrategy(
  strategy: 'removed' | 'added',
  diff: Change[],
) {
  // We only want to know which parts of the string need to be highlighted.
  // If the strategy is 'removed', we want to know which parts stay the same in the text and
  // which parts are removed. We don't care about anything else in that case. We treat the case where
  // the strategy is 'added' analogously

  interface Accumulator {
    currentChain: TextSegmentStructureElement | null;
    result: TextSegmentStructureElement[];
  }

  const initialVal: Accumulator = {
    currentChain: null,
    result: [],
  };

  /**
   * Filters out all changes that do not correspond to the current strategy.
   * Combines changes that belong together according to the strategy.
   * @param acc The accumulated result until now.
   * @param c The current change (element of arr)
   * @param i The current index in arr
   * @param arr The array we're working on
   * @returns A new accumulator that is created by combining acc and c
   */
  function filterAndCombineChanges(
    acc: Accumulator,
    c: Change,
    i: number,
    arr: Change[],
  ) {
    const otherStrategy = strategy === 'removed' ? 'added' : 'removed';

    // Only work on relevant elements
    // E.g., if strategy === 'removed' and c.added === true, we skip this element,
    // because it is not relevant if we're looking for words that were deleted from the text.
    if (!c[otherStrategy]) {
      // End a chain
      if (
        acc.currentChain !== null
        // c cannot be added to the current chain because its highlight value differs
        && acc.currentChain.highlight !== Boolean(c[strategy])
      ) {
        acc.result.push(acc.currentChain);
        acc.currentChain = null;
      }

      // Start a chain
      if (acc.currentChain === null) {
        acc.currentChain = {
          // Start with the text value of the current change
          value: c.value,
          // The change's highlight value is that of the current change
          highlight: Boolean(c[strategy]),
        };
      } else {
        // Continue a chain
        // Just concatenate the text value of the current chain with the text value of the the current change c
        acc.currentChain.value += c.value;
      }
    }

    // Tidy up if it's the last change
    if (i === arr.length - 1 && acc.currentChain !== null) {
      acc.result.push(acc.currentChain);
    }

    return acc;
  }

  // Reduces the array from left to right with the function 'reducer' and the initial value 'initialVal'.
  const { result } = diff.reduce(filterAndCombineChanges, initialVal);
  // Highlight whitespace between two consecutive highlighted regions
  return highlightWhitespaceBetweenHighlights(result);
}

/**
 * Decides what parts of the 'from' and the 'to' string should be highlighted
 * See the tests for examples of the functionality.
 * @param from Original text
 * @param to Changed text
 * @returns An object describing what should be highlighted both in the 'from' and 'to' string
 */
function getHighlights(from: string, to: string) {
  // Gives us a list of elements that
  // - are unchanged
  // - were added
  // - were removed
  const diff = diffWords(from, to);

  return {
    fromHighlights: getHighlightsWithStrategy('removed', diff),
    toHighlights: getHighlightsWithStrategy('added', diff),
  };
}

export {
  getIdOfAdjacentTextSegmentWithActiveSuggestion,
  getTextSegmentsWithActiveSuggestion,
  getCleanId,
  defaultTextSegmentId,
  hasActiveSuggestion,
  getHighlights,
};
