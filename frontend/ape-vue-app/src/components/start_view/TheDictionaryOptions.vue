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
  <!-- Mount this component at the body of the DOM (for better accessability) -->
  <teleport to="body">

    <!-- Semi-transparent background -->
    <transition name="fade">
      <div
        v-if="visible"
        class="fixed inset-0 bg-black opacity-60"
        style="z-index: 10000"
        @click="dismiss"
      ></div>
    </transition>

    <!-- Floating card for the content -->
    <transition name="fade-move-up">
      <div
        v-if="visible"
        class="
          z-30
          fixed
          inset-0
          flex
          justify-center
          items-center
          pointer-events-none
        "
        style="z-index: 10001"
      >
        <base-card
          class="
            h-full
            w-full
            mx-8
            my-10
            min-w-md
            max-w-3xl
            relative
            flex-col
            pointer-events-auto
          "
          style="max-height: 90%"
        >

          <!-- Top right button to close the options -->
          <button
            class="absolute top-5 right-5 w-6 h-6 text-gray-400"
            @click="dismiss"
          >
            <x-icon />
          </button>

          <!-- Main content -->
          <div class="max-h-full overflow-auto block p-8">
            <h1 class="font-heading text-2xl">
              Dictionary Options:
              <span class="text-gray-400 ml-0.5">{{
                languagePairKey.toUpperCase()
              }}</span>
            </h1>
            <p>
              It is possible to refine the suggestions with the help of
              dictionaries. If there is a dictionary entry for a specific word,
              suggestions will include the translation found in this entry with
              a higher probability.
            </p>

            <!-- Section for user-defined dictionaries -->
            <div v-if="showUserDict">
              <h2 class="mt-6 font-heading">Custom Dictionary</h2>
              <p>
                Each entry should be put into a separate line. The word in the
                source language should be on the left and the translation should
                be on the right.
              </p>
              <p class="mt-4">
                For example, this is what entries should look like for the
                language pair English to German:
              </p>

              <div
                class="
                  my-4
                  border-l-2 border-gray-300
                  pl-4
                  text-gray-700
                  font-mono
                  text-sm
                "
              >
                <p>hello=grüezi</p>
                <p>bicycle=Velo</p>
              </div>

              <textarea
                v-model="newUserDictRaw"
                class="w-full border-2 p-4 rounded-md"
                :class="{ 'ring-red-400 ring-4': !inputIsValid }"
                name=""
                id=""
                rows="10"
              ></textarea>
            </div>

            <!-- Section for predefined dictionaries -->
            <div v-if="availableDictionaries.length > 0">
              <h2 class="mt-6 font-heading">Other Dictionaries</h2>
              <p class="mb-4">
                Below, you can select which other dictionaries you want to use.
              </p>

              <div
                v-for="(title, index) in availableDictionaries"
                :key="index"
                class="
                  flex
                  justify-between
                  items-center
                  py-1.5
                  px-4
                  bg-gray-100
                  mb-2
                  rounded-md
                "
              >
                <h2 class="font-bold">{{ title }}</h2>
                <input
                  type="checkbox"
                  :checked="newSelectedDictionaries.includes(title)"
                  @change="updateDictionarySelection(index, ($event!.target! as any).checked!)"
                />
              </div>
            </div>
          </div>
        </base-card>
      </div>
    </transition>
  </teleport>
</template>

<script lang="ts">
import {
  defineComponent, ref, watchEffect, PropType,
} from 'vue';
import { XIcon } from '@heroicons/vue/outline';
import BaseCard from '../UI/BaseCard.vue';
import {
  LanguageCode,
  LanguagePairKey,
  NotificationMessageType,
} from '@/modules/types';
import options from '@/modules/options';
import { useNotifier, useStore } from '@/modules/injectUtil';
import { userDictShouldBeDisplayed, validateUserDict } from '@/modules/dictUtil';

export default defineComponent({
  components: {
    BaseCard,
    XIcon,
  },
  emits: {
    dismiss: () => true,
  },
  props: {
    languagePairKey: {
      type: String as PropType<LanguagePairKey<LanguageCode, LanguageCode>>,
      required: true,
    },
    visible: {
      type: Boolean,
      required: true,
    },
  },
  setup(props, { emit }) {
    const notifier = useNotifier();
    const { state, methods } = useStore();

    // Object containing all info about the dictionaries of the current language pair
    const dictionaries = state.dictionaries[props.languagePairKey];

    if (!dictionaries) {
      throw new Error(
        `The state does not contain information about dictionaries for the language pair ${props.languagePairKey}. The language pair key might be incorrect.`,
      );
    }

    /**
     * USER DEFINED DICTIONARY ---------------------------------------------------------------------
     */

    const newUserDictRaw = ref(dictionaries.userDictRaw);

    let lastEditTime = Date.now();
    // This will be updated immediately bu the next method.
    const inputIsValid = ref(true);
    watchEffect(() => {
      const thisEditTime = Date.now();
      lastEditTime = thisEditTime;

      let ok = true;

      try {
        validateUserDict(newUserDictRaw.value);
      } catch (error: any) {
        ok = false;

        // If they have stopped making edits and the input is still invalid,
        // tell them what is wrong.
        setTimeout(() => {
          if (thisEditTime !== lastEditTime) {
            // They edited it again in the meantime.
            return;
          }

          notifier.dismissCurrentNotification();
          notifier.notify(error.message, {
            messageType: NotificationMessageType.alert,
          });
        }, 2000);
      }

      // If the input is invalid, immediately provide visual feedback to the user.
      inputIsValid.value = ok;
      if (ok) {
        notifier.dismissCurrentNotification();
      }

      // This will only parse the valid lines. Thus, we can parse every time the input changes.
      methods.updateUserDictRaw(props.languagePairKey, newUserDictRaw.value);
    });

    /**
     * OTHER DICTIONARY SELECTION ------------------------------------------------------------------
     */

    const newSelectedDictionaries = ref(dictionaries.selectedDicts);
    // This function will be called if the user selects/deselects a dictionary.
    function updateDictionarySelection(index: number, selected: boolean) {
      const changeVal = dictionaries.availableDicts[index];

      if (!changeVal) {
        console.warn(
          'Selected dictionary cannot be found.', 'Index:', index, 'Selected:', selected, 'Value:', changeVal,
        );
        return;
      }

      if (selected) {
        if (options.allowMultipleDictSelection) {
          newSelectedDictionaries.value.push(changeVal);
        } else {
          newSelectedDictionaries.value = [changeVal];
        }
      } else {
        newSelectedDictionaries.value = newSelectedDictionaries.value.filter(
          (v) => v !== changeVal,
        );
      }

      methods.updateSelectedDicts(
        props.languagePairKey,
        newSelectedDictionaries.value,
      );
    }

    /**
     * MISC ----------------------------------------------------------------------------------------
     */

    function dismiss() {
      emit('dismiss');
    }

    return {
      dismiss,
      newUserDictRaw,
      updateDictionarySelection,
      availableDictionaries: dictionaries.availableDicts,
      newSelectedDictionaries,
      inputIsValid,
      showUserDict: userDictShouldBeDisplayed(props.languagePairKey),
    };
  },
});
</script>
