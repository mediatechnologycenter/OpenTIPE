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
  <div class="relative">
    <button
      :title="description"
      class="
        h-full
        w-full
        px-4
        py-2
        rounded-md
        shadow-md
        hover:shadow-lg
        transition-all
        ease-in-out
        flex
        space-x-2
        text-white
        focus:outline-none
        items-center
        justify-center
      "
      :class="{
        'bg-gray-400 hover:bg-gray-500 active:bg-gray-600':
          type == 'secondary' || type == 'tertiary',
        'opacity-50': type == 'tertiary' && !disabled,
        'bg-mtc_pink-500 hover:bg-mtc_pink-600 active:bg-mtc_pink-700':
          type == 'primary',
        'bg-mtc_powder_blue-700 hover:bg-mtc_powder_blue-800 active:bg-mtc_powder_blue-900':
          type == 'primary-green',
        'opacity-20': disabled,
      }"
      @click="emitClick()"
      :disabled="disabled"
    >
      <!-- Small hack to visually center the button content -->
      <div :class="{ '-ml-1': title }">
        <slot name="icon"></slot>
      </div>
      <p v-if="title">{{ title }}</p>
    </button>
    <!-- This overlay disables things like hovering if the button is disabled. -->
    <div
      v-if="disabled"
      class="absolute w-full h-full top-0 left-0 cursor-not-allowed"
    />
  </div>
</template>

<script>
import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    title: String,
    type: {
      default: () => 'primary',
      required: false,
      type: String,
    },
    disabled: Boolean,
    description: String,
  },

  emits: {
    click: () => true,
  },

  setup(_, { emit }) {
    function emitClick() {
      emit('click');
    }

    return {
      emitClick,
    };
  },
});
</script>

<style></style>
