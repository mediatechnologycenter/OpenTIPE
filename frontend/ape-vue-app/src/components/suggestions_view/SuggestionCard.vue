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
  <div :class="{ selected: isSelected }" class="relative suggestion-card">
    <div class="w-0 relative" style="height: 72px; margin-top: -72px"></div>
    <base-card
      @click="$emit('newFocus', textSegment._id)"
      class="
        min-h-24
        flex-shrink-0
        p-4
        duration-300
        ring-2 ring-transparent ring-inset
        h-full
        relative
        transform
      "
      :class="{
        'ring-blue-300 bg-blue-50': isSelected,
        'cursor-pointer': !isSelected,
        'hover:shadow-lg hover:-translate-y-0.5 hover:duration-75' : !isSelected,
      }"
    >
      <div
        v-if="isFirstSuggestion && showNudge"
        class="
          absolute
          inset-0
          opacity-10
          ring-8 ring-blue-400
          animate-pulse
          rounded-lg
        "
      ></div>

      <!-- Card content if the suggestion is not selected -->
      <p v-if="!isSelected" class="z-30">
        <span
          v-for="(s, i) in textSegment.mtTextStructure"
          :key="i"
          :class="{ 'border-b-2 border-blue-400': s.highlight }"
          >{{ s.value }}</span
        >
      </p>

      <!-- Card content if the suggestion is selected -->
      <div v-else>
        <h3 class="text-gray-400 text-sm mb-1">Machine Translation</h3>
        <p class="text-gray-800">
          <span
            v-for="(s, i) in textSegment.mtTextStructure"
            :key="i"
            :class="{
              'bg-pink-400 bg-opacity-20 border-b-2 border-mtc_pink-300':
                s.highlight,
            }"
            >{{ s.value }}</span
          >
        </p>
        <div class="w-full flex justify-center mt-7 mb-1">
          <arrow-down-icon class="h-5 w-5 text-gray-400"></arrow-down-icon>
        </div>
        <h3 class="text-gray-400 text-sm mb-1">Suggestion</h3>
        <p class="mb-6">
          <span
            v-for="(s, i) in textSegment.apeTextStructure"
            :key="i"
            :class="{
              'bg-mtc_medium_aquamarine-400 bg-opacity-30 border-b-2 border-mtc_medium_aquamarine-700':
                s.highlight,
            }"
            >{{ s.value }}</span
          >
        </p>

        <!-- Buttons -->
        <div class="w-full flex space-x-2 justify-between">
          <!-- Left button group -->
          <div class="flex space-x-2">
            <base-button
              title="Apply"
              type="primary-green"
              @click="$emit('apply')"
            >
              <template v-slot:icon>
                <check-icon class="w-5 h-5"></check-icon>
              </template>
            </base-button>

            <base-button
              title="Discard"
              type="secondary"
              @click="$emit('discard')"
            >
              <template v-slot:icon>
                <x-icon class="w-5 h-5"></x-icon>
              </template>
            </base-button>
          </div>

          <!-- Right button group -->
          <div v-if="true" class="flex space-x-2">
            <base-button
              :disabled="isFirstSuggestion"
              type="tertiary"
              @click="$emit('previous')"
            >
              <template v-slot:icon>
                <arrow-up-icon class="w-5 h-5 -mx-2"></arrow-up-icon>
              </template>
            </base-button>

            <base-button
              :disabled="isLastSuggestion"
              type="tertiary"
              @click="$emit('next')"
            >
              <template v-slot:icon>
                <arrow-down-icon class="w-5 h-5 -mx-2"></arrow-down-icon>
              </template>
            </base-button>
          </div>
        </div>
      </div>
    </base-card>
  </div>
</template>

<script lang="ts">
import {
  watchEffect, ref, PropType, defineComponent, computed,
} from 'vue';

import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  XIcon,
} from '@heroicons/vue/solid';
import BaseCard from '../UI/BaseCard.vue';
import BaseButton from '../UI/BaseButton.vue';
import { TextSegment } from '@/modules/types';
import { useStore } from '@/modules/injectUtil';

export default defineComponent({
  components: {
    BaseCard,
    ArrowUpIcon,
    ArrowDownIcon,
    BaseButton,
    CheckIcon,
    XIcon,
  },
  props: {
    textSegment: {
      type: Object as PropType<TextSegment>,
      required: true,
    },
    selectedTextSegmentId: {
      type: String,
      default: () => null,
      required: false,
    },
    isFirstSuggestion: {
      type: Boolean,
      required: true,
    },
    isLastSuggestion: {
      type: Boolean,
      required: true,
    },
  },
  emits: {
    apply: () => true,
    discard: () => true,
    previous: () => true,
    next: () => true,
    newFocus: (_textSegmentId: string) => true,
  },
  setup(props) {
    const store = useStore();
    const showNudge = ref(false);

    setTimeout(() => {
      watchEffect(() => {
        showNudge.value = store.state
          .usingTheApplicationForTheFirstTime as boolean;
      });
    }, 5000);

    const isSelected = computed(() => props.selectedTextSegmentId === props.textSegment._id);

    watchEffect(() => {
      if (isSelected.value) {
        // eslint-disable-next-line no-unused-expressions
        store?.methods.updateState({
          usingTheApplicationForTheFirstTime: false,
        });
      }
    });

    return {
      isSelected,
      showNudge,
    };
  },
});
</script>
