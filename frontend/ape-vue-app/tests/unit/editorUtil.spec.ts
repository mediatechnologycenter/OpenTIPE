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

import * as uuid from 'uuid';
import { parseEditorContent } from '@/modules/editorUtil';
import { Translatable } from '@/modules/types';

function idsAreUnique(arr: Translatable[]) {
  return (
    arr
      // For all text segments, check if they're the only text segment with their id in the array.
      .map((x) => arr.filter((y) => x._id === y._id).length === 1)
      // 'And' all of the entries.
      .reduce((x, y) => x && y)
  );
}

// changes the textSegmentId property to true if it's a valid id.
function checkTextSegmentIds(x: any) {
  if (x.textSegmentId) {
    // eslint-disable-next-line no-param-reassign
    x.textSegmentId = uuid.validate(x.textSegmentId);
  }
  if (x.content) {
    x.content.forEach((y: any) => {
      checkTextSegmentIds(y);
    });
  }
  return x;
}

describe(parseEditorContent, () => {
  it('Handles a single sentence', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              text: 'Single sentence.',
            },
          ],
        },
      ],
    };

    const { textSegments, structure } = await parseEditorContent(content);
    const anyStructure = structure as any;

    expect(textSegments.length).toEqual(1);
    expect(textSegments[0].srcText).toEqual('Single sentence.');

    expect(structure.content).toBeDefined();
    expect(anyStructure.content[0].content[0].textSegmentId).toBeDefined();
  });

  it('Handles multiple sentences in one node', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              text: 'Sentence 1. Sentence 2.',
            },
          ],
        },
      ],
    };

    // eslint-disable-next-line no-unused-vars
    const targetStructure = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              textSegmentId: true,
            },
            {
              type: 'text',
              text: ' ',
            },
            {
              type: 'text',
              textSegmentId: true,
            },
          ],
        },
      ],
    };

    const { textSegments, structure } = await parseEditorContent(content);
    expect(textSegments.length).toEqual(2);
    expect(textSegments.filter((e) => e.srcText === 'Sentence 1.').length).toBe(
      1,
    );
    expect(textSegments.filter((e) => e.srcText === 'Sentence 2.').length).toBe(
      1,
    );
    // Check that ids are unique.
    expect(idsAreUnique(textSegments)).toBeTruthy();
    expect(checkTextSegmentIds(structure)).toEqual(targetStructure);
  });

  it('Handles sentences in multiple nodes', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              text: 'Sentence 1. Sentence 2.',
            },
          ],
        },
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              text: 'Sentence 3. Sentence 4.',
            },
          ],
        },
      ],
    };

    const { textSegments } = await parseEditorContent(content);
    expect(textSegments.length).toEqual(4);

    // Each sentence is in its own text segment
    for (let i = 1; i <= 4; i += 1) {
      expect(
        textSegments.filter((e) => e.srcText === `Sentence ${i}.`).length,
      ).toBe(1);
    }

    expect(idsAreUnique(textSegments)).toBeTruthy();
  });

  it('Handles existing text segments', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
                {
                  type: 'suggestionMark',
                  attrs: {
                    suggestionId: '-1',
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
              ],
              text: 'Sentence 1.',
            },
            {
              type: 'text',
              text: ' ',
            },
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: '77a14b95-89ed-420f-9927-c22e0e4407b6',
                  },
                },
                {
                  type: 'suggestionMark',
                  attrs: {
                    suggestionId: '-1',
                    textSegmentId: '77a14b95-89ed-420f-9927-c22e0e4407b6',
                  },
                },
              ],
              text: 'Sentence 2.',
            },
          ],
        },
      ],
    };

    const targetStructure = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
            },
            {
              type: 'text',
              text: ' ',
            },
            {
              type: 'text',
              textSegmentId: '77a14b95-89ed-420f-9927-c22e0e4407b6',
            },
          ],
        },
      ],
    };

    const targetTextSegments: Translatable[] = [
      {
        _id: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
        srcText: 'Sentence 1.',
      },
      {
        _id: '77a14b95-89ed-420f-9927-c22e0e4407b6',
        srcText: 'Sentence 2.',
      },
    ];

    const { textSegments, structure } = await parseEditorContent(content);
    expect(textSegments.length).toEqual(2);
    expect(textSegments).toEqual(targetTextSegments);
    expect(structure).toEqual(targetStructure);
  });

  /**
   * If the user presses enter in the translated text editor, the part of the text segment before
   * the caret should continue to have the same text segment id. The part of the text segment after
   * the caret should be treated as a new text segment with a new id.
   */
  it('Handles separated text segments with same id', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: 'b8418d2d-3491-489d-93ef-adf7d1fc06ff',
                  },
                },
              ],
              text: 'First part of the sentence',
            },
          ],
        },
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: 'b8418d2d-3491-489d-93ef-adf7d1fc06ff',
                  },
                },
              ],
              text: ' Second part of the sentence.',
            },
          ],
        },
      ],
    };
    const { textSegments, structure } = await parseEditorContent(content);
    const anyStructure = structure as any;

    // Text segments

    // Finds two text segments
    expect(textSegments[0].srcText).toEqual('First part of the sentence');
    expect(textSegments[1].srcText).toEqual(' Second part of the sentence.');

    // Both have a different id
    expect(idsAreUnique(textSegments)).toBeTruthy();

    // Structure

    // Part before the caret still has the same id
    expect(anyStructure.content[0].content[0].textSegmentId).toBe(
      'b8418d2d-3491-489d-93ef-adf7d1fc06ff',
    );
    // Part after the caret has a new id
    expect(anyStructure.content[1].content[0].textSegmentId).not.toBe(
      'b8418d2d-3491-489d-93ef-adf7d1fc06ff',
    );
    // All ids are valid
    expect(
      uuid.validate(anyStructure.content[1].content[0].textSegmentId),
    ).toBeTruthy();
  });

  /**
   * A text segment in which not everything is a suggestion is parsed as a single text
   * segment, not as multiple ones.
   */
  it('Handles dissected text segments', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
              ],
              text: 'This ',
            },
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
                {
                  type: 'suggestionMark',
                  attrs: {
                    suggestionId: '-1',
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
              ],
              text: 'can',
            },
            {
              type: 'text',
              marks: [
                {
                  type: 'textSegmentMark',
                  attrs: {
                    textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
                  },
                },
              ],
              text: ' happen.',
            },
          ],
        },
      ],
    };

    const { textSegments, structure } = await parseEditorContent(content);
    expect(textSegments).toEqual([
      {
        srcText: 'This can happen.',
        _id: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
      },
    ]);
    expect(textSegments.length).toEqual(1);
    expect(structure).toEqual({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'text',
              textSegmentId: '49c9f4eb-5801-4c01-a99d-af5c1c8d19da',
            },
          ],
        },
      ],
    });
  });

  it('Handles an empty document', async () => {
    const content = {
      type: 'doc',
      content: [
        {
          type: 'paragraph',
        },
      ],
    };

    const { textSegments, structure } = await parseEditorContent(content);
    expect(textSegments).toEqual([]);
    expect(structure).toEqual(structure);
  });
});
