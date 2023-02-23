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
import { Mark, mergeAttributes } from '@tiptap/core';

const defaultId = '-1';
const idName = 'textSegmentId';
const markName = 'textSegmentMark';
const htmlTag = 'text-segment';

const TextSegmentMark = Mark.create({
  name: markName,

  /**
   * Means that the text segment will wrap the suggestion if, e.g., the entire
   * text segment is a suggestion:
   *
   * <text-segment> ... <suggestion> ... </suggestion> ... </text-segment>
   * instead of
   * <suggestion> ... <text-segment> ... </text-segment> ... </suggestion>
   *
   */
  priority: 1000,

  addOptions() {
    return {
      HTMLAttributes: {},
      [idName]: defaultId,
      hasSuggestion: false,
    };
  },

  addAttributes() {
    return {
      [idName]: {
        default: defaultId,
        parseHTML: (element) => element.getAttribute(idName),
        renderHTML: (attributes) => ({
          [idName]: attributes[idName],
        }),
      },
      hasSuggestion: {
        default: defaultId,
        renderHTML: (attributes) => ({
          hasSuggestion: attributes.hasSuggestion,
        }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: htmlTag,
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      htmlTag,
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes),
      0,
    ];
  },
});

export default {
  Mark: TextSegmentMark,
  name: markName,
  tag: htmlTag,
  idName,
  defaultId,
};
