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
/* eslint-disable no-console */
import {
  defaultTextSegmentId,
  getHighlights,
  getIdOfAdjacentTextSegmentWithActiveSuggestion,
} from '@/modules/suggestionUtil';
import { TextSegment, TextSegmentStructureElement } from '@/modules/types';

describe(getIdOfAdjacentTextSegmentWithActiveSuggestion, () => {
  // Only id property matters here
  const textSegments: TextSegment[] = [...Array(10).keys()].map(
    (i) => ({
      _id: `${i}`,
      // Even index => has suggestion
      suggestionIsActive: i % 2 === 0,
    } as unknown as TextSegment),
  );

  test('Basic functionality', () => {
    const selectedTextSegment = textSegments[5];

    expect(
      getIdOfAdjacentTextSegmentWithActiveSuggestion(
        selectedTextSegment,
        textSegments,
        'forward',
      ),
    ).toEqual(textSegments[6]._id);

    expect(
      getIdOfAdjacentTextSegmentWithActiveSuggestion(
        selectedTextSegment,
        textSegments,
        'backward',
      ),
    ).toEqual(textSegments[4]._id);
  });

  it('Respects array limits', () => {
    let selectedTextSegment = textSegments[9];
    expect(
      getIdOfAdjacentTextSegmentWithActiveSuggestion(
        selectedTextSegment,
        textSegments,
        'forward',
      ),
    ).toEqual(defaultTextSegmentId);

    [selectedTextSegment] = textSegments;
    expect(
      getIdOfAdjacentTextSegmentWithActiveSuggestion(
        selectedTextSegment,
        textSegments,
        'backward',
      ),
    ).toEqual(defaultTextSegmentId);
  });

  it('Handles empty arrays', () => {
    const selectedTextSegment = textSegments[9];
    expect(
      getIdOfAdjacentTextSegmentWithActiveSuggestion(
        selectedTextSegment,
        [],
        'forward',
      ),
    ).toEqual(defaultTextSegmentId);
  });
});

describe(getHighlights, () => {
  test('One different word', () => {
    const output = getHighlights('I like beans.', 'I like pasta.');
    expect(output.fromHighlights).toEqual([
      {
        value: 'I like ',
        highlight: false,
      },
      {
        value: 'beans',
        highlight: true,
      },
      {
        value: '.',
        highlight: false,
      },
    ]);
    expect(output.toHighlights).toEqual([
      {
        value: 'I like ',
        highlight: false,
      },
      {
        value: 'pasta',
        highlight: true,
      },
      {
        value: '.',
        highlight: false,
      },
    ]);
  });

  test('Consecutive different words', () => {
    const { fromHighlights, toHighlights } = getHighlights(
      'I like white houses.',
      'I hate pink houses.',
    );
    console.log(fromHighlights);
    expect(fromHighlights).toEqual([
      {
        value: 'I ',
        highlight: false,
      },
      {
        value: 'like white',
        highlight: true,
      },
      {
        value: ' houses.',
        highlight: false,
      },
    ]);
    expect(toHighlights).toEqual([
      {
        value: 'I ',
        highlight: false,
      },
      {
        value: 'hate pink',
        highlight: true,
      },
      {
        value: ' houses.',
        highlight: false,
      },
    ]);
  });

  test('No changes', () => {
    const { fromHighlights, toHighlights } = getHighlights(
      'Mountains are inspiring!',
      'Mountains are inspiring!',
    );
    expect(fromHighlights).toEqual(toHighlights);
  });

  test('Empty from string', () => {
    const s = 'Are cyclists fast?';
    const { fromHighlights, toHighlights } = getHighlights('', s);
    expect(fromHighlights).toEqual([]);
    expect(toHighlights).toEqual([
      {
        value: s,
        highlight: true,
      },
    ]);
  });

  test('Empty to string', () => {
    const s = 'Are runners slow?';
    const { fromHighlights, toHighlights } = getHighlights(s, '');
    expect(toHighlights).toEqual([]);
    expect(fromHighlights).toEqual([
      {
        value: s,
        highlight: true,
      },
    ]);
  });

  function repeatWordWithWhitespace(word: string, num: number) {
    let res = '';
    for (let i = 0; i < num; i += 1) {
      res += word;
      if (i !== num - 1) {
        res += ' ';
      }
    }
    return res;
  }

  /**
   * @param len Number of segments
   * @param k Max number of words per segment
   */
  function getRandomTestCase(len: number, k: number) {
    const word1 = 'foo';
    const word2 = 'bar';
    const length = len;

    const changeWords = Array.from(Array(length).keys()).map(
      (x) => x % 2 === 0,
    );

    const numWords = Array.from(Array(length).keys()).map(
      () => Math.floor(Math.random() * k) + 1,
    );

    const targetFromHighlights: TextSegmentStructureElement[] = [];
    const targetToHighlights: TextSegmentStructureElement[] = [];
    let fromString = '';
    let toString = '';

    changeWords.forEach((change, i, arr) => {
      const num = numWords[i];

      const whitespace = change || i === arr.length - 1 ? '' : ' ';
      const whitespace2 = targetFromHighlights.slice(-1).pop()?.highlight
        ? ' '
        : '';
      const s1 = whitespace2 + repeatWordWithWhitespace(word1, num) + whitespace;
      const s2 = whitespace2 + repeatWordWithWhitespace(word2, num) + whitespace;

      targetFromHighlights.push({
        value: s1,
        highlight: change,
      });

      targetToHighlights.push({
        value: change ? s2 : s1,
        highlight: change,
      });

      fromString += s1;
      toString += change ? s2 : s1;
    });

    return {
      fromString,
      toString,
      targetFromHighlights,
      targetToHighlights,
    };
  }

  test('Random test', () => {
    for (let i = 1; i <= 100; i += 1) {
      const {
        fromString, toString, targetFromHighlights, targetToHighlights,
      } = getRandomTestCase(i, 10);
      const { fromHighlights, toHighlights } = getHighlights(
        fromString,
        toString,
      );
      expect(fromHighlights).toEqual(targetFromHighlights);
      expect(toHighlights).toEqual(targetToHighlights);
    }
  });
});
