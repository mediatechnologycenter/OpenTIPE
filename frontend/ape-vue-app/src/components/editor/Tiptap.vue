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
    class="h-full relative overflow-hidden transform"
    :class="{ 'pb-10 delay-150': showMenu }"
  >

    <!-- The contents of the editor are rendered inside this component -->
    <editor-content
      :editor="editor"
      :spellcheck="enableSpellcheck"
      class="h-full overflow-y-auto editor p-8"
      :class="{ unfocused: !showMenu }"
    />

    <!-- Menu -->
    <transition name="fade">
      <editor-menu
        v-if="showMenu"
        class="absolute w-full bottom-0 left-0 h-10"
        :editor="editor"
        @mouseenter="handleMenuFocus"
        @mouseleave="handleMenuBlur"
        :characterLimit="characterLimit"
      ></editor-menu>
    </transition>
  </div>
</template>

<script lang="ts">
import { Editor, EditorContent, JSONContent } from '@tiptap/vue-3';
import StarterKit, { StarterKitOptions } from '@tiptap/starter-kit';
import CharacterCount from '@tiptap/extension-character-count';
import {
  defineComponent,
  onBeforeUnmount,
  PropType,
  Ref,
  ref,
  watch,
  watchEffect,
} from 'vue';
import EditorMenu from './EditorMenu.vue';
import TextSegmentMark from '../../modules/tiptap_extensions/TextSegmentMark';
import SuggestionMark from '../../modules/tiptap_extensions/SuggestionMark';
import { getTextSegmentIdOfSelectedMarks } from '../../modules/editorUtil';
import Highlight from '../../modules/tiptap_extensions/Highlight';
import { defaultTextSegmentId } from '@/modules/suggestionUtil';

export default defineComponent({
  components: {
    EditorContent,
    EditorMenu,
  },

  props: {
    modelValue: {
      type: Object as PropType<JSONContent>,
      required: true,
    },
    editable: {
      type: Boolean,
      default: () => true,
    },
    enableHistory: {
      type: Boolean,
      required: false,
      default: () => true,
    },
    selectedTextSegmentId: {
      type: String,
      default: () => defaultTextSegmentId,
    },
    enableHighlight: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    characterLimit: {
      type: Number,
      required: false,
      default: () => null,
    },
    enableSpellcheck: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    enableTextSegment: {
      type: Boolean,
      required: false,
      default: () => true,
    },
    enableSuggestion: {
      type: Boolean,
      required: false,
      default: () => true,
    },
  },

  emits: {
    // These are runtime validation functions. In this case, we only use them to get type
    // for custom event emits.
    userEdit: () => true,
    markClick: (_textSegmentId: string) => true,
    newEditor: (_editor: Editor) => true,
    textSegmentSelectionChange: () => true,
    'update:modelValue': (_editorContent: JSONContent) => true,
  },

  setup(props, { emit }) {
    /**
     * Editor options ------------------------------------------------------------------------------
     */

    const starterKitOptions: Partial<StarterKitOptions> = {
      bold: false,
      code: false,
      italic: false,
      strike: false,
      codeBlock: false,
      gapcursor: false,
    };

    if (!props.enableHistory) {
      starterKitOptions.history = false;
    }

    const extensions: any[] = [
      StarterKit.configure(starterKitOptions),
    ];

    if (props.enableTextSegment) {
      extensions.push(
        TextSegmentMark.Mark,
      );
    }

    if (props.enableSuggestion) {
      extensions.push(
        SuggestionMark.Mark,
      );
    }

    if (props.enableHighlight) {
      extensions.push(
        Highlight.configure({
          // Deep copy string in chrome. Otherwise we get an infinite loop for some reason.
          // eslint-disable-next-line prefer-template
          getSelectedTextSegmentId: () => ` ${props.selectedTextSegmentId}`.slice(1),
        }),
      );
    }

    if (props.characterLimit !== null) {
      extensions.push(
        CharacterCount.configure({
          limit: props.characterLimit,
        }),
      );
    }

    /**
     * EDITOR CREATION & EVENTS --------------------------------------------------------------------
     */

    const editorIsFocused = ref(false);

    const editor = ref(
      new Editor({
        content: props.modelValue,
        editable: props.editable,
        extensions,

        // Triggered when the content of the editor changes
        onUpdate: ({ editor: e }) => {
          emit('update:modelValue', e.getJSON() as JSONContent);
          emit('userEdit');
        },

        onSelectionUpdate: ({ editor: e }) => {
          const textSegmentId = getTextSegmentIdOfSelectedMarks(e);
          if (textSegmentId) {
            emit('markClick', textSegmentId);
          }
        },

        // Triggered if the user focuses the editor
        onFocus: () => {
          editorIsFocused.value = true;
        },

        // Triggered if the user focuses an element that is not the editor
        onBlur: () => {
          editorIsFocused.value = false;
        },
      }),
    ) as Ref<Editor>;

    onBeforeUnmount(() => {
      editor.value.destroy();
    });

    // Emitting the editor object allows the parent component to perform actions on the editor.
    // E.g., selecting all text is easier this way.
    emit('newEditor', editor.value);

    // Listen to changes of the editor content.
    // If there is an external change (something from the system, not the user),
    // the actual editor content must be updated.
    //
    // This method is executed every time the editor content changes.
    // => Potential performance improvement possible.
    watch(
      () => props.modelValue,
      (newVal) => {
        const isSameContent = JSON.stringify(editor.value.getJSON()) === JSON.stringify(newVal);

        if (isSameContent) {
          return;
        }

        const { pos } = editor.value.state.selection.$anchor;
        editor.value
          .chain()
          .setContent(newVal, false)
          .setTextSelection(pos)
          .run();
      },
    );

    /**
     * Manually dispatches an editor transaction in order to trigger a re-application of any
     * editor content decoration.
     *
     * E.g., if the text segment selection is changed, some styles need to be applied to the newly
     * selected text segment in the editor. Calling this method will reevaluate the styles of all
     * elements in the editor content.
     */
    function applyDecoration(e: Editor) {
      if (!e) return;
      const { state, view } = e;

      const transaction = state.tr;
      view.dispatch(transaction);
    }

    watch(
      () => props.selectedTextSegmentId,
      () => {
        emit('textSegmentSelectionChange');
        applyDecoration(editor.value);
      },
    );

    /**
     * EDITOR MENU ---------------------------------------------------------------------------------
     */

    const menuIsFocused = ref(false);

    function handleMenuFocus() {
      menuIsFocused.value = true;
    }

    function handleMenuBlur() {
      menuIsFocused.value = false;
    }

    const showMenu = ref(false);

    watchEffect(() => {
      showMenu.value = props.editable && (menuIsFocused.value || editorIsFocused.value);
    });

    return {
      editor,
      handleMenuBlur,
      handleMenuFocus,
      showMenu,
    };
  },
});
</script>

<style lang="scss">
.ProseMirror {
  height: 100%;
  @apply outline-none;
}

.unfocused {
  .ProseMirror {
    > *:last-child {
      @apply pb-10;
    }
  }
}

.editor {
  .ProseMirror {
    outline: none;

    > * {
      @apply mb-3;
      @apply leading-loose;
    }

    h1,
    h2,
    h3 {
      @apply font-bold;
    }

    h1 {
      @apply text-2xl mb-5;
    }

    h2 {
      @apply text-xl mb-4;
    }

    h3 {
      @apply text-lg mb-3;
    }

    ul {
      @apply list-disc pl-5;
    }

    ol {
      @apply list-decimal pl-5;
    }

    blockquote {
      @apply border-l-4 pl-3 border-black;
    }

    suggestion {
      @apply border-b-2 border-blue-400 cursor-pointer;

      > .selected {
        @apply bg-gradient-to-t from-blue-200 to-blue-100 cursor-auto border-blue-400 border-b-2 rounded-sm;
        @apply -mt-1 pt-1;
      }
    }

    text-segment[hassuggestion='true'] {
      @apply border-b-2 border-blue-200 cursor-pointer;

      > .selected {
        @apply border-blue-200;
      }
    }

    text-segment {

      > .selected {
        @apply bg-gray-200 border-b-2 border-gray-300;
        @apply -mt-1 pt-1;
      }
    }
  }
}
</style>
