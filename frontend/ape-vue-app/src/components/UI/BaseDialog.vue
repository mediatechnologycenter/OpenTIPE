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
  <teleport to="body">
    <transition name="fade">
      <div
        v-if="visible"
        class="fixed inset-0 bg-black opacity-60"
        style="z-index: 300000"
      ></div>
    </transition>
    <transition name="fade-move-up">
      <div
        v-if="visible"
        class="fixed inset-0 left-0 top-0 z-30 flex justify-center items-center"
        @click="emitBackgroundClick"
        style="z-index: 300001"
      >
        <base-card
          class="
            max-h-96
            min-w-md
            max-w-xl
            m-8
            p-8
            flex flex-col
            justify-center
            items-center
          "
        >
          <h2 class="font-bold text-2xl text-gray-700 mb-4">{{ title }}</h2>
          <p v-if="description" class="text-gray-500 mb-12">
            {{ description }}
          </p>
          <base-loading-animation class="mb-20"></base-loading-animation>
          <slot name="buttons" class=""></slot>
        </base-card>
      </div>
    </transition>
  </teleport>
</template>

<script>
import { defineComponent } from 'vue';
import BaseCard from './BaseCard.vue';
import BaseLoadingAnimation from './BaseLoadingAnimation.vue';

export default defineComponent({
  components: {
    BaseCard,
    BaseLoadingAnimation,
  },
  emits: {
    backgroundClick: () => true,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: false,
    },
    visible: {
      type: Boolean,
      required: false,
      default: () => true,
    },
  },
  setup(_, { emit }) {
    function emitBackgroundClick() {
      emit('backgroundClick');
    }

    return {
      emitBackgroundClick,
    };
  },
});
</script>

<style lang="scss" scoped>
.min-w-md {
  min-width: 28rem;
}
</style>
