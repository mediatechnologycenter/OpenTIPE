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
  <button
    class="
      h-7
      w-7
      rounded-md
      flex
      justify-center
      items-center
      hover:bg-gray-200
      transition-all
    "
    :class="{ 'bg-gray-200 hover:bg-gray-300': active }"
  >
    <slot class="flex justify-center items-center"></slot>
  </button>
</template>

<script>
export default {
  props: ['active'],
};
</script>
