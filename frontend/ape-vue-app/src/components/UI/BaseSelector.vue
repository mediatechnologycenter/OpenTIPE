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
      bg-gray-300
      p-1
      rounded-full
      flex
      space-x-2
      transition-all
      ease-in-out
    "
    style="min-width: 8rem"
  >
    <button
      class="
        w-full
        rounded-full
        px-6
        border-gray-600 border-4 border-opacity-0
        focus:outline-none
        text-sm
        font-bold
        text-gray-500
      "
      :class="{
        'bg-white shadow-md text-gray-700': key === selectedIndex,
        'hover:border-opacity-20': key !== selectedIndex,
      }"
      v-for="(option, key) in menuOptions"
      :key="key"
      @click="updateSelectedIndex(key)"
    >
      <p class="">
        {{ upperCase ? String(option).toUpperCase() : option }}
      </p>
    </button>
  </div>
</template>

<script lang="ts">
import {
  defineComponent, PropType, ref, watchEffect,
} from 'vue';

export default defineComponent({
  props: {
    menuOptions: {
      type: Object as PropType<string[]>,
      required: true,
    },
    upperCase: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    modelValue: {
      type: Number,
      required: true,
    },
  },
  emits: {
    'update:modelValue': (_index: number) => true,
  },
  setup(props, context) {
    const selectedIndex = ref(props.modelValue);

    watchEffect(() => {
      selectedIndex.value = Math.min(
        selectedIndex.value,
        props.menuOptions.length - 1,
      );
      context.emit('update:modelValue', selectedIndex.value);
    });

    function updateSelectedIndex(index: number) {
      if (index === selectedIndex.value) {
        return;
      }

      selectedIndex.value = index;
      context.emit('update:modelValue', selectedIndex.value);
    }

    return {
      selectedIndex,
      updateSelectedIndex,
    };
  },
});

</script>

<style></style>
