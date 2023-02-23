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
import * as clipboard from 'clipboard-polyfill';
import { Editor, JSONContent } from '@tiptap/core';
import { Selection } from 'prosemirror-state';
import { Node } from 'prosemirror-model';
import {
  splitStringIntoSentencesAndWhitespace,
  getDeepCopyOfObject,
  getLastElementInArray,
  stringContainsOnlyWhitespace,
} from './otherUtil';
import SuggestionMark from './tiptap_extensions/SuggestionMark';
import TextSegmentMark from './tiptap_extensions/TextSegmentMark';
import { defaultTextSegmentId, hasActiveSuggestion } from './suggestionUtil';

import {
  JSONContentStructure, Mark, TextSegment, Translatable,
} from './types';

/**
 * Get the ids of custom marks.
 * @param marks List of marks from an Tiptap editor content node
 */
function getTextSegmentIdFromMarks(marks: Mark[]): string | null {
  let textSegmentId: string | null = null;

  marks.forEach((m) => {
    textSegmentId = textSegmentId || m.attrs?.textSegmentId;
  });

  return textSegmentId;
}

/**
 * Merges successive text segments with the same id.
 */
function mergeTextSegmentsWithSameId(textSegments: Translatable[]) {
  const cleanedTextSegments: Translatable[] = [];

  let currentId: string;
  let currentText: string;

  textSegments.forEach((ts, i, arr) => {
    if (ts._id !== currentId) {
      // End chain and start new one
      if (currentText && currentId) {
        cleanedTextSegments.push({
          _id: currentId,
          srcText: currentText,
        });
      }

      currentId = ts._id;
      currentText = ts.srcText;
    } else {
      // Continue chain
      currentText = `${currentText}${ts.srcText}`;
    }

    if (arr.length === i + 1) {
      if (currentText) {
        cleanedTextSegments.push({
          _id: currentId,
          srcText: currentText,
        });
      }
    }
  });

  return cleanedTextSegments;
}

/**
 * Removes duplicate successive text nodes.
 */
function removeDuplicateTextNodes(content: JSONContentStructure[]) {
  const newContent: JSONContentStructure[] = [];
  let lastId: string | undefined;

  content.forEach((node) => {
    if (!node.textSegmentId || lastId !== node.textSegmentId) {
      newContent.push(node);
    }

    lastId = node.textSegmentId;
  });

  return newContent;
}

function requiresNewTextSegmentId(
  textSegmentId: string | null,
  parseHistory: string[],
) {
  return (
    // It currently doesn't have an id
    !textSegmentId
    // It does not continue a chain of text nodes with the same id
    || (getLastElementInArray(parseHistory) !== textSegmentId
      // The current id has been used before
      && parseHistory.includes(textSegmentId))
  );
}

interface IdReplacements {
  [key: string]: string;
}

function getTextSegmentIdFromMarksWithReplacement(
  marks: Mark[],
  idReplacements: IdReplacements,
) {
  let textSegmentId = getTextSegmentIdFromMarks(marks);

  if (!textSegmentId) {
    return null;
  }

  if (idReplacements[textSegmentId]) {
    textSegmentId = idReplacements[textSegmentId];
  }

  return textSegmentId;
}

function parseEditorContentInternal(
  contentNode: JSONContent,
  parseHistory: string[] = [],
  oldIdReplacements: IdReplacements = {},
) {
  const copiedContentNode = getDeepCopyOfObject(contentNode);
  const {
    type, attrs, content, text, marks,
  } = copiedContentNode;

  const structureProps = {
    type,
    attrs,
  };

  // Will contain all found text segments.
  const textSegments: Translatable[] = [];

  // Stores which text segment ids were already used.
  const localParseHistory: string[] = [];

  // Stores how text segment ids should be replaced. This is necessary if the user splits a text
  // segment. In that case, only the first part should keep the original id.
  let idReplacements = oldIdReplacements;

  // This will be added to the content of the parent node.
  const structures: JSONContentStructure[] = [];

  if (text !== undefined) {
    // Leaf node

    if (marks) {
      // TextSegment is already present

      let textSegmentId = getTextSegmentIdFromMarksWithReplacement(
        marks,
        idReplacements,
      );

      // Create new id if this one is already used. This can happen through user edits.
      if (
        !textSegmentId
        || requiresNewTextSegmentId(textSegmentId, parseHistory)
      ) {
        const newId = uuid();
        if (textSegmentId) {
          idReplacements[textSegmentId] = newId;
        }
        textSegmentId = newId;
      }

      textSegments.push({
        _id: textSegmentId,
        srcText: text,
      });

      structures.push({
        ...structureProps,
        textSegmentId,
      });

      localParseHistory.push(textSegmentId);
    } else {
      // Raw text. Text segments must be wrapped.

      const splitText = splitStringIntoSentencesAndWhitespace(text);

      splitText.forEach((str) => {
        if (stringContainsOnlyWhitespace(str)) {
          // Only whitespace means we save it in the structure, not in a textSegment.

          structures.push({
            ...structureProps,
            text: str,
          });
          localParseHistory.push('blank');
        } else {
          const textSegmentId = uuid();

          textSegments.push({
            _id: textSegmentId,
            srcText: str,
          });

          structures.push({
            ...structureProps,
            textSegmentId,
          });
          localParseHistory.push(textSegmentId);
        }
      });
    }
  } else if (!content) {
    // Leaf node without text (e.g., an empty paragraph).
    structures.push(copiedContentNode);
    localParseHistory.push('break');
  } else if (content !== undefined && content !== null) {
    // Not a leaf node.

    const structure = {
      ...structureProps,
      content,
    };

    const tempTextSegments: Translatable[] = [];
    const tempContent: JSONContentStructure[] = [];

    content.forEach((child) => {
      const {
        textSegments: childTextSegments,
        structures: childStructures,
        parseHistory: childParseHistory,
        idReplacements: childIdReplacements,
      } = parseEditorContentInternal(
        child,
        parseHistory.concat(localParseHistory),
        idReplacements,
      );

      idReplacements = childIdReplacements;
      tempContent.push(...childStructures);
      tempTextSegments.push(...childTextSegments);
      localParseHistory.push(...childParseHistory);
    });

    localParseHistory.push('break');

    // Clean the result
    textSegments.push(...mergeTextSegmentsWithSameId(tempTextSegments));
    structure.content = removeDuplicateTextNodes(tempContent);

    structures.push(structure);
  }

  return {
    textSegments,
    structures,
    parseHistory: localParseHistory,
    idReplacements,
  };
}

async function parseEditorContent(editorContent: JSONContent) {
  const { textSegments, structures } = parseEditorContentInternal(editorContent);
  return {
    textSegments,
    // Root is always just one node, which means the element at index 0 is always the document.
    structure: structures[0],
  };
}

function buildEditorContentWithMarksInternal(
  structure: JSONContentStructure,
  textSegments: TextSegment[],
  takeSource = false,
) {
  const copiedStructure = getDeepCopyOfObject(structure);
  const {
    type, attrs, content, textSegmentId, text,
  } = copiedStructure;

  const targetObjects = [];

  if (text !== undefined) {
    // E.g., a text node with whitespace (wouldn't be part of text segments)

    // Text nodes cannot be empty
    if (text) {
      // We can just copy it without changing it.
      targetObjects.push(copiedStructure);
    }
  } else if (textSegmentId !== undefined) {
    // It must be a leaf node, since it contains text.

    const textSegment = textSegments.find((ts) => ts._id === textSegmentId);

    if (!textSegment) {
      throw new Error(
        `Cannot build editor content because the text segment with the following id cannot be found: ${textSegmentId}.`,
      );
    }

    /**
     * Wrapping the text segments with the appropriate marks.
     */

    // This will always be added to every part of the text fragment.
    const textSegmentMark = {
      type: TextSegmentMark.name,
      attrs: {
        [TextSegmentMark.idName]: textSegment._id,
        hasSuggestion: textSegment.suggestionIsActive,
      },
    };

    // This will only be added to parts of the text fragment with an active suggestion.
    const suggestionMark = {
      type: SuggestionMark.name,
      attrs: {
        [TextSegmentMark.idName]: textSegment._id,
      },
    };

    const textSegmentRegions: any[] = [];

    if (hasActiveSuggestion(textSegment)) {
      // Highlight all parts of the text with changes
      if (takeSource) {
        textSegmentRegions.push({
          type: 'text',
          text: textSegment.srcText,
          marks: [textSegmentMark, suggestionMark],
        });
      } else {
        const segments = textSegment.mtTextStructure;
        segments.forEach((s) => {
          textSegmentRegions.push({
            type: 'text',
            text: s.value,
            marks: s.highlight
              ? [textSegmentMark, suggestionMark]
              : [textSegmentMark],
          });
        });
      }
    } else {
      const textSegmentWithMarks = {
        type: 'text',
        text: takeSource ? textSegment.srcText : textSegment.hpeText,
        marks: [textSegmentMark],
      };
      textSegmentRegions.push(textSegmentWithMarks);
    }

    // Text nodes cannot be empty.
    targetObjects.push(...textSegmentRegions.filter((x) => x.text !== ''));
  } else if (content !== undefined && content !== null) {
    // It's not a leaf node. Therefore, it has children.

    let newContent: JSONContent[] = [];

    // Recursively building the editor content.
    content.forEach((element) => {
      const childTargetObjects = buildEditorContentWithMarksInternal(
        element,
        textSegments,
        takeSource,
      );
      newContent = newContent.concat(childTargetObjects);
    });

    const targetObj = {
      // Adding type and attrs if they exist
      type,
      attrs,
      content: newContent,
    };

    targetObjects.push(targetObj);
  } else {
    // It's a child but without text. This could be an empty paragraph, for example.

    // Adding type and attrs if they exist, but no content or text.
    const emptyElement = {
      type,
      attrs,
    };

    targetObjects.push(emptyElement);
  }

  // There is only one root node in the editor content. Therefore, we can return that node directly
  // if the current node is the root node.
  return targetObjects;
}

function buildEditorContentWithMarks(
  structure: JSONContentStructure,
  textSegments: TextSegment[],
  takeSource = false,
) {
  return buildEditorContentWithMarksInternal(
    structure,
    textSegments,
    takeSource,
  )[0];
}

/**
 * @param selection Selection object of Tiptap editor
 * @param doc Document object of Tiptap editor
 * @returns Ids of currently selected text segments
 */
function getIdsOfSelectedTextSegments(selection: Selection, doc: Node) {
  const { from, to } = selection;
  const selectedTextSegmentIds: string[] = [];
  doc.descendants((node, pos) => {
    // +1 and -1 are necessary because nodes have start and end markers.
    // We don't care about those markers
    const startPos = pos + 1;
    const endPos = pos + node.nodeSize - 1;

    // True if any part of the text segment is part of the selection.
    const isInSelection = from <= endPos && startPos <= to && from !== to;
    if (!isInSelection) return;

    const { marks } = node;

    // E.g., whitespace nodes.
    if (!marks) return;

    let textSegmentId: string | null = null;

    marks.forEach((m) => {
      textSegmentId = textSegmentId || m.attrs.textSegmentId;
    });

    // Doesn't have an id (i.e., is not a text segment)
    if (!textSegmentId) return;

    // Already found that text segment
    if (selectedTextSegmentIds.includes(textSegmentId)) return;

    selectedTextSegmentIds.push(textSegmentId);
  });
  return selectedTextSegmentIds;
}

/**
 * @param editor The Tiptap editor in which text segments are selected
 * @param textSegments An array of text segments.
 * @returns The currently selected text segments.
 */
function getSelectedTextSegments(editor: Editor, textSegments: TextSegment[]) {
  const ids = getIdsOfSelectedTextSegments(
    editor.state.selection,
    editor.state.doc,
  );
  return textSegments.filter((ts) => ids.includes(ts._id));
}

/**
 * Copy the entire text of an editor to the clipboard.
 * @param editor The editor to copy the text from
 */
async function copyEditorContentAsText(editor: Editor) {
  const item = new clipboard.ClipboardItem({
    'text/html': new Blob([editor.getHTML()], { type: 'text/html' }),
    'text/plain': new Blob([editor.state.doc.textContent], {
      type: 'text/plain',
    }),
  });

  await clipboard.write([item]);
}

function selectionIsEmpty(editor: Editor) {
  return editor.state.selection.from === editor.state.selection.to;
}

function cursorIsAtDocumentLocation(editor: Editor, location: 'start' | 'end') {
  const { from, to } = editor.state.selection;
  if (location === 'start') {
    const targetPos = 1;
    const minPos = Math.max(from, to);
    return minPos <= targetPos;
  }
  const targetPos = editor.state.doc.content.size - 1;
  const maxPos = Math.max(from, to);
  return targetPos <= maxPos;
}

/**
 * Gets the textSegmentId of one currently selected mark (the caret location) in the passed editor.
 */
function getTextSegmentIdOfSelectedMarks(editor: Editor) {
  let textSegmentId: string | null = null;

  // We don't want the last node to be selected if the user clicks anywhere below the text.
  if (
    !editor.state.selection.empty
    || (selectionIsEmpty(editor)
      && (cursorIsAtDocumentLocation(editor, 'start')
        || cursorIsAtDocumentLocation(editor, 'end')))
  ) {
    textSegmentId = defaultTextSegmentId;
  }

  const pos = editor.state.selection.$head;
  const closeNode = pos.nodeAfter || pos.nodeBefore;

  // No actual content near the selection (e.g., in an empty document or in a new paragraph).
  if (!closeNode) return null;

  const { marks } = closeNode;

  // Not a custom mark.
  if (!marks) return null;

  marks.forEach((m) => {
    // We can do this because our nested custom marks always have the same textSegmentId.
    textSegmentId = textSegmentId || m.attrs.textSegmentId;
  });

  return textSegmentId;
}

export {
  parseEditorContent,
  buildEditorContentWithMarks,
  getSelectedTextSegments,
  copyEditorContentAsText,
  getTextSegmentIdOfSelectedMarks,
};
