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
import {
  getDeepCopyOfObject,
  posMod,
  removeTrailingWhitespace,
  splitStringIntoSentencesAndWhitespace,
  stringContainsOnlyWhitespace,
} from '@/modules/otherUtil';

describe(splitStringIntoSentencesAndWhitespace, () => {
  it('Handles empty strings', () => {
    expect(splitStringIntoSentencesAndWhitespace('')).toEqual([]);
  });
  it('Handles single sentences', () => {
    const sentences = [
      'hello',
      'Habitant litora consequat scelerisque proin quam nisl velit libero, blandit eget urna nec sagittis quis habitasse, tempus tristique torquent sapien vivamus at viverra.',
      'Noch ein Satz!',
    ];

    sentences.forEach((s) => {
      expect(splitStringIntoSentencesAndWhitespace(s)).toEqual([s]);
    });
  });
  it('Handles whitespace without sentences', () => {
    const strings = ['    ', ' ', ' \n \r '];

    strings.forEach((s) => {
      expect(splitStringIntoSentencesAndWhitespace(s)).toEqual([s]);
    });
  });
  it('Handles parentheses and quotes', () => {
    const stringsSegments = [
      ['(Apple juice!).', ' '],
      ['My people need me!?!?!?!))]]}}}]', ' '],
      ['"Hello!)[])]]}}}]"', ' '],
      ['"Bye"!)[])]]}}}]', ' '],
    ];

    stringsSegments.forEach((segments) => {
      const inputString = segments.join('');
      expect(splitStringIntoSentencesAndWhitespace(inputString)).toEqual(
        segments,
      );
    });
  });
  it('Handles multiple sentences', () => {
    const stringsSegments = [
      ['Sentence 1.', ' ', 'Sentence 2?!!', '           ', '(Sentence 3.).'],
    ];

    stringsSegments.forEach((segments) => {
      const inputString = segments.join('');
      expect(splitStringIntoSentencesAndWhitespace(inputString)).toEqual(
        segments,
      );
    });
  });
});

describe(removeTrailingWhitespace, () => {
  it('Handles empty strings', () => {
    expect(removeTrailingWhitespace('')).toEqual('');
  });

  it('Handles non-empty strings with trailing whitespace', () => {
    const nonWhitespace = 'Hello this is a test.';
    expect(removeTrailingWhitespace(`${nonWhitespace}           `)).toEqual(
      nonWhitespace,
    );
  });

  it('Handles non-empty strings without trailing whitespace', () => {
    const nonWhitespace = 'Hello this is another test.';
    expect(removeTrailingWhitespace(`${nonWhitespace}`)).toEqual(nonWhitespace);
  });
});

describe(stringContainsOnlyWhitespace, () => {
  test('String with only whitespace', () => {
    expect(
      stringContainsOnlyWhitespace('  \n \r                  '),
    ).toBeTruthy();
    expect(stringContainsOnlyWhitespace(' ')).toBeTruthy();
  });

  test('Empty string', () => {
    expect(stringContainsOnlyWhitespace('')).toBeTruthy();
  });

  test('Non-whitespace string', () => {
    expect(
      stringContainsOnlyWhitespace(
        '  some  whitespace but not only whitespace    \n',
      ),
    ).toBeFalsy();
  });
});

describe(getDeepCopyOfObject, () => {
  it('Handles null', () => {
    expect(getDeepCopyOfObject(null)).toBeNull();
  });

  it('Handles non-null objects', () => {
    const src = {
      a: 'hello',
      b: 12,
      c: ['x'],
    };
    expect(getDeepCopyOfObject(src)).not.toBe(src);
  });
});

describe(posMod, () => {
  const tests = [
    [5, 22, 5],
    [25, 22, 3],
    [-1, 22, 21],
    [-2, 22, 20],
    [10, 3, 1],
    [10, -3, 1],
    [-13, 64, 51],
  ];

  tests.forEach((t) => {
    expect(posMod(t[0], t[1])).toEqual(t[2]);
  });
});
