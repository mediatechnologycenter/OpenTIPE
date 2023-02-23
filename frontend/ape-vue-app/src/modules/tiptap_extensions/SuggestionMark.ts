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
import TextSegmentMark from './TextSegmentMark';

const defaultId = '-1';
const idName = 'suggestionId';
const textSegmentIdName = TextSegmentMark.idName;
const defaultTextSegmentId = TextSegmentMark.defaultId;
const markName = 'suggestionMark';
const htmlTag = 'suggestion';

const SuggestionMark = Mark.create({
  name: markName,

  addOptions() {
    return {
      HTMLAttributes: {},
      clickEvent: null,
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
      [textSegmentIdName]: {
        default: defaultTextSegmentId,
        parseHTML: (element) => element.getAttribute(textSegmentIdName),
        renderHTML: (attributes) => ({
          [textSegmentIdName]: attributes[textSegmentIdName],
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
  Mark: SuggestionMark,
  name: markName,
};
