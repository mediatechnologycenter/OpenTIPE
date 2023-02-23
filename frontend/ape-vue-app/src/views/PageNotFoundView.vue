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
  <div class="flex justify-center items-center h-full">
    <base-card class="p-8 w-full max-w-md">
      <div class="flex flex-col">
        <h1 class="mx-auto text-xl font-heading mb-8">Page cannot be found.</h1>
        <base-button
          title="Go home"
          type="primary-green"
          @click="buttonClicked"
        ></base-button>
      </div>
    </base-card>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useRouter } from 'vue-router';
import BaseCard from '@/components/UI/BaseCard.vue';
import BaseButton from '@/components/UI/BaseButton.vue';

export default defineComponent({
  components: {
    BaseCard,
    BaseButton,
  },
  setup() {
    const router = useRouter();

    function buttonClicked() {
      router.push({
        path: '/',
      });
    }

    return {
      buttonClicked,
    };
  },
});
</script>
