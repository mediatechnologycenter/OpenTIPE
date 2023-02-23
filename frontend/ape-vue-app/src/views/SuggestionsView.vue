<!-- Copyright 2022 ETH Zurich, Media Technology Center

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->
<template>
  <div
    class="
      h-full
      w-full
      fixed
      bg-gradient-to-bl
      from-gray-100
      to-gray-200
      flex flex-grow-0 flex-col
      space-y-4
      p-4
    "
  >
    <!-- Control bar at the top -->
    <div
      class="
        flex
        justify-between
        transition-all
        rounded-md
        flex-shrink
        pointer-events-none
      "
      style="z-index: 100000"
    >
      <!-- Left aligned buttons -->
      <div class="flex justify-start space-x-5 pointer-events-auto">

        <!-- Back button -->
        <base-button
          class="flex-grow-0 flex-shrink-0"
          title="Translate another text"
          type="secondary"
          @click="goToStageOne"
        >
          <template v-slot:icon>
            <arrow-left-icon class="w-5 h-5 text-white"></arrow-left-icon>
          </template>
        </base-button>
      </div>

      <!-- Right aligned buttons -->
      <div class="flex justify-start space-x-5 pointer-events-auto mr-96">
        <!-- History buttons -->
        <div class="flex space-x-1">
          <!-- Undo button -->
          <base-button
            title=""
            type="secondary"
            @click="undo"
            :disabled="!undoIsPossible"
            description="Undo changes"
          >
            <template v-slot:icon>
              <back-icon></back-icon>
            </template>
          </base-button>

          <!-- Redo button -->
          <base-button
            title=""
            type="secondary"
            @click="redo"
            :disabled="!redoIsPossible"
            description="Redo changes"
          >
            <template v-slot:icon>
              <forward-icon></forward-icon>
            </template>
          </base-button>
        </div>

        <!-- Copy button -->
        <base-button
          title="Copy translated text"
          @click="copyTranslatedText"
          class="flex-none"
        >
          <template v-slot:icon>
            <clipboard-copy-icon class="w-5 h-5"></clipboard-copy-icon>
          </template>
        </base-button>
      </div>
    </div>

    <!-- Three columns -->
    <div class="w-full h-full flex-grow-0 flex space-x-2 min-h-0">

      <!-- src text -->
      <div class="flex-1 overflow-hidden -m-2 p-2">
        <base-card class="h-full text-gray-700">
          <tiptap
            v-model="editorContentUntranslated"
            :editable="false"
            :enableHighlight="true"
            @markClick="handleMarkClick"
            :selectedTextSegmentId="selectedTextSegmentId"
            class="h-full"
          />
        </base-card>
      </div>

      <!-- mt text -->
      <div class="flex-1 overflow-hidden -m-2 p-2">
        <base-card class="h-full">
          <tiptap
            v-model="editorContentTranslated"
            :enableSpellcheck="enableSpellcheck"
            :enableHistory="false"
            :enableHighlight="true"
            @userEdit="handleUserEdit"
            @newEditor="registerNewTranslatedTextEditor"
            @copy="handleTranslatedTextCopy()"
            @markClick="handleMarkClick"
            :selectedTextSegmentId="selectedTextSegmentId"
            class="h-full"
          />
        </base-card>
      </div>

      <!-- Right column (the suggestions) -->
      <div
        class="flex-grow-0 flex flex-col space-y-4 -mb-4"
        style="margin-top: -72px"
      >

        <!-- Message for when there are no suggestions -->
        <div
          v-if="!textSegmentsWithActiveSuggestion.length"
          class="h-full w-full flex justify-center items-center"
        >
          <div class="w-96 -mx-2 flex flex-col items-center">
            <h3 class="font-bold text-2xl text-gray-400">Looks good!</h3>
            <p class="text-gray-400">There are no suggestions available.</p>
          </div>
        </div>

        <!-- Available suggestions -->
        <div
          v-else
          class="overflow-y-auto h-full space-y-4 -mx-2 px-2 pb-96 w-96"
          style="padding-top: 72px"
        >
          <!-- About the z-index: Each suggestion-card has an artificially increased height
          to properly align the card when using the auto-scroll library. This increased height
          means that the cards overlap, which prevents clicking on them. With custom z-values,
          the invisible element that creates the artificial height is *behind* the card above.
          This way, the card above is still clickable.-->
          <suggestion-card
            v-for="(ts, i) in textSegmentsWithActiveSuggestion"
            :key="ts._id"
            :textSegment="ts"
            :selectedTextSegmentId="selectedTextSegmentId"
            :isFirstSuggestion="
              ts._id === idOfFirstTextSegmentWithActiveSuggestion
            "
            :isLastSuggestion="
              ts._id === idOfLastTextSegmentWithActiveSuggestion
            "
            :style="`z-index: ${10000 - i}`"
            @newFocus="setNewTextSegmentSelection"
            @apply="applySuggestionButtonClicked(ts)"
            @discard="discardSuggestionButtonClicked(ts)"
            @previous="selectPreviousTextSegmentWithActiveSuggestion(ts)"
            @next="selectNextTextSegmentWithActiveSuggestion(ts)"
          ></suggestion-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {
  computed, defineComponent, onBeforeUnmount, ref, toRefs, watch, watchEffect,
} from 'vue';
import { useRouter } from 'vue-router';
import { ArrowLeftIcon, ClipboardCopyIcon } from '@heroicons/vue/solid';

import { JSONContent } from '@tiptap/core';
import { Editor } from '@tiptap/vue-3';
import { error as printError, warn } from 'loglevel';
import {
  buildEditorContentWithMarks,
  copyEditorContentAsText,
  getSelectedTextSegments,
  parseEditorContent,
} from '@/modules/editorUtil';
import {
  defaultTextSegmentId,
  getCleanId,
  getIdOfAdjacentTextSegmentWithActiveSuggestion,
  getTextSegmentsWithActiveSuggestion,
} from '@/modules/suggestionUtil';
import HistoryManager from '../modules/HistoryManager';

import BaseButton from '../components/UI/BaseButton.vue';
import BaseCard from '../components/UI/BaseCard.vue';
import Tiptap from '../components/editor/Tiptap.vue';
import SuggestionCard from '../components/suggestions_view/SuggestionCard.vue';
import BackIcon from '../components/custom_icons/BackIcon.vue';
import ForwardIcon from '../components/custom_icons/ForwardIcon.vue';
import { NotificationMessageType, StoreState, TextSegment } from '@/modules/types';
import { scrollToElementsWithClass } from '@/modules/scrollUtil';
import { sendPostEditData } from '@/modules/serverUtil';
import { getLanguagePairKey } from '@/modules/otherUtil';
import options from '@/modules/options';
import { useNotifier, useStore } from '@/modules/injectUtil';
import { EventLogger, EventLogType } from '@/modules/eventLogger';

export default defineComponent({
  components: {
    BaseButton,
    BaseCard,
    ArrowLeftIcon,
    ClipboardCopyIcon,
    Tiptap,
    SuggestionCard,
    BackIcon,
    ForwardIcon,
  },
  mounted() {
    EventLogger.idleTimer.registerEventListeners();
  },
  unmounted() {
    EventLogger.idleTimer.removeEventListeners();
  },
  setup() {
    const router = useRouter();
    const notifier = useNotifier();
    const {
      state,
      methods,
    } = useStore();

    const {
      augmentedStructure,
      augmentedTextSegments,
      originalStructure,
    } = toRefs(state);
    const {
      applySuggestion,
      discardSuggestion,
      applyEdits,
      replaceState,
      updateState,
    } = methods;

    /**
     * TEXT SEGMENT SELECTION ----------------------------------------------------------------------
     */

    const textSegmentsWithActiveSuggestion = computed(
      () => getTextSegmentsWithActiveSuggestion(augmentedTextSegments.value || []),
    );
    const idOfFirstTextSegmentWithActiveSuggestion = computed(
      () => getCleanId(textSegmentsWithActiveSuggestion.value[0]?._id),
    );
    const idOfLastTextSegmentWithActiveSuggestion = computed(
      () => getCleanId(textSegmentsWithActiveSuggestion.value.slice(-1)[0]?._id),
    );

    const selectedTextSegmentId = ref(defaultTextSegmentId);

    /**
     * @param id The newly selected id
     * @param delay Delay in ms after which the new id should be selected
     */
    function setNewTextSegmentSelection(id: string | null, delay = 0) {
      if (selectedTextSegmentId.value === id) return;
      if (id === null) {
        setNewTextSegmentSelection(defaultTextSegmentId, delay);
        return;
      }
      // Timeout (delay) is necessary if this is triggered by a button press. If no timeout was specified,
      // The focus would immediately be set back to the item in which the button was clicked.
      setTimeout(() => {
        selectedTextSegmentId.value = id;
      }, delay);
    }

    function handleMarkClick(textSegmentId: string) {
      try {
        if (textSegmentId) {
          setNewTextSegmentSelection(textSegmentId);
        }
      } catch (error: any) {
        notifier.notify(`Action failed: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    /**
     * EDITOR --------------------------------------------------------------------------------------
     */

    let translatedTextEditor: Editor | null = null;

    // This method will be called once the Tiptap component has created the editor object.
    function registerNewTranslatedTextEditor(e: Editor) {
      translatedTextEditor = e;
    }

    // The Tiptap editor uses these objects to know what to display.
    // It's a two-way binding. If user makes edits, these objects will reflect that.
    const editorContentUntranslated = ref<JSONContent>({
      type: 'doc',
    });
    const editorContentTranslated = ref<JSONContent>({
      type: 'doc',
    });

    // Update editor contents if the underlying data changes.
    // Data change --> Editor content change
    watchEffect(() => {
      try {
        if (
          !originalStructure.value
          || !augmentedTextSegments.value
          || !augmentedStructure.value
        ) {
          throw new Error(
            'Original structure or augmentedTextSegments or augmentedStructure is not available.',
          );
        }

        // Only the highlighting will change. The structure and the actual content always
        // stay the same here.
        editorContentUntranslated.value = buildEditorContentWithMarks(
          originalStructure.value,
          augmentedTextSegments.value,
          true,
        );

        // Structure, content, and highlights can change here.
        editorContentTranslated.value = buildEditorContentWithMarks(
          augmentedStructure.value,
          augmentedTextSegments.value,
        );
      } catch (error: any) {
        notifier.notify(error.message, {
          messageType: NotificationMessageType.error,
        });
      }
    });

    // Update the application data if the editor content changes
    // Editor content change --> Data change
    let lastUserEditTime = -1;

    async function handleUserEdit(delay = 750) {
      const thisUserEditTime = Date.now();
      lastUserEditTime = thisUserEditTime;

      try {
        const {
          textSegments,
          structure,
        } = await parseEditorContent(
          editorContentTranslated.value,
        );

        // For performance reasons, only update the application data once the user has stopped
        // making changes.
        setTimeout(async () => {
          try {
            if (thisUserEditTime !== lastUserEditTime) {
              // There has been a new user edit in the meantime.
              return;
            }

            await applyEdits(textSegments);
            updateState({
              augmentedStructure: structure,
            });
          } catch (error: any) {
            notifier.notify(`Edits could not be applied: ${error.message}`, {
              messageType: NotificationMessageType.error,
            });
          }
        }, delay);
      } catch (error: any) {
        notifier.notify(
          `Editor content could not be parsed: ${error.message}`,
          { messageType: NotificationMessageType.error },
        );
      }
    }

    /**
     * HANDLE COPY ---------------------------------------------------------------------------------
     */

    async function handleTranslatedTextCopy() {
      if (!translatedTextEditor) {
        throw new Error('Editor for translated text does not exist.');
      }

      if (augmentedTextSegments.value === null) {
        throw new Error(
          'Cannot copy text because augmentedTextSegments is null',
        );
      }

      let textSegmentsToSend: TextSegment[];

      if (options.saveAllTextSegments) {
        textSegmentsToSend = augmentedTextSegments.value;
      } else {
        textSegmentsToSend = getSelectedTextSegments(
          translatedTextEditor,
          augmentedTextSegments.value,
        );
      }

      const langPairKey = getLanguagePairKey(state.srcLang, state.trgLang);

      if (options.useFakeApi) {
        console.debug('Skipped sending post edit data to API because fake api is used');
      } else {
        await sendPostEditData(
          textSegmentsToSend,
          state.srcLang,
          state.trgLang,
          state.translationSessionId,
          state.user,
          state.dictionaries[langPairKey].selectedDicts,
          state.dictionaries[langPairKey].userDictJSON,
        );
      }

      EventLogger.log(EventLogType.CopyEvent);
    }

    async function copyTranslatedText() {
      try {
        if (translatedTextEditor === null) {
          throw new Error(
            'Cannot copy translated text because the editor is missing.',
          );
        }

        // Put all currently displayed translated text into clipboard
        await copyEditorContentAsText(translatedTextEditor);

        // Select entire editor content
        translatedTextEditor.commands.selectAll();

        // Send edits to backend
        try {
          await handleTranslatedTextCopy();
        } catch (error) {
          // Notifying the user of errors here is unnecessary because the outcome of this function does
          // not influence the user. It is only for sending the edits to the backend.
          warn('Sending edits to server failed');
          printError(error);
        }

        // Clear selection
        translatedTextEditor.commands.setTextSelection(0);

        notifier.notify('Successfully copied the text!', {
          automaticallyDismissAfter: 3000,
          messageType: NotificationMessageType.success,
        });
      } catch (error: any) {
        notifier.notify(`Failed to copy text: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    /**
     * HISTORY -------------------------------------------------------------------------------------
     */

    const maxHistoryLength = 100;
    const historyManager = new HistoryManager<StoreState>(maxHistoryLength);
    historyManager.addToHistory(state);

    // Enables/disables the history buttons
    const undoIsPossible = ref(false);
    const redoIsPossible = ref(false);

    // Whenever the state changes, we add the new state to the history.
    watch(
      state,
      (s) => {
        if (!s.isInTransaction) {
          historyManager.addToHistory(s);
          undoIsPossible.value = historyManager.canGoBack();
          redoIsPossible.value = historyManager.canGoForward();
        }
      },
      { deep: true },
    );

    function undo() {
      const { user } = state;

      try {
        if (historyManager.goBack()) {
          const newState = historyManager.getState();
          if (newState) {
            newState.user = user;
            replaceState(newState);
            setNewTextSegmentSelection(null);
            EventLogger.log(EventLogType.UndoEvent);
          }
        }
      } catch (error: any) {
        notifier.notify(`Failed to undo: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    function redo() {
      const { user } = state;

      try {
        if (historyManager.goForward()) {
          const newState = historyManager.getState();
          if (newState) {
            newState.user = user;
            replaceState(newState);
            setNewTextSegmentSelection(null);
            EventLogger.log(EventLogType.RedoEvent);
          }
        }
      } catch (error: any) {
        notifier.notify(`Failed to redo: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    function processHistoryEventsInKeyboardEvent(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.code === 'KeyZ') {
        if (event.shiftKey) {
          redo();
        } else {
          undo();
        }
      }
    }

    /**
     * SUGGESTION ACTIONS --------------------------------------------------------------------------
     */

    /**
     * @param textSegment The currently selected textSegment
     */
    function selectPreviousTextSegmentWithActiveSuggestion(
      textSegment: TextSegment,
    ) {
      if (!augmentedTextSegments.value) {
        return;
      }
      const id = getIdOfAdjacentTextSegmentWithActiveSuggestion(
        textSegment,
        augmentedTextSegments.value,
        'backward',
      );
      setNewTextSegmentSelection(id, 20);
    }

    /**
     * @param textSegment The currently selected textSegment
     */
    function selectNextTextSegmentWithActiveSuggestion(
      textSegment: TextSegment,
    ) {
      if (!augmentedTextSegments.value) {
        return;
      }
      const id = getIdOfAdjacentTextSegmentWithActiveSuggestion(
        textSegment,
        augmentedTextSegments.value,
        'forward',
      );
      setNewTextSegmentSelection(id, 20);
    }

    async function applySuggestionButtonClicked(textSegment: TextSegment) {
      try {
        await applySuggestion(textSegment);
        selectNextTextSegmentWithActiveSuggestion(textSegment);
        EventLogger.log(EventLogType.AcceptEvent);
      } catch (error: any) {
        notifier.notify(`Action failed: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    async function discardSuggestionButtonClicked(textSegment: TextSegment) {
      try {
        await discardSuggestion(textSegment);
        selectNextTextSegmentWithActiveSuggestion(textSegment);
        EventLogger.log(EventLogType.RejectEvent);
      } catch (error: any) {
        notifier.notify(`Action failed: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    /**
     * MISC ----------------------------------------------------------------------------------------
     */

    function goToStageOne() {
      router.push({
        name: 'StartView',
      });
    }

    function processSaveEventInKeyboardEvent(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.code === 'KeyS') {
        event.preventDefault();
        notifier.notify('Your progress is saved automatically!', {
          messageType: NotificationMessageType.success,
          automaticallyDismissAfter: 3000,
        });
      }
    }

    function handleKeyPress(event: KeyboardEvent) {
      try {
        processHistoryEventsInKeyboardEvent(event);
        processSaveEventInKeyboardEvent(event);
      } catch (error: any) {
        notifier.notify(`Keyboard shortcut failed: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    document.addEventListener('keydown', handleKeyPress);
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleKeyPress);
    });

    // Automatically scroll to selected elements once the text segment selection changes
    watch(selectedTextSegmentId, () => {
      try {
        setTimeout(() => {
          scrollToElementsWithClass('selected');
        }, 50);
      } catch (error) {
        // Notifying the user is not helpful here.
        warn('Automatic scrolling failed', error);
      }
    });

    return {
      handleMarkClick,
      undoIsPossible,
      redoIsPossible,
      goToStageOne,
      undo,
      redo,
      applySuggestionButtonClicked,
      discardSuggestionButtonClicked,
      editorContentUntranslated,
      editorContentTranslated,
      setNewTextSegmentSelection,
      textSegmentsWithActiveSuggestion,
      selectedTextSegmentId,
      selectPreviousTextSegmentWithActiveSuggestion,
      selectNextTextSegmentWithActiveSuggestion,
      idOfFirstTextSegmentWithActiveSuggestion,
      idOfLastTextSegmentWithActiveSuggestion,
      handleUserEdit,
      copyTranslatedText,
      registerNewTranslatedTextEditor,
      handleTranslatedTextCopy,
      enableSpellcheck: options.enableSpellcheck,
    };
  },
});
</script>

<style lang="scss" scoped>
.min-w-suggestions {
  min-width: 20rem;
}
</style>
