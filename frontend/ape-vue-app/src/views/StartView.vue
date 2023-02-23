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
  <!-- Dialog for when the translation is in progress -->
  <base-dialog
    :visible="showTranslationDialog"
    title="Translation is in progress..."
    description="This might take a few moments."
  >
    <template v-slot:buttons>
      <base-button
        title="Abort Translation"
        type="tertiary"
        @click="abortTranslation"
      ></base-button>
    </template>
  </base-dialog>

  <the-dictionary-options
    v-if="dictOptionsAvailable"
    :key="languagePairKey"
    :visible="dictionaryOptionsAreVisible"
    :languagePairKey="languagePairKey"
    @dismiss="hideDictionaryOptions"
  />

  <!-- Container to center content -->
  <div class="flex justify-center h-full">
    <div class="w-full h-full flex flex-col items-center w-full max-w-5xl p-8">
      <!-- Heading -->
      <h1 class="mt-10 mb-10 2xl:mt-10 2xl:mb-10 max-w-xs 2xl:max-w-xs">
        <img src="/banner.svg" alt="MTC Human-Assisted Post-Editing" />
      </h1>

      <!-- Editor label -->
      <element-label
        text="Enter the text you want to translate"
      ></element-label>

      <!-- Editor card -->
      <base-card class="w-full h-full flex-grow" style="min-height: 20rem">
        <tiptap
          v-model="editorContent"
          class="h-full"
          :enableSpellcheck="enableSpellcheck"
          :characterLimit="characterLimit"
          :enableTextSegment="false"
          :enableSuggestion="false"
        />
      </base-card>

      <!-- Horizontal menu -->
      <div class="w-full flex justify-evenly items-end mt-8">
        <!-- Source language selector -->
        <div class="flex flex-1 flex-col items-center">
          <element-label text="Source language"></element-label>
          <src-lang-selector
            class="flex-grow-0"
            v-model="selectedSrcLangIndex"
            :menuOptions="srcLangs"
            :upperCase="true"
          ></src-lang-selector>
        </div>

        <!-- Target language selector -->
        <div class="flex flex-1 flex-col items-center">
          <element-label text="Target language"></element-label>
          <trg-lang-selector
            v-model="selectedTrgLangIndex"
            :menuOptions="trgLangs"
            :upperCase="true"
          ></trg-lang-selector>
        </div>

        <div class="flex-1 flex justify-center">
          <base-button
            title="Dictionary options"
            type="secondary"
            @click="showDictionaryOptions"
            :disabled="!dictOptionsAvailable"
          >
            <template v-slot:icon>
              <book-open-icon class="w-5 h-5"></book-open-icon>
            </template>
          </base-button>
        </div>
      </div>

      <!-- Divider -->
      <div
        class="
          flex-shrink-0
          border-t-2
          w-full
          my-8
          border-gray-300 border-dashed
        "
      ></div>

      <div class="flex items-center justify-center w-full">
        <!-- Start button -->
        <base-button
          class="max-w-xs w-full mx-10"
          title="Start translation"
          @click="startTranslation()"
        >
          <template v-slot:icon>
            <translate-icon class="w-5 h-5"></translate-icon>
          </template>
        </base-button>
      </div>

      <!-- Logout button -->
      <router-link to="/logout" class="py-8" :class="{'invisible' : !authenticationIsEnabled()}" >
        <p class="text-gray-400 text-md">Log out</p>
      </router-link>
    </div>
  </div>
</template>

<script lang="ts">
import {
  ref, watchEffect, defineComponent, computed,
} from 'vue';
import { useRouter } from 'vue-router';
import { TranslateIcon } from '@heroicons/vue/solid';
import { BookOpenIcon } from '@heroicons/vue/outline';

import { JSONContent } from '@tiptap/core';
import { log } from 'loglevel';
import { parseEditorContent } from '../modules/editorUtil';
import { requestTranslationData } from '../modules/serverUtil';

import BaseSelector from '../components/UI/BaseSelector.vue';
import BaseButton from '../components/UI/BaseButton.vue';
import BaseDialog from '../components/UI/BaseDialog.vue';
import BaseCard from '../components/UI/BaseCard.vue';
import ElementLabel from '../components/start_view/ElementLabel.vue';
import Tiptap from '../components/editor/Tiptap.vue';
import TheDictionaryOptions from '@/components/start_view/TheDictionaryOptions.vue';
import { NotificationMessageType } from '@/modules/types';
import {
  authenticationIsEnabled,
  getLanguagePairKey,
  onlyUniqueValues,
} from '@/modules/otherUtil';
import options from '@/modules/options';
import { useNotifier, useStore } from '@/modules/injectUtil';
import { userDictShouldBeDisplayed } from '@/modules/dictUtil';

export default defineComponent({
  name: 'Home',
  components: {
    SrcLangSelector: BaseSelector,
    trgLangSelector: BaseSelector,
    ElementLabel,
    BaseButton,
    BaseDialog,
    BaseCard,
    TranslateIcon,
    Tiptap,
    BookOpenIcon,
    TheDictionaryOptions,
  },
  setup() {
    const notifier = useNotifier();
    const { state, methods } = useStore();
    const router = useRouter();

    /**
     * LANGUAGE SELECTION --------------------------------------------------------------------------
     */

    const selectedSrcLangCode = ref(state.srcLang);
    const selectedTrgLangCode = ref(state.trgLang);

    if (
      // Selected language pair is not available
      options.availableLanguagePairs.filter(
        (x) => x.from === selectedSrcLangCode.value
          && x.to === selectedTrgLangCode.value,
      ).length === 0
    ) {
      const firstAvailableLanguagePair = options.availableLanguagePairs[0];
      if (firstAvailableLanguagePair === undefined) {
        throw new Error('No available language pair was specified in options.ts');
      }

      selectedSrcLangCode.value = firstAvailableLanguagePair.from;
      selectedTrgLangCode.value = firstAvailableLanguagePair.to;
    }

    const languagePairKey = computed(() => getLanguagePairKey(
      selectedSrcLangCode.value,
      selectedTrgLangCode.value,
    ));

    const srcLangs = ref(
      options.availableLanguagePairs
        .map((pair) => pair.from)
        .filter((onlyUniqueValues)),
    );
    const trgLangs = ref(
      options.availableLanguagePairs
        .map((pair) => pair.to)
        .filter(onlyUniqueValues),
    );

    // Index of the selected source language in the srcLangs array
    const selectedSrcLangIndex = ref(
      srcLangs.value.findIndex((el) => el === selectedSrcLangCode.value),
    );

    // Index of the selected target language in the trgLangs array
    const selectedTrgLangIndex = ref(
      trgLangs.value.findIndex((el) => el === selectedTrgLangCode.value),
    );

    // Update the list of selectable targetLanguages if the selected source language is updated.
    watchEffect(() => {
      log('Updating available target languages');
      trgLangs.value = options.availableLanguagePairs
        .filter((pair) => pair.from === selectedSrcLangCode.value)
        .map((pair) => pair.to)
        .filter(onlyUniqueValues);
    });

    // Listen to changes in the source language selection
    watchEffect(() => {
      try {
        selectedSrcLangCode.value = srcLangs.value[selectedSrcLangIndex.value];
        methods.updateState({
          srcLang: selectedSrcLangCode.value,
        });
      } catch (error: any) {
        notifier.notify(error.message, {
          messageType: NotificationMessageType.error,
        });
      }
    });

    // Listen to changes in the target language selection
    watchEffect(() => {
      try {
        selectedTrgLangCode.value = trgLangs.value[selectedTrgLangIndex.value];
        methods.updateState({
          trgLang: selectedTrgLangCode.value,
        });
      } catch (error: any) {
        notifier.notify(error.message, {
          messageType: NotificationMessageType.error,
        });
      }
    });

    /**
     * EDITOR --------------------------------------------------------------------------------------
     */

    const editorContent = ref<JSONContent>({ type: 'doc' });
    Object.assign(editorContent.value, state.originalEditorContent);

    // Listen to updates in the editor
    watchEffect(() => {
      methods.updateState({
        originalEditorContent: editorContent.value,
      });
    });

    /**
     * TRANSLATION ---------------------------------------------------------------------------------
     */

    const showTranslationDialog = ref(false);
    let latestTranslationId = state.translationSessionId;

    async function startTranslation() {
      try {
        const thisTranslationId = state.translationSessionId;
        latestTranslationId = thisTranslationId;

        showTranslationDialog.value = true;

        const { textSegments, structure } = await parseEditorContent(
          editorContent.value,
        );

        methods.updateState({
          originalStructure: structure,
          originalTextSegments: textSegments,
        });

        if (!selectedSrcLangCode.value || !selectedTrgLangCode.value) {
          throw new Error('Source or target language is undefined.');
        }

        const response = await requestTranslationData(
          textSegments,
          selectedSrcLangCode.value,
          selectedTrgLangCode.value,
          state.translationSessionId,
          state.user,
          state.dictionaries[languagePairKey.value].userDictJSON,
          state.dictionaries[languagePairKey.value].selectedDicts,
        );

        if (
          // User has dismissed the dialog and therefore aborted the translation.
          !showTranslationDialog.value
          // The response corresponds to a previous translation request.
          || latestTranslationId !== thisTranslationId
        ) {
          return;
        }

        methods.updateState({
          textSegmentsFromApi: response,
        });

        showTranslationDialog.value = false;
        router.push({
          name: 'SuggestionsView',
        });
      } catch (error: any) {
        showTranslationDialog.value = false;
        notifier.notify(`Translation failed: ${error.message}`, {
          messageType: NotificationMessageType.error,
        });
      }
    }

    function abortTranslation() {
      showTranslationDialog.value = false;
    }

    /**
     * DICTIONARIES --------------------------------------------------------------------------------
     */

    const dictionaryOptionsAreVisible = ref(false);

    function showDictionaryOptions() {
      dictionaryOptionsAreVisible.value = true;
    }

    function hideDictionaryOptions() {
      dictionaryOptionsAreVisible.value = false;
    }

    const dictOptionsAvailable = computed(() => userDictShouldBeDisplayed(languagePairKey.value)
      || state.dictionaries[languagePairKey.value].availableDicts.length > 0);

    /**
     * MISC ----------------------------------------------------------------------------------------
     */

    const characterLimit = options.enableCharacterLimit
      ? options.characterLimit
      : undefined;

    return {
      languagePairKey,
      srcLangs,
      trgLangs,
      selectedSrcLangIndex,
      selectedTrgLangIndex,
      startTranslation,
      editorContent,
      abortTranslation,
      showTranslationDialog,
      authenticationIsEnabled,
      dictionaryOptionsAreVisible,
      showDictionaryOptions,
      hideDictionaryOptions,
      characterLimit,
      dictOptionsAvailable,
      enableSpellcheck: options.enableSpellcheck,
    };
  },
});
</script>

<style lang="scss"></style>
